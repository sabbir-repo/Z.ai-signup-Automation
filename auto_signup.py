from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import time
import random
import sys
import os
import json
import threading
import html
import string
import concurrent.futures

# Import local TmailorBrowser
from tmailor_browser import TmailorBrowser

_account_lock = threading.Lock()

class EmailFound(Exception):
    pass

def generate_random_password(length=16):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*")
    ]
    password += [random.choice(chars) for _ in range(length - 4)]
    random.shuffle(password)
    return ''.join(password)

def get_random_name():
    try:
        with open(r"E:\Python Projects\Z.ai\name.json", "r") as f:
            names = json.load(f)
            if names:
                return random.choice(names)["full_name"]
    except Exception as e:
        print(f"Error loading name.json: {e}")
    return "Test User " + str(random.randint(1000, 9999))

def save_account(email, password, accesstoken, session_state=None):
    filename = "accounts.json"
    acc_data = {
        "email": email,
        "password": password,
        "accesstoken": accesstoken
    }
    if session_state:
        acc_data["session_state"] = session_state
    try:
        with _account_lock:
            try:
                with open(filename, "r") as f:
                    accounts = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                accounts = []
                
            accounts.append(acc_data)
            with open(filename, "w") as f:
                json.dump(accounts, f, indent=4)
        print(f"[+] Account saved to {filename}!")
    except Exception as e:
        print(f"[-] Error saving account: {e}")

def get_random_proxy():
    try:
        with open(r"E:\Python Projects\Z.ai\Webshare 10 proxies.txt", "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
            if proxies:
                proxy_str = random.choice(proxies)
                # Webshare format: ip:port:user:password
                parts = proxy_str.split(":")
                if len(parts) == 4:
                    ip, port, user, pwd = parts
                    return f"http://{user}:{pwd}@{ip}:{port}"
                elif len(parts) == 2:
                    ip, port = parts
                    return f"http://{ip}:{port}"
    except Exception as e:
        print(f"Error loading proxies: {e}")
    return None

import urllib.request

def is_proxy_active(proxy_url, timeout=8):
    try:
        if proxy_url:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
            opener = urllib.request.build_opener(proxy_handler)
            req = urllib.request.Request("http://cloudflare.com/cdn-cgi/trace", headers={'User-Agent': 'Mozilla/5.0'})
            with opener.open(req, timeout=timeout) as response:
                if response.status == 200:
                    return True
    except Exception:
        pass
    return False

def wait_for_verification_email(browser_api):
    print("Waiting for verification email...")
    verification_data = {"email_content": None, "email_html": None}
    
    def on_email(msg_data):
        print("\n[+] Verification Email Received!")
        print(f"Subject: {msg_data.get('subject')}")
        body = msg_data.get('body_text') or msg_data.get('body') or msg_data.get('content') or ''
        html_content = msg_data.get('html') or ''
        verification_data["email_content"] = body
        verification_data["email_html"] = html_content
        
        raise EmailFound()
        
    try:
        browser_api.listen_for_emails(on_email)
    except EmailFound:
        pass
    except KeyboardInterrupt:
        pass
        
    return verification_data

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
]

VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
    {"width": 1600, "height": 900}
]

def auto_signup_with_retry(proxy=None, max_retries=3):
    for attempt in range(1, max_retries + 1):
        print(f"\n[{attempt}/{max_retries}] Attempting account creation...")
        success = auto_signup(proxy)
        if success:
            print(f"[+] Account creation successful on attempt {attempt}!")
            return True
        else:
            print(f"[-] Attempt {attempt} failed.")
            if attempt < max_retries:
                print("[*] Retrying in 5 seconds...")
                time.sleep(5)
            else:
                print("[-] All retries failed for this thread.")
                return False

