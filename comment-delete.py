import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_comments_for_page(base_url, auth, page=1, per_page=100, verbose=False):
    endpoint = f"{base_url.rstrip('/')}/wp-json/wp/v2/comments"
    params = {
        "page": page,
        "per_page": per_page,
        "status": "hold",   # 'hold' = pending comments
        "context": "edit",  # 'edit' context required to see unpublished comments
    }

    if verbose:
        print(f"Fetching page {page} ...")

    response = requests.get(endpoint, params=params, auth=auth)

    if response.status_code != 200:
        print(f"Error fetching comments (HTTP {response.status_code}): {response.text}")
        return []

    data = response.json()
    if not data and verbose:
        print("No comments found on this page.")

    return data

def delete_comment(base_url, comment_id, auth, force=False):
    endpoint = f"{base_url.rstrip('/')}/wp-json/wp/v2/comments/{comment_id}"
    params = {"force": "true" if force else "false"}
    response = requests.delete(endpoint, params=params, auth=auth)
    return comment_id, response

def process_deletion(comment, base_url, auth, force):
    comment_id = comment.get("id")
    author_name = comment.get("author_name", "Unknown")
    print(f"  Deleting comment ID {comment_id} by '{author_name}' ...")

    comment_id, response = delete_comment(base_url, comment_id, auth, force)
    if response.status_code == 200:
        print(f"    -> Successfully deleted (moved to Trash) comment ID: {comment_id}")
        return True
    elif response.status_code == 410:
        print(f"    -> Comment ID {comment_id} was already deleted.")
        return True
    else:
        print(f"    -> Failed to delete comment ID {comment_id}, status={response.status_code}")
        print(response.text)
        return False

def main():
    load_dotenv()
    wp_site_url = os.getenv("WP_SITE_URL")
    wp_admin_user = os.getenv("WP_ADMIN_USER")
    wp_admin_pass = os.getenv("WP_ADMIN_PASS")

    if not wp_site_url or not wp_admin_user or not wp_admin_pass:
        print("Missing environment variables. Check your .env file.")
        return

    auth = HTTPBasicAuth(wp_admin_user, wp_admin_pass)
    page = 1
    total_deleted = 0
    threads = 5  # You can adjust this for performance

    while True:
        comments = fetch_comments_for_page(wp_site_url, auth, page=page, per_page=100, verbose=True)
        if not comments and page == 1:
            print(f"No more pending comments to delete on page {page}.")
            break
        elif not comments:
            print(f"setting to page 1 and trying again!")
            page = 1
            continue

        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [
                executor.submit(process_deletion, c, wp_site_url, auth, False)
                for c in comments
            ]

            for future in as_completed(futures):
                if future.result():
                    total_deleted += 1

        page += 1

    print(f"\nTotal comments deleted: {total_deleted}")

if __name__ == "__main__":
    main()
