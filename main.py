"""
Instagram Profile Categorizer — Main Entry Point
Pure terminal tool. No browser. Works on Windows, Linux, Termux.

Usage:
    python main.py <username_or_url>
    python main.py <username>
    python main.py @nasa --followers-only
    python main.py https://www.instagram.com/natgeo/ --following-only
    python main.py username --interactive
"""

import sys
import logging
import argparse
from datetime import datetime

try:
    from colorama import init as colorama_init, Fore, Style
    colorama_init(autoreset=True)
    HAS_COLORS = True
except ImportError:
    HAS_COLORS = False
    # Fallback — define empty color codes
    class Fore:
        RED = GREEN = YELLOW = CYAN = MAGENTA = WHITE = BLUE = RESET = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""

import config
from session import create_loader, login
from scraper import scrape_profile
from categorizer import categorize_full_scrape
from exporter import export_to_json, export_to_excel, generate_summary_report

# ──────────────────────────────────────────────
# Logging Setup
# ──────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format=config.LOG_FORMAT,
    datefmt=config.LOG_DATE_FORMAT,
    handlers=[
        logging.StreamHandler(
            open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)
        ),
        logging.FileHandler(
            f"{config.DATA_DIR}/run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding="utf-8",
            errors="replace",
        ),
    ],
)
logger = logging.getLogger(__name__)


def _parse_username(input_str):
    """
    Extract username from various input formats.
    Accepts: full URL, @username, or just username
    """
    input_str = input_str.strip().rstrip("/")

    # Remove @ prefix
    if input_str.startswith("@"):
        input_str = input_str[1:]

    # Handle full URLs
    if "instagram.com" in input_str:
        input_str = input_str.split("instagram.com/")[-1].split("/")[0].split("?")[0]

    return input_str


def _print_banner(username, scrape_followers, scrape_following):
    """Print a styled terminal banner."""
    c = Fore.CYAN if HAS_COLORS else ""
    g = Fore.GREEN if HAS_COLORS else ""
    y = Fore.YELLOW if HAS_COLORS else ""
    b = Style.BRIGHT if HAS_COLORS else ""
    r = Style.RESET_ALL if HAS_COLORS else ""

    mode_parts = []
    if scrape_followers:
        mode_parts.append("Followers")
    if scrape_following:
        mode_parts.append("Following")
    mode_str = " + ".join(mode_parts)

    print(f"\n{c}{'=' * 55}")
    print(f"{c}|{b}  INSTAGRAM PROFILE CATEGORIZER{r}")
    print(f"{c}|{r}  Pure Terminal Tool -- No Browser Needed")
    print(f"{c}{'=' * 55}")
    print(f"{c}|{r}  Target:  {g}@{username}{r}")
    print(f"{c}|{r}  Mode:    {y}{mode_str}{r}")
    print(f"{c}|{r}  Batch:   {config.BATCH_SIZE} accounts max per list")
    print(f"{c}|{r}  Time:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{c}{'=' * 55}{r}\n")


def _print_phase(phase_num, title):
    """Print a phase header."""
    c = Fore.MAGENTA if HAS_COLORS else ""
    b = Style.BRIGHT if HAS_COLORS else ""
    r = Style.RESET_ALL if HAS_COLORS else ""
    print(f"\n{c}{b}[Phase {phase_num}]{r} {title}")
    print(f"{c}{'-' * 45}{r}")


def main():
    """Main execution pipeline."""
    # ──────────────────────────────────────────────
    # Argument Parsing
    # ──────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="Instagram Profile Categorizer -- Scrape & categorize followers/following (pure terminal, no browser)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py <username>
  python main.py @nasa --followers-only
  python main.py https://www.instagram.com/natgeo/ --following-only
  python main.py username --interactive

