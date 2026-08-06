# Instagram Profile Categorizer 🔍

A pure terminal Python tool that scrapes any Instagram profile's followers/following list, categorizes accounts by verification status, privacy, profile completeness, follower tiers & more — then exports structured data to JSON & Excel.

**No browser needed.** Works on Windows, Linux, Termux (Android), macOS.

---

## Features

- 🔐 **Session persistence** — login once, reuse session across runs
- 📊 **Smart categorization** — verified, public/private, business/personal, follower tiers
- 💾 **Incremental saves** — never lose data on crash or rate-limit
- 📄 **Dual export** — JSON + multi-sheet Excel workbook
- 🎨 **Colored terminal output** — clean, readable progress logs
- 🛡️ **Rate-limit handling** — auto-retry with delays
- 📱 **Cross-platform** — Windows, Linux, Termux, macOS

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/Filter-Insta.git
cd Filter-Insta
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> **Termux users:** Run `pkg install python` first if Python isn't installed.

### 3. Set your credentials

Open `config.py` and replace the placeholder credentials:

```python
INSTAGRAM_USERNAME = "your_test_username"   # ← change this
INSTAGRAM_PASSWORD = "your_test_password"   # ← change this
```

> ⚠️ **Use a test/dummy account — never your personal account!**

Or skip this step and use `--interactive` mode (see below).

---

## Usage

### Basic

```bash
python main.py <username>
```

### With interactive login (no need to edit config.py)

```bash
python main.py <username> --interactive
```

### Scrape only followers

```bash
python main.py @nasa --followers-only
```

### Scrape only following

```bash
python main.py natgeo --following-only
```

### Full URL input

```bash
python main.py https://www.instagram.com/natgeo/
```

### Custom batch size

```bash
python main.py username -b 50
```

### Force fresh login (ignore saved session)

```bash
python main.py username --fresh-login
```

---

## Output

Results are saved in the `output/` directory:

| Format | Contents |
|--------|----------|
| `.json` | Full categorized data — all categories, summaries, account details |
| `.xlsx` | Multi-sheet Excel workbook — one sheet per category |

### Categories

| Category | Description |
|----------|-------------|
| **Verified / Unverified** | Official Instagram blue checkmark |
| **Public / Private** | Account privacy status |
| **Complete / Incomplete Profile** | Has profile pic + bio + display name vs bot-like |
| **Business / Personal** | Business account vs personal |
| **Follower Tiers** | Nano (0-1K), Micro (1K-10K), Mid (10K-100K), Macro (100K-1M), Mega (1M+) |

---

## Project Structure

```
Filter-Insta/
├── main.py            # Entry point — run this
├── config.py          # All settings (credentials, limits, thresholds)
├── session.py         # Instagram login & session management
├── scraper.py         # Profile & followers/following data extraction
├── categorizer.py     # Account classification engine
├── exporter.py        # JSON & Excel export
├── requirements.txt   # Python dependencies
├── output/            # Exported JSON & Excel files (auto-created)
├── data/              # Raw scraped data & logs (auto-created)
└── sessions/          # Saved login sessions (auto-created)
```

---

## Requirements

- Python 3.10+
- `instaloader` — Instagram API via HTTP (no browser)
- `pandas` — Data processing
- `openpyxl` — Excel export
- `colorama` — Colored terminal output

---

## ⚠️ Important Notes

1. **Use a test account** — automated access may trigger Instagram's anti-bot systems
2. **Respect rate limits** — the tool adds delays automatically, but don't run it too frequently
3. **Private profiles** — you can only access followers/following of private accounts you follow
4. **2FA support** — if your account has 2FA enabled, use `--interactive` mode to enter the code

---

## License

MIT
