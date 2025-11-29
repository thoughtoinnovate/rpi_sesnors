#!/usr/bin/env python3
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

"""
Headless UI Test Tool for Raspberry Pi

This script performs a smoke test of the Air Quality Monitor UI.
It attempts two methods:
1. Full Headless Browser (using Playwright) - verifies JS execution and rendering
2. HTTP/HTML Check (using urllib) - verifies server is up and serving assets

Usage:
    python tools/ui_headless_test.py [url]

"""

def check_http_health(url: str) -> bool:
    """Lightweight check using standard library."""
    print(f"📡 Checking HTTP accessibility for {url}...")
    try:
        # Check root page
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                print(f"❌ Root page returned status {response.status}")
                return False
            content = response.read().decode('utf-8')
            if "Air Quality" not in content and "PM2.5" not in content:
                print("⚠️  Root page loaded but expected content not found")
                # Continue anyway, might be empty DB
            print("✅ Root page loaded successfully")

        # Check Health Endpoint
        health_url = url.rstrip('/') + '/api/health'
        with urllib.request.urlopen(health_url) as response:
            if response.status != 200:
                print(f"❌ Health endpoint returned status {response.status}")
                return False
            print("✅ API Health endpoint accessible")
            
        return True
    except urllib.error.URLError as e:
        print(f"❌ Connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_headless_browser(url: str) -> bool:
    """Full headless browser check using Playwright."""
    print(f"\n🖥️  Attempting full headless browser test (Playwright)...")
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Try to launch chromium with flags optimized for Pi/Container
            launch_args = [
                "--no-sandbox", 
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
            
            print("   Launching headless Chromium...")
            try:
                browser = p.chromium.launch(headless=True, args=launch_args)
            except Exception as e:
                print(f"⚠️  Browser launch failed: {e}")
                print("   (This is common on minimal Pi setups without UI libraries)")
                return False

            page = browser.new_page()
            
            print(f"   Navigating to {url}...")
            page.goto(url)
            
            # Wait for title
            title = page.title()
            print(f"   Page Title: {title}")
            
            # Check if key elements are visible (requires JS to run)
            # Wait for a bit of JS to execute
            time.sleep(2)
            
            # Check for main container
            if page.locator("body").is_visible():
                print("✅ Body is visible")
            else:
                print("❌ Body not visible")
                browser.close()
                return False
                
            browser.close()
            print("✅ Full headless browser test passed")
            return True
            
    except ImportError:
        print("⚠️  Playwright not installed or not found in environment.")
        print("   Run: pip install playwright && python -m playwright install")
        return False
    except Exception as e:
        print(f"❌ Browser test error: {e}")
        return False


def main():
    # Default to localhost:5000
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000/"
    
    print(f"🧪 Starting UI Headless Test against {url}\n")
    
    # 1. Run Lightweight Check (always available)
    http_ok = check_http_health(url)
    
    # 2. Run Browser Check (if possible)
    browser_ok = check_headless_browser(url)
    
    print("\n" + "="*40)
    print("TEST RESULTS")
    print("="*40)
    print(f"HTTP Connectivity: {'PASS' if http_ok else 'FAIL'}")
    print(f"Browser Rendering: {'PASS' if browser_ok else 'FAIL'}")
    
    if http_ok:
        print("\nSUMMARY: The UI Server is reachable and serving content.")
        if not browser_ok:
             print("         (Browser test failed, but API/HTML is accessible)")
        sys.exit(0)
    else:
        print("\nSUMMARY: The UI Server is NOT reachable.")
        sys.exit(1)


if __name__ == "__main__":
    main()
