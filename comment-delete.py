import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

class WordPressAPI:
    def __init__(self, base_url, auth):
        self.base_url = base_url.rstrip('/')
        self.auth = auth
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        # Configure connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=100,
            pool_maxsize=100
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.auth = self.auth
        return session

    def fetch_comments(self, page=1, per_page=100):
        endpoint = f"{self.base_url}/wp-json/wp/v2/comments"
        params = {
            "page": page,
            "per_page": per_page,
            "status": "hold",
            "context": "edit",
        }

        try:
            response = self.session.get(endpoint, params=params, timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching comments: {e}")
            return []

    def delete_comment(self, comment_id, force=False):
        endpoint = f"{self.base_url}/wp-json/wp/v2/comments/{comment_id}"
        params = {"force": "true" if force else "false"}

        try:
            response = self.session.delete(endpoint, params=params, timeout=60)
            return comment_id, response
        except requests.RequestException as e:
            print(f"Error deleting comment {comment_id}: {e}")
            return comment_id, None

def calculate_optimal_thread_count(total_items):
    """Calculate optimal thread count based on system resources and workload"""
    cpu_count = os.cpu_count() or 4
    # Use more threads for I/O bound operations, but cap it reasonably
    return min(max(cpu_count * 4, 10), min(total_items, 50))

def process_batch(api, comments, progress_bar=None):
    """Process a batch of comments"""
    results = {'success': 0, 'failed': 0}

    for comment in comments:
        comment_id = comment.get("id")
        author_name = comment.get("author_name", "Unknown")

        _, response = api.delete_comment(comment_id, force=False)

        if response and response.status_code in (200, 410):
            results['success'] += 1
        else:
            results['failed'] += 1

        if progress_bar:
            progress_bar.update(1)

    return results

def main():
    load_dotenv()
    wp_site_url = os.getenv("WP_SITE_URL")
    wp_admin_user = os.getenv("WP_ADMIN_USER")
    wp_admin_pass = os.getenv("WP_ADMIN_PASS")

    if not wp_site_url or not wp_admin_user or not wp_admin_pass:
        print("Missing environment variables. Please ensure WP_SITE_URL, WP_ADMIN_USER, and WP_ADMIN_PASS are set in your .env file.")
        return

    auth = HTTPBasicAuth(wp_admin_user, wp_admin_pass)
    api = WordPressAPI(wp_site_url, auth)

    page = 1
    batch_size = 100
    total_success = 0
    total_failed = 0

    print("Starting comment deletion process...")

    while True:
        comments = api.fetch_comments(page=page, per_page=batch_size)

        if not comments:
            if page == 1:
                print("No pending comments found.")
                break
            page = 1
            time.sleep(2)  # Add small delay before retrying
            continue

        total_comments = len(comments)
        thread_count = calculate_optimal_thread_count(total_comments)
        chunks = [comments[i:i + thread_count] for i in range(0, len(comments), thread_count)]

        with tqdm(total=total_comments, desc=f"Processing page {page}") as progress_bar:
            with ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = [
                    executor.submit(process_batch, api, chunk, progress_bar)
                    for chunk in chunks
                ]

                for future in as_completed(futures):
                    try:
                        results = future.result()
                        total_success += results['success']
                        total_failed += results['failed']
                    except Exception as e:
                        print(f"Batch processing error: {e}")
                        total_failed += len(chunk)

        page += 1

    print("\nDeletion Process Complete")
    print(f"Total comments successfully processed: {total_success}")
    print(f"Total failed deletions: {total_failed}")

    if total_failed > 0:
        print("\nSome deletions failed. You may want to run the script again to retry failed items.")

if __name__ == "__main__":
    main()
