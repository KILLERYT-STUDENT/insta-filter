"""
Instagram Profile Categorizer — Export Module
Handles exporting categorized data to JSON and Excel formats.
"""

import json
import os
import sys
import logging
from datetime import datetime

import pandas as pd

import config

logger = logging.getLogger(__name__)


def _sanitize_filename(text):
    """Remove or replace characters that are invalid in filenames."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        text = text.replace(char, "_")
    return text.strip()


def _generate_filename(profile_username, list_type, extension):
    """Generate a timestamped filename for exports."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_username = _sanitize_filename(profile_username)
    return f"{safe_username}_{list_type}_{timestamp}.{extension}"


def export_to_json(categorized_data, profile_username="profile"):
    """
    Export full categorized data to a pretty-printed JSON file.
    
    Args:
        categorized_data: dict from categorizer.categorize_full_scrape()
        profile_username: username for filename
    
    Returns:
        str: path to the exported JSON file
    """
    filename = _generate_filename(profile_username, "categorized", "json")
    filepath = os.path.join(config.OUTPUT_DIR, filename)

    try:
        # Convert data to JSON-serializable format
        export_data = {
            "export_info": {
                "tool": "Instagram Profile Categorizer",
                "exported_at": datetime.now().isoformat(),
                "profile": profile_username,
                "profile_url": categorized_data.get("profile_url", ""),
            },
            "profile_stats": categorized_data.get("profile_stats", {}),
        }

        # Add followers data
        followers_cat = categorized_data.get("followers_categorized", {})
        if followers_cat:
            export_data["followers"] = {
                "summary": followers_cat.get("summary", {}),
                "verified": followers_cat.get("verified", []),
                "unverified": followers_cat.get("unverified", []),
                "public": followers_cat.get("public", []),
                "private": followers_cat.get("private", []),
                "complete_profile": followers_cat.get("complete_profile", []),
                "incomplete_profile": followers_cat.get("incomplete_profile", []),
                "tiers": {
                    "nano": followers_cat.get("nano", []),
                    "micro": followers_cat.get("micro", []),
                    "mid": followers_cat.get("mid", []),
                    "macro": followers_cat.get("macro", []),
                    "mega": followers_cat.get("mega", []),
                },
                "all_accounts": followers_cat.get("all", []),
            }

        # Add following data
        following_cat = categorized_data.get("following_categorized", {})
        if following_cat:
            export_data["following"] = {
                "summary": following_cat.get("summary", {}),
                "verified": following_cat.get("verified", []),
                "unverified": following_cat.get("unverified", []),
                "public": following_cat.get("public", []),
                "private": following_cat.get("private", []),
                "complete_profile": following_cat.get("complete_profile", []),
                "incomplete_profile": following_cat.get("incomplete_profile", []),
                "tiers": {
                    "nano": following_cat.get("nano", []),
                    "micro": following_cat.get("micro", []),
                    "mid": following_cat.get("mid", []),
                    "macro": following_cat.get("macro", []),
                    "mega": following_cat.get("mega", []),
                },
                "all_accounts": following_cat.get("all", []),
            }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=config.JSON_INDENT, ensure_ascii=False)

        file_size_kb = os.path.getsize(filepath) / 1024
        logger.info(f"JSON exported -> {filepath} ({file_size_kb:.1f} KB)")
        return filepath

    except Exception as e:
        logger.error(f"Failed to export JSON: {e}")
        return ""


def _accounts_to_dataframe(accounts, category_label=""):
    """
    Convert a list of account dicts to a pandas DataFrame with clean columns.
    """
    if not accounts:
        return pd.DataFrame()

    df = pd.DataFrame(accounts)

    # Define column order and rename for readability
    column_mapping = {
        "username": "Username",
        "display_name": "Display Name",
        "profile_url": "Profile URL",
        "followers": "Followers",
        "following": "Following",
        "posts": "Posts",
        "bio": "Bio",
        "is_verified": "Verified",
        "is_private": "Private",
        "is_business": "Business Account",
        "business_category": "Business Category",
        "has_profile_pic": "Has Profile Pic",
        "category_verified": "Verification",
        "category_privacy": "Privacy",
        "category_completeness": "Profile Complete",
        "category_tier": "Follower Tier",
        "category_account_type": "Account Type",
        "scraped_at": "Scraped At",
    }

    # Only keep columns that exist
    existing_cols = [col for col in column_mapping.keys() if col in df.columns]
    df = df[existing_cols]
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in existing_cols})

    # Clean up boolean columns for readability
    bool_replacements = {True: "Yes", False: "No"}
    for col in ["Verified", "Private", "Business Account", "Has Profile Pic"]:
        if col in df.columns:
            df[col] = df[col].map(bool_replacements).fillna(df[col])

    return df


