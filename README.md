# WordPress Comment Deletion Automaton

A high-performance Python script for bulk deletion of pending comments in WordPress sites using the WordPress REST API.

## Features

- **Parallel Processing**: Efficiently deletes comments using multi-threading
- **Adaptive Performance**: Automatically optimizes thread count based on system resources
- **Connection Pooling**: Reuses HTTP connections for better performance
- **Progress Tracking**: Real-time progress bars for batch operations
- **Error Handling**: Built-in retry mechanism with exponential backoff
- **Session Management**: Maintains persistent sessions for better efficiency

## Prerequisites

- Python 3.9 or higher
- WordPress site with REST API enabled
- Admin credentials with comment deletion permissions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wordpress-automaton.git
cd wordpress-automaton
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root with your WordPress credentials:
```env
WP_SITE_URL=https://your-wordpress-site.com
WP_ADMIN_USER=your-admin-username
WP_ADMIN_PASS=your-admin-password
```

## Usage

Run the script:
```bash
python comment-delete.py
```

The script will:
1. Connect to your WordPress site
2. Fetch pending comments in batches
3. Delete comments in parallel using optimized threading
4. Show progress with real-time progress bars
5. Provide a summary of successful and failed deletions

## Performance Features

- **Adaptive Threading**: Automatically calculates optimal thread count based on CPU cores and workload
- **Connection Pooling**: Reuses HTTP connections to reduce overhead
- **Batch Processing**: Processes comments in optimized chunks
- **Automatic Retries**: Handles transient network issues with exponential backoff
- **Progress Tracking**: Visual feedback on deletion progress

## Error Handling

The script includes robust error handling:
- Automatic retry for network-related issues
- Exponential backoff for rate limiting
- Detailed error reporting for failed deletions
- Session management for connection stability

## Requirements

```
requests~=2.32.3
python-dotenv~=1.1.0
tqdm~=4.66.1
```

## Security Notes

- Store your `.env` file securely and never commit it to version control
- Use a dedicated WordPress admin account with minimum required permissions
- Consider using application passwords if supported by your WordPress installation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
