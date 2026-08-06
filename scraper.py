"""
Instagram Profile Categorizer — Scraper Module
Uses Instaloader API to extract profile data, followers, and following.
No browser — pure HTTP requests.
Works on: Windows, Linux, Termux (Android)
"""

import json
import os
import time
import random
import logging
from datetime import datetime

import instaloader

import config

logger = logging.getLogger(__name__)


def _random_delay():
    """Sleep for a random duration to avoid rate limiting."""
    delay = random.uniform(config.REQUEST_DELAY_MIN, config.REQUEST_DELAY_MAX)
    time.sleep(delay)


def _save_incremental(accounts, username, list_type):
    """Save scraped data incrementally to prevent loss on crash/disconnect."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{username}_{list_type}_raw_{timestamp}.json"
    filepath = os.path.join(config.DATA_DIR, filename)

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(accounts, f, indent=config.JSON_INDENT, ensure_ascii=False)
        logger.info(f"  💾 Incremental save: {len(accounts)} accounts → {filename}")
    except Exception as e:
        logger.error(f"  Failed to save incremental data: {e}")


def get_profile(loader, username):
    """
    Fetch profile metadata for an Instagram username.
    
    Args:
        loader: Instaloader instance (logged in)
        username: Instagram username (without @)
    
    Returns:
        dict with profile stats, or None if profile not found
    """
    # Clean username input
    username = username.strip().lstrip("@")

    # Handle full URLs
    if "instagram.com" in username:
        username = username.rstrip("/").split("/")[-1]

    logger.info(f"Fetching profile: @{username}")

    try:
        profile = instaloader.Profile.from_username(loader.context, username)

        stats = {
            "username": profile.username,
            "full_name": profile.full_name or "",
            "bio": profile.biography or "",
            "bio_links": [link.url for link in profile.biography_links] if hasattr(profile, 'biography_links') else [],
            "external_url": profile.external_url or "",
            "posts": profile.mediacount,
            "followers": profile.followers,
            "following": profile.followees,
            "is_verified": profile.is_verified,
            "is_private": profile.is_private,
            "is_business": profile.is_business_account,
            "business_category": profile.business_category_name or "",
            "profile_pic_url": profile.profile_pic_url or "",
            "has_profile_pic": bool(profile.profile_pic_url),
            "user_id": profile.userid,
        }

        logger.info(
            f"  @{stats['username']} | "
            f"Posts: {stats['posts']} | "
            f"Followers: {stats['followers']} | "
            f"Following: {stats['following']} | "
            f"{'✓ Verified' if stats['is_verified'] else '✗ Not Verified'} | "
            f"{'🔒 Private' if stats['is_private'] else '🌐 Public'}"
        )

        return stats, profile

    except instaloader.exceptions.ProfileNotExistsException:
        logger.error(f"❌ Profile @{username} does not exist!")
        return None, None

    except instaloader.exceptions.ConnectionException as e:
        if "429" in str(e):
            logger.error(f"❌ Rate limited while fetching profile — wait and retry")
        else:
            logger.error(f"❌ Connection error fetching profile: {e}")
        return None, None

    except Exception as e:
        logger.error(f"❌ Error fetching profile @{username}: {e}")
        return None, None


def _extract_account_data(profile_obj):
    """
    Extract relevant data from an Instaloader Profile object.
    
    Args:
        profile_obj: instaloader.Profile object
    
    Returns:
        dict with account data
    """
    try:
        return {
            "username": profile_obj.username,
            "display_name": profile_obj.full_name or "",
            "profile_url": f"https://www.instagram.com/{profile_obj.username}/",
            "user_id": profile_obj.userid,
            "is_verified": profile_obj.is_verified,
            "is_private": profile_obj.is_private,
            "followers": profile_obj.followers,
            "following": profile_obj.followees,
            "posts": profile_obj.mediacount,
            "bio": profile_obj.biography or "",
            "has_profile_pic": bool(profile_obj.profile_pic_url),
            "is_business": profile_obj.is_business_account,
            "business_category": profile_obj.business_category_name or "",
            "external_url": profile_obj.external_url or "",
            "scraped_at": datetime.now().isoformat(),
        }
    except Exception as e:
        # Minimal fallback if some attributes fail
        try:
            return {
                "username": profile_obj.username,
                "display_name": getattr(profile_obj, 'full_name', '') or "",
                "profile_url": f"https://www.instagram.com/{profile_obj.username}/",
                "user_id": getattr(profile_obj, 'userid', 0),
                "is_verified": getattr(profile_obj, 'is_verified', False),
                "is_private": getattr(profile_obj, 'is_private', False),
                "followers": 0,
                "following": 0,
                "posts": 0,
                "bio": "",
                "has_profile_pic": False,
                "is_business": False,
                "business_category": "",
                "external_url": "",
                "scraped_at": datetime.now().isoformat(),
                "_extraction_error": str(e),
            }
        except Exception:
            return None


def scrape_list(loader, profile, list_type="followers"):
    """
    Scrape followers or following list from a profile.
    
    Args:
        loader: Instaloader instance (logged in)
        profile: instaloader.Profile object
        list_type: 'followers' or 'following'
    
    Returns:
        list of account dicts
    """
    username = profile.username
    max_accounts = config.BATCH_SIZE

    if list_type == "followers":
        total_count = profile.followers
        iterator_func = profile.get_followers
    else:
        total_count = profile.followees
        iterator_func = profile.get_followees

    actual_target = min(total_count, max_accounts)
    logger.info(f"\n{'═' * 55}")
    logger.info(f"  Scraping {list_type.upper()} of @{username}")
    logger.info(f"  Total {list_type}: {total_count} | Scraping up to: {actual_target}")
    logger.info(f"{'═' * 55}")

    if profile.is_private:
        # Check if we follow this private account
        try:
            followers_iter = iterator_func()
            # Try to get the first item to verify access
        except instaloader.exceptions.PrivateProfileNotFollowedException:
            logger.error(f"  ❌ @{username} is PRIVATE and you don't follow them")
            logger.error(f"     Cannot access {list_type} list")
            return []

    accounts = []
    error_count = 0
    last_save_count = 0

    try:
        iterator = iterator_func()

        for i, follower_profile in enumerate(iterator, 1):
            if len(accounts) >= max_accounts:
                logger.info(f"  Reached batch limit of {max_accounts} — stopping")
                break

            try:
                account_data = _extract_account_data(follower_profile)
                if account_data:
                    accounts.append(account_data)

                    # Progress log every 10 accounts
                    if len(accounts) % 10 == 0:
                        logger.info(
                            f"  📊 Progress: {len(accounts)}/{actual_target} "
                            f"({len(accounts)/actual_target*100:.1f}%)"
                        )

                # Incremental save
                if len(accounts) - last_save_count >= config.INCREMENTAL_SAVE_INTERVAL:
                    _save_incremental(accounts, username, list_type)
                    last_save_count = len(accounts)

                # Random delay to avoid rate limiting
                _random_delay()

            except instaloader.exceptions.ConnectionException as e:
                error_count += 1
                if "429" in str(e) or "rate" in str(e).lower():
                    logger.warning(
                        f"  ⚠️  Rate limited at account #{i} — "
                        f"waiting {config.RETRY_DELAY}s..."
                    )
                    # Save what we have before waiting
                    _save_incremental(accounts, username, list_type)
                    last_save_count = len(accounts)
                    time.sleep(config.RETRY_DELAY)
                else:
                    logger.warning(f"  ⚠️  Connection error on account #{i}: {e}")
                    if error_count >= config.MAX_RETRIES:
                        logger.error(
                            f"  ❌ Too many errors ({error_count}) — stopping scrape"
                        )
                        break
                    time.sleep(5)

            except instaloader.exceptions.QueryReturnedBadRequestException:
                logger.warning(f"  ⚠️  Bad request at account #{i} — skipping")
                error_count += 1
                if error_count >= config.MAX_RETRIES * 2:
                    break
                time.sleep(3)

            except Exception as e:
                error_count += 1
                logger.warning(f"  ⚠️  Error extracting account #{i}: {e}")
                if error_count >= config.MAX_RETRIES * 3:
                    logger.error("  ❌ Too many extraction errors — stopping")
                    break

    except instaloader.exceptions.LoginRequiredException:
        logger.error("  ❌ Login required! Session may have expired.")
        logger.error("     Run again with --fresh-login flag")

    except instaloader.exceptions.PrivateProfileNotFollowedException:
        logger.error(f"  ❌ @{username} is PRIVATE — cannot access {list_type}")

    except instaloader.exceptions.QueryReturnedNotFoundException:
        logger.error(f"  ❌ Instagram returned 'not found' for {list_type} query")

    except Exception as e:
        logger.error(f"  ❌ Unexpected error during {list_type} scrape: {e}")

    # Final save
    if accounts:
        _save_incremental(accounts, username, list_type)

    logger.info(f"\n  ✅ {list_type.capitalize()} scrape complete:")
    logger.info(f"     Extracted: {len(accounts)} accounts")
    logger.info(f"     Errors:    {error_count}")

    return accounts


def scrape_profile(loader, target_username, scrape_followers=True, scrape_following=True):
    """
    Full scraping pipeline for a single Instagram profile.
    
    Args:
        loader: Instaloader instance (logged in)
        target_username: Instagram username or URL
        scrape_followers: Whether to scrape followers list
        scrape_following: Whether to scrape following list
    
    Returns:
        dict with keys: profile_stats, followers, following
    """
    result = {
        "profile_url": "",
        "profile_stats": {},
        "followers": [],
        "following": [],
        "scraped_at": datetime.now().isoformat(),
    }

    # ── Fetch profile ──
    stats, profile = get_profile(loader, target_username)

    if not stats or not profile:
        logger.error("Failed to fetch profile — aborting scrape")
        return result

    result["profile_stats"] = stats
    result["profile_url"] = f"https://www.instagram.com/{stats['username']}/"

    # ── Check if private ──
    if stats["is_private"]:
        logger.warning(
            f"\n  ⚠️  @{stats['username']} is PRIVATE"
            f"\n     Followers/following lists are only accessible if you follow this account"
        )

    # ── Scrape followers ──
    if scrape_followers:
        result["followers"] = scrape_list(loader, profile, "followers")

        # Pause between scrapes to avoid rate limiting
        if scrape_following and result["followers"]:
            logger.info("\n  ⏳ Pausing between followers and following scrapes...")
            pause = random.uniform(5, 10)
            time.sleep(pause)

    # ── Scrape following ──
    if scrape_following:
        result["following"] = scrape_list(loader, profile, "following")

    # ── Summary ──
    logger.info(f"\n{'═' * 55}")
    logger.info(f"  SCRAPE SUMMARY — @{stats['username']}")
    logger.info(f"{'═' * 55}")
    logger.info(f"  Followers scraped: {len(result['followers'])}")
    logger.info(f"  Following scraped: {len(result['following'])}")
    logger.info(f"  Total:             {len(result['followers']) + len(result['following'])}")
    logger.info(f"{'═' * 55}\n")

    return result