def export_to_excel(categorized_data, profile_username="profile"):
    """
    Export categorized data to a multi-sheet Excel workbook.
    Each category gets its own sheet.
    
    Args:
        categorized_data: dict from categorizer.categorize_full_scrape()
        profile_username: username for filename
    
    Returns:
        str: path to the exported Excel file
    """
    filename = _generate_filename(profile_username, "categorized", "xlsx")
    filepath = os.path.join(config.OUTPUT_DIR, filename)

    try:
        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            sheets_written = 0

            # ── Summary sheet ──
            summary_data = []

            # Profile stats
            profile_stats = categorized_data.get("profile_stats", {})
            if profile_stats:
                summary_data.append({
                    "Section": "PROFILE INFO",
                    "Metric": "Username",
                    "Value": f"@{profile_stats.get('username', 'N/A')}",
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Full Name",
                    "Value": profile_stats.get("full_name", "N/A"),
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Posts",
                    "Value": profile_stats.get("posts", 0),
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Followers",
                    "Value": profile_stats.get("followers", 0),
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Following",
                    "Value": profile_stats.get("following", 0),
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Verified",
                    "Value": "Yes" if profile_stats.get("is_verified") else "No",
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Private",
                    "Value": "Yes" if profile_stats.get("is_private") else "No",
                })
                summary_data.append({"Section": "", "Metric": "", "Value": ""})

            # Followers summary
            followers_cat = categorized_data.get("followers_categorized", {})
            followers_summary = followers_cat.get("summary", {})
            if followers_summary and followers_summary.get("total_accounts", 0) > 0:
                summary_data.append({
                    "Section": "FOLLOWERS BREAKDOWN",
                    "Metric": "Total Scraped",
                    "Value": followers_summary.get("total_accounts", 0),
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Verified",
                    "Value": f"{followers_summary.get('verified_count', 0)} ({followers_summary.get('verified_pct', 0)}%)",
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Public",
                    "Value": f"{followers_summary.get('public_count', 0)} ({followers_summary.get('public_pct', 0)}%)",
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Private",
                    "Value": f"{followers_summary.get('private_count', 0)} ({followers_summary.get('private_pct', 0)}%)",
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Complete Profiles",
                    "Value": f"{followers_summary.get('complete_profile_count', 0)} ({followers_summary.get('complete_profile_pct', 0)}%)",
                })
                summary_data.append({"Section": "", "Metric": "", "Value": ""})

            # Following summary
            following_cat = categorized_data.get("following_categorized", {})
            following_summary = following_cat.get("summary", {})
            if following_summary and following_summary.get("total_accounts", 0) > 0:
                summary_data.append({
                    "Section": "FOLLOWING BREAKDOWN",
                    "Metric": "Total Scraped",
                    "Value": following_summary.get("total_accounts", 0),
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Verified",
                    "Value": f"{following_summary.get('verified_count', 0)} ({following_summary.get('verified_pct', 0)}%)",
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Public",
                    "Value": f"{following_summary.get('public_count', 0)} ({following_summary.get('public_pct', 0)}%)",
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Private",
                    "Value": f"{following_summary.get('private_count', 0)} ({following_summary.get('private_pct', 0)}%)",
                })
                summary_data.append({
                    "Section": "",
                    "Metric": "Complete Profiles",
                    "Value": f"{following_summary.get('complete_profile_count', 0)} ({following_summary.get('complete_profile_pct', 0)}%)",
                })

            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name="Summary", index=False)
                sheets_written += 1

            # ── Category sheets for FOLLOWERS ──
            if followers_cat:
                for category_key, sheet_name in config.EXCEL_SHEET_NAMES.items():
                    accounts = followers_cat.get(category_key, [])
                    if accounts:
                        df = _accounts_to_dataframe(accounts, category_key)
                        if not df.empty:
                            # Prefix sheet name to distinguish from following
                            full_sheet_name = f"F_{sheet_name}"[:31]  # Excel max 31 chars
                            df.to_excel(writer, sheet_name=full_sheet_name, index=False)
                            sheets_written += 1

            # ── Category sheets for FOLLOWING ──
            if following_cat:
                for category_key, sheet_name in config.EXCEL_SHEET_NAMES.items():
                    accounts = following_cat.get(category_key, [])
                    if accounts:
                        df = _accounts_to_dataframe(accounts, category_key)
                        if not df.empty:
                            full_sheet_name = f"G_{sheet_name}"[:31]  # Excel max 31 chars
                            df.to_excel(writer, sheet_name=full_sheet_name, index=False)
                            sheets_written += 1

            # ── Guard: ensure at least one sheet exists ──
            if sheets_written == 0:
                empty_df = pd.DataFrame(
                    [{"Info": "No data was scraped. The target profile may be private or empty."}]
                )
                empty_df.to_excel(writer, sheet_name="No Data", index=False)
                sheets_written += 1

            # ── Auto-adjust column widths ──
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if cell.value:
                                max_length = max(max_length, len(str(cell.value)))
                        except Exception:
                            pass
                    adjusted_width = min(max_length + 3, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

        file_size_kb = os.path.getsize(filepath) / 1024
        logger.info(
            f"Excel exported -> {filepath} "
            f"({sheets_written} sheets, {file_size_kb:.1f} KB)"
        )
        return filepath

    except Exception as e:
        logger.error(f"Failed to export Excel: {e}")
        return ""


def generate_summary_report(categorized_data):
    """
    Print a formatted summary report to the console.
    
    Args:
        categorized_data: dict from categorizer.categorize_full_scrape()
    """
    import io

    profile_stats = categorized_data.get("profile_stats", {})
    username = profile_stats.get("username", "Unknown")

    # Build the report as a string first, then write with proper encoding
    lines = []
    lines.append("")
    lines.append("")
    lines.append("+" + "=" * 58 + "+")
    lines.append("|" + " INSTAGRAM PROFILE CATEGORIZER -- FINAL REPORT".center(58) + "|")
    lines.append("+" + "=" * 58 + "+")

    # Profile info
    lines.append("|" + f"  Profile: @{username}".ljust(58) + "|")
    lines.append("|" + f"  Posts: {profile_stats.get('posts', 'N/A')}  |  "
                       f"Followers: {profile_stats.get('followers', 'N/A')}  |  "
                       f"Following: {profile_stats.get('following', 'N/A')}".ljust(58) + "|")

    verified_str = "[V] VERIFIED" if profile_stats.get("is_verified") else "[X] Not Verified"
    private_str = "[Private]" if profile_stats.get("is_private") else "[Public]"
    lines.append("|" + f"  {verified_str}  |  {private_str}".ljust(58) + "|")

    lines.append("+" + "=" * 58 + "+")

    # Followers breakdown
    followers_cat = categorized_data.get("followers_categorized", {})
    followers_summary = followers_cat.get("summary", {})
    total_followers = followers_summary.get("total_accounts", 0)

    if total_followers > 0:
        lines.append("|" + " FOLLOWERS ANALYSIS".center(58) + "|")
        lines.append("+" + "-" * 58 + "+")
        lines.append("|" + f"  Total scraped: {total_followers}".ljust(58) + "|")
        lines.append("|" + f"  [V] Verified:        {followers_summary.get('verified_count', 0):>5}  ({followers_summary.get('verified_pct', 0)}%)".ljust(58) + "|")
        lines.append("|" + f"  [Pub] Public:        {followers_summary.get('public_count', 0):>5}  ({followers_summary.get('public_pct', 0)}%)".ljust(58) + "|")
        lines.append("|" + f"  [Prv] Private:       {followers_summary.get('private_count', 0):>5}  ({followers_summary.get('private_pct', 0)}%)".ljust(58) + "|")
        lines.append("|" + f"  [OK] Complete:       {followers_summary.get('complete_profile_count', 0):>5}  ({followers_summary.get('complete_profile_pct', 0)}%)".ljust(58) + "|")
        lines.append("|" + f"  [--] Incomplete:     {followers_summary.get('incomplete_profile_count', 0):>5}".ljust(58) + "|")

        lines.append("+" + "-" * 58 + "+")
        lines.append("|" + "  Follower Tiers:".ljust(58) + "|")
        lines.append("|" + f"    Nano (0-1K):       {followers_summary.get('tier_nano', 0):>5}".ljust(58) + "|")
        lines.append("|" + f"    Micro (1K-10K):    {followers_summary.get('tier_micro', 0):>5}".ljust(58) + "|")
        lines.append("|" + f"    Mid (10K-100K):    {followers_summary.get('tier_mid', 0):>5}".ljust(58) + "|")
        lines.append("|" + f"    Macro (100K-1M):   {followers_summary.get('tier_macro', 0):>5}".ljust(58) + "|")
        lines.append("|" + f"    Mega (1M+):        {followers_summary.get('tier_mega', 0):>5}".ljust(58) + "|")

    # Following breakdown
    following_cat = categorized_data.get("following_categorized", {})
    following_summary = following_cat.get("summary", {})
    total_following = following_summary.get("total_accounts", 0)

    if total_following > 0:
        lines.append("+" + "=" * 58 + "+")
        lines.append("|" + " FOLLOWING ANALYSIS".center(58) + "|")
        lines.append("+" + "-" * 58 + "+")
        lines.append("|" + f"  Total scraped: {total_following}".ljust(58) + "|")
        lines.append("|" + f"  [V] Verified:        {following_summary.get('verified_count', 0):>5}  ({following_summary.get('verified_pct', 0)}%)".ljust(58) + "|")
        lines.append("|" + f"  [Pub] Public:        {following_summary.get('public_count', 0):>5}  ({following_summary.get('public_pct', 0)}%)".ljust(58) + "|")
        lines.append("|" + f"  [Prv] Private:       {following_summary.get('private_count', 0):>5}  ({following_summary.get('private_pct', 0)}%)".ljust(58) + "|")
        lines.append("|" + f"  [OK] Complete:       {following_summary.get('complete_profile_count', 0):>5}  ({following_summary.get('complete_profile_pct', 0)}%)".ljust(58) + "|")

    lines.append("+" + "=" * 58 + "+")
    lines.append("")

    # Print with encoding safety for Windows
    report = "\n".join(lines)
    try:
        # Try utf-8 output first
        out = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)
        out.write(report + "\n")
        out.flush()
    except Exception:
        # Fallback to plain print
        print(report)
