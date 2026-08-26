"""
Instagram Profile Categorizer — Categorization Engine
Processes raw scraped data and organizes accounts into categorized buckets.
Now uses Instaloader data format with real follower counts.
"""

import logging

import config

logger = logging.getLogger(__name__)


def _determine_follower_tier(follower_count):
    """
    Classify an account into a follower tier based on count.
    
    Returns:
        str: tier name ('nano', 'micro', 'mid', 'macro', 'mega', or 'unknown')
    """
    if follower_count is None or follower_count < 0:
        return "unknown"
    elif follower_count <= config.TIER_NANO_MAX:
        return "nano"
    elif follower_count <= config.TIER_MICRO_MAX:
        return "micro"
    elif follower_count <= config.TIER_MID_MAX:
        return "mid"
    elif follower_count <= config.TIER_MACRO_MAX:
        return "macro"
    else:
        return "mega"


def _determine_privacy_status(account):
    """
    Determine if an account is public or private.
    Instaloader gives us the actual is_private field.
    
    Returns:
        str: 'public' or 'private'
    """
    is_private = account.get("is_private", False)
    return "private" if is_private else "public"


def _determine_profile_completeness(account):
    """
    Determine if a profile is complete or looks like a bot/empty account.
    
    Complete = has custom profile picture AND has bio AND has a display name
    Incomplete = missing any of these (bot-like behavior)
    
    Returns:
        str: 'complete' or 'incomplete'
    """
    has_pic = account.get("has_profile_pic", False)
    has_name = bool(account.get("display_name", "").strip())
    has_bio = bool(account.get("bio", "").strip())

    if has_pic and has_name and has_bio:
        return "complete"
    else:
        return "incomplete"


