import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

def fetch_comments_for_page(base_url, auth, page=1, per_page=100, verbose=False):
    """
    Fetch a single page of WordPress comments via the WP REST API (v2).
    Returns a list of comments for the given page or an empty list if none.
    """
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
    """
    Delete a WordPress comment by ID.
    If force=True, the comment is permanently deleted (skips Trash).
    """
    endpoint = f"{base_url.rstrip('/')}/wp-json/wp/v2/comments/{comment_id}"
    params = {}
    if force:
        params["force"] = "true"

    response = requests.delete(endpoint, params=params, auth=auth)
    return response

def main():
    # Load environment variables from .env
    load_dotenv()

    # Retrieve values from environment variables
    wp_site_url = os.getenv("WP_SITE_URL")
    wp_admin_user = os.getenv("WP_ADMIN_USER")
    wp_admin_pass = os.getenv("WP_ADMIN_PASS")

    if not wp_site_url or not wp_admin_user or not wp_admin_pass:
        print("Missing environment variables. Check your .env file.")
        return

    auth = HTTPBasicAuth(wp_admin_user, wp_admin_pass)

    page = 1
    total_deleted = 0

    while True:
        comments = fetch_comments_for_page(wp_site_url, auth, page=page, per_page=10, verbose=True)
        if not comments:
            print(f"No more pending comments to delete on page {page}.")
            break

        for c in comments:
            comment_id = c.get("id")
            author_name = c.get("author_name", "Unknown")
            print(f"  Deleting comment ID {comment_id} by '{author_name}' ...")

            # Set force=True if you want to skip the Trash and permanently delete
            delete_response = delete_comment(wp_site_url, comment_id, auth, force=False)

            if delete_response.status_code == 200:
                print(f"    -> Successfully deleted (moved to Trash) comment ID: {comment_id}")
                total_deleted += 1
            elif delete_response.status_code == 410:
                print(f"    -> Comment ID {comment_id} was already deleted.")
            else:
                print(f"    -> Failed to delete comment ID {comment_id}, status={delete_response.status_code}")
                print(delete_response.text)

        page += 1

    print(f"\nTotal comments deleted: {total_deleted}")

if __name__ == "__main__":
    main()