def auto_signup(proxy=None):
    try:
        if proxy and proxy.lower() in ["none", "n"]:
            proxy = None
            print("[*] Running without proxy (using local IP)...")
        elif not proxy:
            for attempt in range(1, 6):
                proxy = get_random_proxy()
                masked_proxy = proxy.split('@')[0] + '@...' if proxy and '@' in proxy else proxy or 'None'
                print(f"[*] Checking random proxy {masked_proxy} (Attempt {attempt}/5)...")
                if proxy and is_proxy_active(proxy):
                    print(f"[+] Proxy {masked_proxy} is active!")
                    break
                else:
                    print(f"[-] Proxy {masked_proxy} is dead or slow. Trying another...")
            else:
                print("[-] Could not find an active proxy after 5 attempts. Exiting thread.")
                return False
        else:
            print(f"[*] Checking provided proxy...")
            if not is_proxy_active(proxy):
                print(f"[-] Provided proxy is dead. Exiting thread.")
                return False
            print("[+] Provided proxy is active!")
            
        name = get_random_name()
        password = generate_random_password()
        user_agent = random.choice(USER_AGENTS)
        viewport = random.choice(VIEWPORTS)
        
        masked_proxy = proxy.split('@')[0] + '@...' if proxy and '@' in proxy else proxy or 'None'
        print(f"[*] Starting signup for {name} with proxy {masked_proxy}...")
        
        print("0. Initializing TempMail to get a disposable email...")
        email_browser = TmailorBrowser(
            storage_file=r"E:\Python Projects\TempMail\emails.json", 
            headless=True, 
            proxy=proxy,
            user_agent=user_agent,
            viewport=viewport
        )
        email_data = email_browser.generate_email()
        
        if not email_data:
            print(f"[-] Failed to generate a temporary email for {name}.")
            return False
            
        email = email_data["email"]
        access_token = email_data.get("accesstoken", "")
        print(f"[+] Using temporary email: {email}")

        p = email_browser.playwright

        launch_args = {
            "headless": False,
            "args": ["--disable-blink-features=AutomationControlled"]
        }
        if proxy:
            launch_args["proxy"] = {"server": proxy}
            
        browser = p.chromium.launch(**launch_args)
        context = browser.new_context(
            viewport=viewport,
            user_agent=user_agent
        )
        page = context.new_page()
        
        Stealth().apply_stealth_sync(page)

        print("1. Navigating to the signup page...")
        page.goto("https://chat.z.ai/auth?action=signup", wait_until="domcontentloaded")

        print("2. Filling out the signup form with typing simulation...")
        page.locator('input[autocomplete="name"]').wait_for(state="visible", timeout=20000)
        page.locator('input[autocomplete="name"]').press_sequentially(name, delay=100)
        page.locator('input[autocomplete="email"]').press_sequentially(email, delay=100)
        page.locator('input[type="password"]').press_sequentially(password, delay=100)
        
        print("3. Waiting for Aliyun Captcha to load and clicking it to open...")
        
        try:
            captcha_box = page.locator('#aliyunCaptcha-captcha-text-box')
            captcha_box.wait_for(state="visible", timeout=15000)
            captcha_box.click(force=True)
            print("4. Please solve the captcha manually in the browser window...")
        except Exception as e:
            print("[-] Captcha box not found. It might be already solved or UI changed.")

        def is_captcha_solved():
            try:
                # 0. Check for the specific Verification Passed text as requested by the user
                if page.locator('text="Verification Passed!"').is_visible(timeout=100) or \
                   page.locator('text="Verification passed!"').is_visible(timeout=100):
                    return True
                    
                # 1. Check if the page has already proceeded to the next step
                if page.locator('text="verify"').is_visible(timeout=100) or \
                   page.locator('text="Verification"').is_visible(timeout=100) or \
                   page.locator('text="Check your inbox"').is_visible(timeout=100):
                    return True
                    
                # 2. First, check if submit button is enabled. If it is enabled, captcha is definitely solved.
                submit_btn = page.locator('button.ButtonCreateAccount').first
                if submit_btn.is_visible(timeout=100) and submit_btn.is_enabled(timeout=100):
                    return True
                    
                # 3. Check for the green tick icon
                if page.locator('.nc_iconfont.icon_pass').is_visible(timeout=100):
                    return True
                    
                # 4. Check for text inside the captcha box
                captcha_box = page.locator('#aliyunCaptcha-captcha-text-box')
                if captcha_box.is_visible(timeout=100):
                    success_text = captcha_box.inner_text(timeout=100)
                    success_keywords = ["Success", "Verified", "success", "verified", "completed", "Completed", "成功", "完成"]
                    if any(word in success_text for word in success_keywords):
                        return True
                return False
            except Exception:
                # If element is detached or other error, assume it might not be solved yet
                return False

        captcha_event = threading.Event()
        
        def on_aliyun_response(response):
            try:
                # Aliyun verification endpoint usually requests 'analyze' or similar from aliyun.com domains
                if "aliyun.com" in response.url and response.status == 200:
                    captcha_event.set()
            except:
                pass
                
        page.on("response", on_aliyun_response)

        print("[*] Waiting for captcha completion (Instant Network/UI Intercept Mode)...")
        # Loop with a very fast wait, combining network event and UI fallback
        while not captcha_event.is_set():
            if is_captcha_solved():
                captcha_event.set()
                break
            captcha_event.wait(timeout=0.2)
            
        # Clean up the listener
        try:
            page.remove_listener("response", on_aliyun_response)
        except:
            pass
            
        print("[+] Captcha solved instantly detected!")
        
        submit_btn = page.locator('button.ButtonCreateAccount').first
        try:
            submit_btn.wait_for(state="visible", timeout=5000)
            submit_btn.click()
            print("[+] Clicked 'Create Account' button!")
        except Exception as e:
            print(f"[-] 'Create Account' button not visible or clickable: {e}")
            # Fallback to the selector user provided if possible or just try pressing Enter
            page.keyboard.press("Enter")
            
        print("5. Waiting for verification step...")
        time.sleep(5)
        
        print("6. Checking inbox for verification email...")
        email_data_res = wait_for_verification_email(email_browser)
        
        email_content = email_data_res.get("email_content")
        email_html = email_data_res.get("email_html", "")
        
        if email_content or email_html:
            import re
            link_match = re.search(r'href=["\'](https?://[^"\']+)["\']', email_html)
            
            verification_link = None
            if link_match:
                verification_link = link_match.group(1)
            
            if verification_link:
                verification_link = html.unescape(verification_link)
                print(f"[*] Found Verification Link: {verification_link}")
                print("[*] Navigating to the verification link...")
                try:
                    page.goto(verification_link, wait_until="networkidle")
                    print("[+] Successfully reached verification page!")
                    
                    print("[*] Filling out Complete Registration form with typing simulation...")
                    page.wait_for_selector('input[type="password"]', timeout=15000)
                    
                    page.locator('input[type="password"]').nth(0).press_sequentially(password, delay=100)
                    page.locator('input[type="password"]').nth(1).press_sequentially(password, delay=100)
                    
                    submit_btn = page.locator('button[type="submit"]').first
                    if submit_btn.is_visible():
                        submit_btn.click()
                        print("[+] Clicked Complete Registration button!")
                    else:
                        page.get_by_role("button", name="Complete Registration").click()
                        print("[+] Clicked Complete Registration button (fallback)!")
                        
                    session_state = None
                    try:
                        print("[*] Waiting for redirect to dashboard (https://chat.z.ai/)...")
                        page.wait_for_url(re.compile(r"chat\.z\.ai"), timeout=20000)
                        print("[+] Redirect successful! Waiting for page to fully load...")
                        page.wait_for_load_state("domcontentloaded", timeout=15000)
                        time.sleep(2)
                        
                        session_state = context.storage_state()
                        print("[+] Browser session state captured successfully.")
                    except Exception as e:
                        print(f"[-] Waited for redirect but timed out or failed: {e}")
                        
                    print("[+] Signup process completely finished!")
                    save_account(email, password, access_token, session_state)
                    return True # Successfully created
                except Exception as e:
                    print(f"[-] Error navigating to or filling verification link: {e}")
                    return False
            else:
                print("[-] Could not find the verification link automatically in the email HTML.")
                return False
        else:
            print("Failed to receive verification email.")
            return False

    except Exception as e:
        import traceback
        print(f"[-] Unexpected error in auto_signup: {e}")
        traceback.print_exc()
        return False
    finally:
        if 'browser' in locals() and browser:
            try:
                browser.close()
            except:
                pass
        if 'email_browser' in locals() and email_browser:
            try:
                email_browser.close()
            except:
                pass

