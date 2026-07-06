import urllib.request
import concurrent.futures

def check_proxy(proxy_str):
    parts = proxy_str.split(":")
    if len(parts) == 4:
        ip, port, user, pwd = parts
        formatted_proxy = f"http://{user}:{pwd}@{ip}:{port}"
    elif len(parts) == 2:
        ip, port = parts
        formatted_proxy = f"http://{ip}:{port}"
    else:
        return proxy_str, False

    try:
        proxy_handler = urllib.request.ProxyHandler({
            'http': formatted_proxy, 
            'https': formatted_proxy
        })
        opener = urllib.request.build_opener(proxy_handler)
        # Using a reliable fast endpoint
        req = urllib.request.Request("http://cloudflare.com/cdn-cgi/trace", headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=10) as response:
            if response.status == 200:
                return proxy_str, True
    except Exception:
        pass
    return proxy_str, False

def main():
    proxy_file = r"E:\Python Projects\Z.ai\Webshare 10 proxies.txt"
    try:
        with open(proxy_file, "r") as f:
            proxies = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading proxy file: {e}")
        return
        
    if not proxies:
        print("No proxies found in the file.")
        return

    print(f"Found {len(proxies)} proxies. Checking...\n")

    active_proxies = []
    dead_proxies = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, len(proxies))) as executor:
        futures = {executor.submit(check_proxy, proxy): proxy for proxy in proxies}
        for future in concurrent.futures.as_completed(futures):
            proxy, is_active = future.result()
            if is_active:
                print(f"[+] Active: {proxy}")
                active_proxies.append(proxy)
            else:
                print(f"[-] Dead  : {proxy}")
                dead_proxies.append(proxy)

    print("\n=== Summary ===")
    print(f"Total Proxies: {len(proxies)}")
    print(f"Active: {len(active_proxies)}")
    print(f"Dead: {len(dead_proxies)}")

if __name__ == "__main__":
    main()
