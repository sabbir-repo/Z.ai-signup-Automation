from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def handle_response(response):
            if 'aliyun' in response.url or 'captcha' in response.url.lower():
                print(f'[ALIYUN] {response.url}')

        page.on('response', handle_response)
        page.goto('https://chat.z.ai/auth/signup', wait_until='networkidle')
        
        print('[*] Typing in email to trigger captcha...')
        try:
            page.locator('input[placeholder*="email"]').fill('test@example.com')
            page.locator('input[placeholder*="username"]').fill('testuser')
            page.locator('button.ButtonCreateAccount').click(force=True, timeout=2000)
        except Exception as e:
            pass
            
        page.wait_for_timeout(10000)
        browser.close()

if __name__ == '__main__':
    run()