if __name__ == "__main__":
    max_threads = os.cpu_count() or 4
    try:
        thread_input = input(f"Enter number of threads to run concurrently (max {max_threads}) [default 1]: ").strip()
        num_threads = int(thread_input) if thread_input else 1
    except ValueError:
        num_threads = 1
        
    num_threads = min(max_threads, max(1, num_threads))
    
    proxy_input = input("Enter proxy (press Enter for local IP, type 'Y' for random Webshare): ").strip()
    if not proxy_input:
        proxy = "none"
    elif proxy_input.lower() == "y":
        proxy = None
    else:
        proxy = proxy_input
    
    total_accounts_input = input(f"Enter total number of accounts to create [default {num_threads}]: ").strip()
    try:
        total_accounts = int(total_accounts_input) if total_accounts_input else num_threads
    except ValueError:
        total_accounts = num_threads
        
    if total_accounts < num_threads:
        num_threads = total_accounts

    print(f"Starting {total_accounts} account creation(s) with {num_threads} thread(s)...")
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(auto_signup_with_retry, proxy) for _ in range(total_accounts)]
            # Use a timeout in wait so KeyboardInterrupt can be caught immediately in Windows
            while True:
                done, not_done = concurrent.futures.wait(futures, timeout=1.0)
                if not not_done:
                    break
    except KeyboardInterrupt:
        print("\n[!] Ctrl+C detected! Stopping all tasks immediately...")
        os._exit(1)
        
    print("All tasks completed!")
