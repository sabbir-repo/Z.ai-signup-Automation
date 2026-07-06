from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def handle_response(response):
            try:
                if response.request.resource_type in ['script']:
                    if 'AliyunCaptcha' in response.url or 'jquery' in response.url: return
                    filename = response.url.split('/')[-1].split('?')[0]
                    if filename:
                        filepath = os.path.join('aliyun_scripts', filename)
                        with open(filepath, 'wb') as f: f.write(response.body())
                        print(f'[+] JS: {filename}')
            except Exception as e: pass

        page.on('response', handle_response)
        page.goto('https://chat.z.ai/auth/signup', wait_until='networkidle')
        
        # Trigger captcha loading by typing
        print('[*] Typing in email to trigger captcha...')
        try:
            page.locator('input[placeholder*="email"]').fill('test@example.com')
            page.locator('input[placeholder*="username"]').fill('testuser')
        except Exception as e:
            pass
            
        page.wait_for_timeout(5000)
        browser.close()

if __name__ == '__main__':
    run()