Platforms: Windows | Linux | Termux (Android) | macOS
        """,
    )
    parser.add_argument(
        "profile",
        help="Instagram username or URL (e.g., '<username>' or '@nasa' or full URL)",
    )
    parser.add_argument(
        "--followers-only",
        action="store_true",
        help="Only scrape followers (skip following)",
    )
    parser.add_argument(
        "--following-only",
        action="store_true",
        help="Only scrape following (skip followers)",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode -- prompt for credentials if not set in config.py",
    )
    parser.add_argument(
        "--fresh-login",
        action="store_true",
        help="Force fresh login (ignore saved session)",
    )
    parser.add_argument(
        "--batch-size", "-b",
        type=int,
        default=None,
        help=f"Override batch size (default: {config.BATCH_SIZE})",
    )

    args = parser.parse_args()

    # Override batch size if specified
    if args.batch_size:
        config.BATCH_SIZE = args.batch_size

    # Determine what to scrape
    scrape_followers = not args.following_only
    scrape_following = not args.followers_only

    username = _parse_username(args.profile)

    # ──────────────────────────────────────────────
    # Banner
    # ──────────────────────────────────────────────
    _print_banner(username, scrape_followers, scrape_following)

    try:
        # ──────────────────────────────────────────────
        # Phase 1: Initialize Instaloader
        # ──────────────────────────────────────────────
        _print_phase(1, "Initializing...")
        loader = create_loader()

        # ──────────────────────────────────────────────
        # Phase 2: Login
        # ──────────────────────────────────────────────
        _print_phase(2, "Authenticating with Instagram...")
        login_success = login(
            loader,
            force_fresh=args.fresh_login,
            interactive=args.interactive,
        )

        if not login_success:
            g = Fore.RED if HAS_COLORS else ""
            r = Style.RESET_ALL if HAS_COLORS else ""
            print(f"\n{g}[X] Login failed -- cannot proceed{r}")
            print(f"   -> Check credentials in config.py")
            print(f"   -> Or run with: python main.py {username} --interactive")
            print(f"   -> Make sure 2FA is disabled on your test account")
            return 1

        g = Fore.GREEN if HAS_COLORS else ""
        r = Style.RESET_ALL if HAS_COLORS else ""
        print(f"{g}[OK] Login successful!{r}")

        # ──────────────────────────────────────────────
        # Phase 3: Scraping
        # ──────────────────────────────────────────────
        _print_phase(3, f"Scraping @{username}...")
        scrape_result = scrape_profile(
            loader,
            username,
            scrape_followers=scrape_followers,
            scrape_following=scrape_following,
        )

        total_scraped = len(scrape_result.get("followers", [])) + len(
            scrape_result.get("following", [])
        )

        if total_scraped == 0:
            y = Fore.YELLOW if HAS_COLORS else ""
            r = Style.RESET_ALL if HAS_COLORS else ""
            print(f"\n{y}[!] No accounts were scraped!{r}")
            print(f"   -> The profile might be private")
            print(f"   -> Instagram might have rate-limited the requests")
            print(f"   -> Check the data/ directory for any incremental saves")
            return 1

        g = Fore.GREEN if HAS_COLORS else ""
        r = Style.RESET_ALL if HAS_COLORS else ""
        print(f"\n{g}[OK] Scraping complete -- {total_scraped} accounts extracted{r}")

        # ──────────────────────────────────────────────
        # Phase 4: Categorization
        # ──────────────────────────────────────────────
        _print_phase(4, "Categorizing accounts...")
        categorized_data = categorize_full_scrape(scrape_result)
        print(f"{g}[OK] Categorization complete!{r}")

        # ──────────────────────────────────────────────
        # Phase 5: Export
        # ──────────────────────────────────────────────
        _print_phase(5, "Exporting results...")

        json_path = export_to_json(categorized_data, username)
        excel_path = export_to_excel(categorized_data, username)

        c = Fore.CYAN if HAS_COLORS else ""
        if json_path:
            print(f"  {c}[JSON]  {json_path}{r}")
        if excel_path:
            print(f"  {c}[XLSX]  {excel_path}{r}")

        # ──────────────────────────────────────────────
        # Final Report
        # ──────────────────────────────────────────────
        generate_summary_report(categorized_data)

        g = Fore.GREEN if HAS_COLORS else ""
        b = Style.BRIGHT if HAS_COLORS else ""
        print(f"\n{g}{b}All done! Check the output/ directory for your files.{r}\n")
        return 0

    except KeyboardInterrupt:
        y = Fore.YELLOW if HAS_COLORS else ""
        r = Style.RESET_ALL if HAS_COLORS else ""
        print(f"\n{y}[!] Interrupted by user -- shutting down...{r}")
        return 130

    except Exception as e:
        logger.error(f"[ERROR] Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