def categorize_accounts(raw_accounts, list_type="followers"):
    """
    Main categorization pipeline. Takes raw scraped account data and
    organizes them into multiple category buckets.
    
    With Instaloader, we get REAL follower counts per account,
    so follower tier categorization is now accurate.
    
    Args:
        raw_accounts: list of account dicts from scraper
        list_type: 'followers' or 'following' (for labeling)
    
    Returns:
        dict with categorized data
    """
    logger.info(f"Categorizing {len(raw_accounts)} {list_type} accounts...")

    # Initialize category buckets
    categories = {
        "all": [],
        "verified": [],
        "unverified": [],
        "public": [],
        "private": [],
        "complete_profile": [],
        "incomplete_profile": [],
        "nano": [],
        "micro": [],
        "mid": [],
        "macro": [],
        "mega": [],
        "unknown_tier": [],
        "business": [],
        "personal": [],
    }

    for account in raw_accounts:
        enriched = account.copy()

        # ── Verification status ──
        is_verified = account.get("is_verified", False)
        enriched["category_verified"] = "verified" if is_verified else "unverified"

        # ── Privacy status (real data from Instaloader) ──
        privacy = _determine_privacy_status(account)
        enriched["category_privacy"] = privacy

        # ── Profile completeness ──
        completeness = _determine_profile_completeness(account)
        enriched["category_completeness"] = completeness

        # ── Follower tier (real follower counts from Instaloader!) ──
        follower_count = account.get("followers", 0)
        tier = _determine_follower_tier(follower_count)
        enriched["category_tier"] = tier

        # ── Business vs Personal ──
        is_business = account.get("is_business", False)
        enriched["category_account_type"] = "business" if is_business else "personal"

        # ── Add to category buckets ──
        categories["all"].append(enriched)

        # Verification
        if is_verified:
            categories["verified"].append(enriched)
        else:
            categories["unverified"].append(enriched)

        # Privacy
        if privacy == "public":
            categories["public"].append(enriched)
        else:
            categories["private"].append(enriched)

        # Profile completeness
        if completeness == "complete":
            categories["complete_profile"].append(enriched)
        else:
            categories["incomplete_profile"].append(enriched)

        # Follower tier
        if tier in categories:
            categories[tier].append(enriched)
        else:
            categories["unknown_tier"].append(enriched)

        # Business / Personal
        if is_business:
            categories["business"].append(enriched)
        else:
            categories["personal"].append(enriched)

    # ── Generate summary statistics ──
    total = len(raw_accounts)
    summary = {
        "list_type": list_type,
        "total_accounts": total,
        "verified_count": len(categories["verified"]),
        "verified_pct": round(len(categories["verified"]) / total * 100, 1) if total else 0,
        "unverified_count": len(categories["unverified"]),
        "public_count": len(categories["public"]),
        "public_pct": round(len(categories["public"]) / total * 100, 1) if total else 0,
        "private_count": len(categories["private"]),
        "private_pct": round(len(categories["private"]) / total * 100, 1) if total else 0,
        "complete_profile_count": len(categories["complete_profile"]),
        "complete_profile_pct": round(len(categories["complete_profile"]) / total * 100, 1) if total else 0,
        "incomplete_profile_count": len(categories["incomplete_profile"]),
        "business_count": len(categories["business"]),
        "business_pct": round(len(categories["business"]) / total * 100, 1) if total else 0,
        "personal_count": len(categories["personal"]),
        "tier_nano": len(categories["nano"]),
        "tier_micro": len(categories["micro"]),
        "tier_mid": len(categories["mid"]),
        "tier_macro": len(categories["macro"]),
        "tier_mega": len(categories["mega"]),
        "tier_unknown": len(categories["unknown_tier"]),
    }

    categories["summary"] = summary

    # ── Log summary ──
    logger.info("=" * 55)
    logger.info(f"  CATEGORIZATION RESULTS -- {list_type.upper()}")
    logger.info("=" * 55)
    logger.info(f"  Total accounts:       {total}")
    logger.info(f"  --- Verification ---")
    logger.info(f"  Verified:             {summary['verified_count']} ({summary['verified_pct']}%)")
    logger.info(f"  Unverified:           {summary['unverified_count']}")
    logger.info(f"  --- Privacy ---------")
    logger.info(f"  Public:               {summary['public_count']} ({summary['public_pct']}%)")
    logger.info(f"  Private:              {summary['private_count']} ({summary['private_pct']}%)")
    logger.info(f"  --- Profile ---------")
    logger.info(f"  Complete profiles:    {summary['complete_profile_count']} ({summary['complete_profile_pct']}%)")
    logger.info(f"  Incomplete profiles:  {summary['incomplete_profile_count']}")
    logger.info(f"  --- Account Type ----")
    logger.info(f"  Business:             {summary['business_count']} ({summary['business_pct']}%)")
    logger.info(f"  Personal:             {summary['personal_count']}")
    logger.info(f"  --- Follower Tiers --")
    logger.info(f"  Nano (0-1K):          {summary['tier_nano']}")
    logger.info(f"  Micro (1K-10K):       {summary['tier_micro']}")
    logger.info(f"  Mid-Tier (10K-100K):  {summary['tier_mid']}")
    logger.info(f"  Macro (100K-1M):      {summary['tier_macro']}")
    logger.info(f"  Mega (1M+):           {summary['tier_mega']}")
    logger.info("=" * 55)

    return categories


def categorize_full_scrape(scrape_result):
    """
    Categorize both followers and following from a full scrape result.
    
    Args:
        scrape_result: dict from scraper.scrape_profile()
    
    Returns:
        dict with keys: profile_stats, followers_categorized, following_categorized
    """
    result = {
        "profile_stats": scrape_result.get("profile_stats", {}),
        "profile_url": scrape_result.get("profile_url", ""),
        "scraped_at": scrape_result.get("scraped_at", ""),
    }

    # Categorize followers
    followers = scrape_result.get("followers", [])
    if followers:
        result["followers_categorized"] = categorize_accounts(followers, "followers")
        logger.info(f"Categorized {len(followers)} followers")
    else:
        result["followers_categorized"] = {"summary": {"total_accounts": 0}, "all": []}
        logger.info("No followers data to categorize")

    # Categorize following
    following = scrape_result.get("following", [])
    if following:
        result["following_categorized"] = categorize_accounts(following, "following")
        logger.info(f"Categorized {len(following)} following")
    else:
        result["following_categorized"] = {"summary": {"total_accounts": 0}, "all": []}
        logger.info("No following data to categorize")

    return result
