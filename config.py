"""
Instagram Profile Categorizer — Configuration
All settings hardcoded. No .env files. Pure terminal tool.
Works on: Windows, Linux, Termux (Android)
"""

import os

# ──────────────────────────────────────────────
# Instagram Credentials (Use a TEST account only!)
# ──────────────────────────────────────────────
INSTAGRAM_USERNAME = "your_test_username"
INSTAGRAM_PASSWORD = "your_test_password"

# ──────────────────────────────────────────────
# Directory Paths (auto-created if missing)
# ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DATA_DIR = os.path.join(BASE_DIR, "data")
SESSION_DIR = os.path.join(BASE_DIR, "sessions")

# Create directories if they don't exist
for directory in [OUTPUT_DIR, DATA_DIR, SESSION_DIR]:
    os.makedirs(directory, exist_ok=True)

# ──────────────────────────────────────────────
# Session file path (cookie-like persistence)
# ──────────────────────────────────────────────
SESSION_FILE = os.path.join(SESSION_DIR, "session-{username}")

# ──────────────────────────────────────────────
# Scraping Limits & Rate Limiting
# ──────────────────────────────────────────────
BATCH_SIZE = 100                # Max accounts to scrape per list (followers/following)
INCREMENTAL_SAVE_INTERVAL = 20  # Save progress every N accounts scraped
REQUEST_DELAY_MIN = 1.0         # Min seconds between API requests
REQUEST_DELAY_MAX = 3.0         # Max seconds between API requests
MAX_RETRIES = 3                 # Max retries on request failure
RETRY_DELAY = 30                # Seconds to wait before retrying after rate limit

# ──────────────────────────────────────────────
# Instaloader Settings
# ──────────────────────────────────────────────
DOWNLOAD_PICTURES = False       # Don't download profile pictures
DOWNLOAD_VIDEOS = False         # Don't download videos
DOWNLOAD_COMMENTS = False       # Don't download comments
DOWNLOAD_GEOTAGS = False        # Don't download geotags
SAVE_METADATA = False           # Don't save post metadata
COMPRESS_JSON = False           # Don't compress JSON output
QUIET_MODE = False              # Show Instaloader progress

# ──────────────────────────────────────────────
# Follower Tier Thresholds
# ──────────────────────────────────────────────
TIER_NANO_MAX = 1_000           # 0 to 1K
TIER_MICRO_MAX = 10_000         # 1K to 10K
TIER_MID_MAX = 100_000          # 10K to 100K
TIER_MACRO_MAX = 1_000_000      # 100K to 1M
# Anything above 1M = Mega

# ──────────────────────────────────────────────
# Export Settings
# ──────────────────────────────────────────────
JSON_INDENT = 4                 # Pretty-print indentation for JSON exports
EXCEL_SHEET_NAMES = {
    "all": "All Accounts",
    "verified": "Verified",
    "unverified": "Unverified",
    "public": "Public",
    "private": "Private",
    "complete_profile": "Complete Profiles",
    "incomplete_profile": "Incomplete Profiles",
    "nano": "Nano (0-1K)",
    "micro": "Micro (1K-10K)",
    "mid": "Mid-Tier (10K-100K)",
    "macro": "Macro (100K-1M)",
    "mega": "Mega (1M+)",
}

# ──────────────────────────────────────────────
# Terminal UI Colors (via colorama)
# ──────────────────────────────────────────────
ENABLE_COLORS = True            # Set False for dumb terminals

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────
LOG_FORMAT = "[%(asctime)s] %(levelname)s — %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = "INFO"
