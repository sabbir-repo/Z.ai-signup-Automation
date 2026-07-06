# Z.ai Auto Signup Bot

An automated tool built with Python and Playwright to create accounts on [Z.ai](https://chat.z.ai/) by utilizing temporary emails and bypassing anti-bot protections (Cloudflare Turnstile & Aliyun Captcha).

## Features

- **Automated Email Generation**: Uses `tmailor_browser.py` to fetch highly credible disposable emails.
- **Advanced Anti-Bot Evasion**: Employs `playwright-stealth` and dynamic mouse movement simulation to bypass Cloudflare Turnstile and Aliyun Sliding Captchas.
- **Proxy Support**: Supports rotating proxies (e.g., Webshare) for creating multiple accounts securely without IP bans.
- **Concurrent Execution**: Multi-threaded architecture allows creating multiple accounts simultaneously.
- **Super Secure Build**: Can be compiled into a standalone, heavily obfuscated executable using Nuitka and MinGW64.

## Prerequisites

If you are running the source code directly, you need:
- Python 3.12 (Recommended for compilation compatibility)
- Node.js (for Playwright browsers)

### Installation

1. Create a virtual environment and activate it:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

## Usage

You can run the script via Python:
```bash
python auto_signup.py
```

Upon running, you will be prompted to:
1. Enter the number of threads for concurrent creation.
2. Select proxy preferences (Local IP or Random Webshare proxy).
3. Enter the total number of accounts to generate.

All successfully created accounts will be saved automatically to `accounts.json`.

## Compilation (Standalone Executable)

To build a secure, standalone `.exe` file that doesn't require Python or Playwright installed on the host machine, we use **Nuitka**.

Run the following command in your activated Python 3.12 environment:
```powershell
python -m nuitka --mingw64 --standalone --onefile --assume-yes-for-downloads --playwright-include-browser=all auto_signup.py
```
This will generate an `auto_signup.exe` file.

## Disclaimer

This script is for educational purposes only. Automated account creation may violate the Terms of Service of the target platform. Use responsibly.
