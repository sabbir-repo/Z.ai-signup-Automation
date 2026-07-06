import json
import time
import os
import urllib.parse
import threading
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from typing import Dict, Any, Optional, List

_file_lock = threading.Lock()

class TmailorBrowser:
    def __init__(self, storage_file: str = "emails.json", headless: bool = True, proxy: Optional[str] = None, user_agent: Optional[str] = None, viewport: Optional[Dict[str, int]] = None):
        self.storage_file = storage_file
        self.headless = headless
        self.proxy = proxy
        self.user_agent = user_agent
        self.viewport = viewport
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.email_data = None
        self.inbox_callback = None
        self.known_message_ids = set()
        
        with _file_lock:
            if not os.path.exists(self.storage_file):
                with open(self.storage_file, 'w') as f:
                    json.dump([], f)

    def _save_to_json(self, email_data: Dict[str, Any]):
        try:
            with _file_lock:
                with open(self.storage_file, 'r') as f:
                    saved_emails = json.load(f)
                    
                for idx, existing in enumerate(saved_emails):
                    if existing.get('email') == email_data['email']:
                        saved_emails[idx] = email_data
                        break
                else:
                    saved_emails.append(email_data)
                    
                with open(self.storage_file, 'w') as f:
                    json.dump(saved_emails, f, indent=4)
        except Exception as e:
            print(f"Error saving to JSON: {e}")

    def get_saved_emails(self) -> List[Dict[str, Any]]:
        try:
            with _file_lock:
                if os.path.exists(self.storage_file):
                    with open(self.storage_file, 'r') as f:
                        return json.load(f)
        except Exception as e:
            print(f"Error reading JSON file: {e}")
        return []

    def _handle_response(self, response):
        if "/api" in response.url and response.request.method == "POST":
            try:
                # Wait for the response body
                text = response.text()
                if not text:
                    return
                data = json.loads(text)
                
                if data.get("msg") == "ok":
                    # Capture new email token
                    if "email" in data and "accesstoken" in data:
                        self.email_data = {
                            "email": data["email"],
                            "accesstoken": data["accesstoken"],
                            "create_time": data.get("create", int(time.time()))
                        }
                        
                    # Capture inbox updates
                    elif "data" in data and isinstance(data["data"], dict):
                        # The data usually looks like {"user@domain.com": {"msg_id": {...}}}
                        for email_key, messages in data["data"].items():
                            if isinstance(messages, dict):
                                for msg_id, msg_data in messages.items():
                                    if msg_id not in self.known_message_ids:
                                        self.known_message_ids.add(msg_id)
                                        if self.inbox_callback:
                                            self.inbox_callback(msg_data)
            except Exception:
                pass

    def generate_email(self) -> Optional[Dict[str, Any]]:
        """
        Launches the browser, bypasses CF, and grabs a newly generated email.
        """
        self.playwright = sync_playwright().start()
        launch_args = {
            "headless": self.headless,
            "args": ['--disable-blink-features=AutomationControlled']
        }
        if self.proxy:
            launch_args["proxy"] = {"server": self.proxy}
            
        self.browser = self.playwright.chromium.launch(**launch_args)
        context_args = {}
        if self.user_agent:
            context_args["user_agent"] = self.user_agent
        else:
            context_args["user_agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
        if self.viewport:
            context_args["viewport"] = self.viewport
            
        self.context = self.browser.new_context(**context_args)
        self.page = self.context.new_page()
        Stealth().apply_stealth_sync(self.page)
        
        self.page.on("response", self._handle_response)
        
        print("[*] Launching invisible browser and solving Cloudflare Turnstile...")
        try:
            self.page.goto("https://tmailor.com", wait_until="domcontentloaded")
            
            print("[*] Waiting for email to be generated...")
            # Wait up to 30 seconds for the browser to save the generated email to localStorage
            for _ in range(300):
                ls_data = self.page.evaluate("localStorage.getItem('currentEmail')")
                if ls_data:
                    try:
                        data = json.loads(ls_data)
                        if "email" in data and "accesstoken" in data:
                            self.email_data = {
                                "email": data["email"],
                                "accesstoken": data["accesstoken"],
                                "create_time": data.get("create", int(time.time()))
                            }
                            self._save_to_json(self.email_data)
                            return self.email_data
                    except:
                        pass
                time.sleep(0.1)
                
            print("[-] Timeout: Failed to extract email from browser. Cloudflare might still be blocking.")
            self.close()
            return None
        except Exception as e:
            print(f"[-] Error during browser operation: {e}")
            self.close()
            return None

    def restore_session(self, email: str, access_token: str) -> bool:
        """
        Launches the browser and restores an existing email session via localStorage.
        """
        self.playwright = sync_playwright().start()
        launch_args = {
            "headless": self.headless,
            "args": ['--disable-blink-features=AutomationControlled']
        }
        if self.proxy:
            launch_args["proxy"] = {"server": self.proxy}
            
        self.browser = self.playwright.chromium.launch(**launch_args)
        context_args = {}
        if self.user_agent:
            context_args["user_agent"] = self.user_agent
        else:
            context_args["user_agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
        if self.viewport:
            context_args["viewport"] = self.viewport
            
        self.context = self.browser.new_context(**context_args)
        self.page = self.context.new_page()
        Stealth().apply_stealth_sync(self.page)
        
        self.page.on("response", self._handle_response)
        
        print("[*] Launching invisible browser to restore session...")
        try:
            self.page.goto("https://tmailor.com", wait_until="domcontentloaded")
            
            # Inject the saved email and token into local storage
            storage_data = json.dumps({"email": email, "accesstoken": access_token})
            self.page.evaluate(f"localStorage.setItem('currentEmail', '{storage_data}');")
            
            # Reload the page to apply the injected storage
            print("[*] Applying saved session and reloading...")
            self.page.reload(wait_until="domcontentloaded")
            return True
        except Exception as e:
            print(f"[-] Error during session restore: {e}")
            self.close()
            return False

    def listen_for_emails(self, callback):
        """
        Keeps the browser open to listen for WebSockets and API updates.
        Since the page is already open, it handles CF automatically.
        """
        if not self.page:
            print("[-] Browser session is not active. Generate an email first.")
            return
            
        print("[*] Live listener started! Actively polling for new emails...")
        self.inbox_callback = callback
        
        script = """
        async () => {
            const ls = localStorage.getItem('currentEmail');
            if (!ls) return null;
            const data = JSON.parse(ls);
            
            try {
                const response = await fetch('/api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: "listinbox",
                        email: data.email,
                        accesstoken: data.accesstoken
                    })
                });
                return await response.json();
            } catch (e) {
                return null;
            }
        }
        """
        
        try:
            while True:
                # Actively ask the browser to fetch the inbox
                result = self.page.evaluate(script)
                if result and result.get("msg") == "ok":
                    inbox_data = result.get("data")
                    if inbox_data and isinstance(inbox_data, dict):
                        messages_dict = inbox_data
                        
                        # Handle potential nesting: {"email@domain.com": {"msg_id": {...}}}
                        for key in list(messages_dict.keys()):
                            if '@' in key and isinstance(messages_dict[key], dict):
                                messages_dict = messages_dict[key]
                                break
                                
                        for msg_id, msg_data in messages_dict.items():
                            if isinstance(msg_data, dict):
                                if msg_id not in self.known_message_ids:
                                    self.known_message_ids.add(msg_id)
                                    
                                    # Fetch full message body using a new tab
                                    body_text = None
                                    body_html = None
                                    if self.email_data and 'email' in self.email_data:
                                        enc_email = urllib.parse.quote(self.email_data['email'])
                                        url = f"https://tmailor.com/inbox?emailid={msg_id}&source=home&email={enc_email}"
                                        
                                        try:
                                            new_page = self.context.new_page()
                                            new_page.goto(url, wait_until="domcontentloaded")
                                            iframe_element = new_page.wait_for_selector("iframe", timeout=10000)
                                            time.sleep(3) # Wait for iframe to load its blob
                                            iframe_frame = iframe_element.content_frame()
                                            if iframe_frame:
                                                body_text = iframe_frame.locator("body").inner_text()
                                                body_html = iframe_frame.locator("body").inner_html()
                                        except Exception as e:
                                            print(f"[-] Error extracting body: {e}")
                                        finally:
                                            try:
                                                new_page.close()
                                            except:
                                                pass
                                            
                                    if body_text:
                                        msg_data["body"] = body_text
                                        msg_data["html"] = body_html
                                    else:
                                        msg_data["body"] = "[Body could not be extracted]"
                                        msg_data["html"] = ""
                                            
                                    if self.inbox_callback:
                                        self.inbox_callback(msg_data)
                
                time.sleep(5) # Poll every 5 seconds
        except KeyboardInterrupt:
            print("\n[*] Live listener stopped by user.")
            self.close()
            
    def close(self):
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception:
            pass
