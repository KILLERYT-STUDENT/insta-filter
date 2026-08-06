"""
Instagram Profile Categorizer — Session Management
Handles Instaloader initialization, login, and session persistence.
No browser needed — pure HTTP requests.
Works on: Windows, Linux, Termux (Android)
"""

import os
import sys
import time
import logging
import getpass

import instaloader

import config

logger = logging.getLogger(__name__)


def create_loader():
    """
    Create and configure an Instaloader instance with hardcoded settings.
    
    Returns:
        instaloader.Instaloader instance
    """
    logger.info("Initializing Instaloader...")

    loader = instaloader.Instaloader(
        download_pictures=config.DOWNLOAD_PICTURES,
        download_videos=config.DOWNLOAD_VIDEOS,
        download_comments=config.DOWNLOAD_COMMENTS,
        download_geotags=config.DOWNLOAD_GEOTAGS,
        save_metadata=config.SAVE_METADATA,
        compress_json=config.COMPRESS_JSON,
        quiet=config.QUIET_MODE,
        dirname_pattern=config.DATA_DIR,
        max_connection_attempts=config.MAX_RETRIES,
    )

    # Set custom user-agent to reduce detection
    loader.context._session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        )
    })

    logger.info("Instaloader initialized ✓")
    return loader


def _get_session_file(username):
    """Get the session file path for a given username."""
    return config.SESSION_FILE.format(username=username)


def load_session(loader, username):
    """
    Try to load a saved session from disk.
    
    Args:
        loader: Instaloader instance
        username: Instagram username
    
    Returns:
        True if session loaded and is valid, False otherwise
    """
    session_file = _get_session_file(username)

    if not os.path.exists(session_file):
        logger.info("No saved session found")
        return False

    try:
        loader.load_session_from_file(username, session_file)
        
        # Verify session is still valid by testing a simple request
        try:
            loader.test_login()
            logger.info(f"Session restored for @{username} ✓")
            return True
        except instaloader.exceptions.LoginException:
            logger.warning("Saved session is expired — need fresh login")
            # Delete the stale session file
            try:
                os.remove(session_file)
            except OSError:
                pass
            return False

    except Exception as e:
        logger.warning(f"Failed to load session: {e}")
        return False


def save_session(loader, username):
    """Save current session to disk for future reuse."""
    session_file = _get_session_file(username)

    try:
        loader.save_session_to_file(session_file)
        logger.info(f"Session saved → {session_file}")
    except Exception as e:
        logger.error(f"Failed to save session: {e}")


def login(loader, force_fresh=False, interactive=False):
    """
    Log into Instagram using hardcoded credentials or interactive prompt.
    
    Flow:
    1. Try loading saved session (skip login if valid)
    2. If no session → login with hardcoded credentials
    3. If credentials not set + interactive → prompt user
    4. Save session for next run
    
    Args:
        loader: Instaloader instance
        force_fresh: If True, skip session loading
        interactive: If True, prompt for credentials if not hardcoded
    
    Returns:
        True if login successful, False otherwise
    """
    username = config.INSTAGRAM_USERNAME
    password = config.INSTAGRAM_PASSWORD

    credentials_set = (
        username != "your_test_username" and 
        password != "your_test_password" and
        username and password
    )

    # ── If credentials not set, try interactive mode ──
    if not credentials_set:
        if interactive:
            print("\n" + "═" * 50)
            print("  Instagram Login Required")
            print("  (Tip: Set credentials in config.py to skip this)")
            print("═" * 50)

            try:
                username = input("  Username: ").strip()
                password = getpass.getpass("  Password: ").strip()
            except (EOFError, KeyboardInterrupt):
                logger.error("Login cancelled by user")
                return False

            if not username or not password:
                logger.error("Username and password cannot be empty")
                return False
        else:
            logger.error("═" * 55)
            logger.error("  CREDENTIALS NOT SET!")
            logger.error("  Edit config.py → set INSTAGRAM_USERNAME & INSTAGRAM_PASSWORD")
            logger.error("  Or run with --interactive flag to enter them manually")
            logger.error("  Use a TEST account — never your personal account!")
            logger.error("═" * 55)
            return False

    # ── Try session restore (skip if force_fresh) ──
    if not force_fresh:
        logger.info("Attempting session restore...")
        if load_session(loader, username):
            return True

    # ── Fresh login ──
    logger.info(f"Logging in as @{username}...")

    try:
        loader.login(username, password)
        logger.info(f"Login successful for @{username} ✓")

        # Save session for future runs
        save_session(loader, username)
        return True

    except instaloader.exceptions.BadCredentialsException:
        logger.error("❌ Bad credentials — wrong username or password")
        return False

    except instaloader.exceptions.TwoFactorAuthRequiredException:
        logger.warning("Two-Factor Authentication required!")

        if interactive or sys.stdin.isatty():
            try:
                print("\n  2FA code sent to your device.")
                code = input("  Enter 2FA code: ").strip()
                loader.two_factor_login(code)
                logger.info("2FA login successful ✓")
                save_session(loader, username)
                return True
            except Exception as e:
                logger.error(f"2FA login failed: {e}")
                return False
        else:
            logger.error("2FA required but running in non-interactive mode")
            logger.error("Disable 2FA on your test account or run with --interactive")
            return False

    except instaloader.exceptions.ConnectionException as e:
        if "Checkpoint" in str(e) or "challenge" in str(e).lower():
            logger.error("❌ Instagram checkpoint/challenge detected!")
            logger.error("   Open Instagram app on your phone and verify the login attempt")
            logger.error("   Then try again")
        elif "429" in str(e) or "rate" in str(e).lower():
            logger.error("❌ Rate limited by Instagram — wait a few minutes and try again")
        else:
            logger.error(f"❌ Connection error: {e}")
        return False

    except instaloader.exceptions.LoginException as e:
        logger.error(f"❌ Login failed: {e}")
        return False

    except Exception as e:
        logger.error(f"❌ Unexpected error during login: {e}")
        return False
