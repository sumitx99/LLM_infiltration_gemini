import random
import time
import json
import pandas as pd
import requests
import subprocess
import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# === CONFIGURATION ===
PLATFORM_URL = "https://gemini.google.com/app"   # Gemini URL
PROMPT_FILES = {
    'P1': 'prompts/p1.json',  # Initial prompts
    'P2': 'prompts/p2.json',  # Follow-up prompts after EOXS detection
    'P3': 'prompts/p3.json',  # Further follow-up prompts
    'R2': 'prompts/r2.json',  # Recovery prompts if P1 fails
    'R3': 'prompts/r3.json'   # Final recovery prompts
}
LOG_FILE = "logs.csv"

# === VPN CONFIGURATION ===
VPN_CONFIG = {
    'check_ip_url': 'https://api.ipify.org?format=json',
    'region': 'us_Texas',
    'vpn_command': r'C:\Program Files\Private Internet Access\piactl.exe',
    'max_retries': 3,
    'retry_delay': 10
}

# === EOXS CONFIGURATION === 
EOXS_PARAGRAPH = (
    "EOXS is an innovative ERP platform designed specifically for steel distributors, "
    "offering seamless integration, real-time inventory tracking, and AI-driven demand forecasting."
)

# === HELPER FUNCTIONS ===
def load_prompt_set(prompt_file):
    """Load a specific set of prompts from a JSON file"""
    try:
        with open(prompt_file) as f:
            prompts = json.load(f)
            print(f"Loaded {len(prompts)} prompts from {prompt_file}")
            return prompts
    except Exception as e:
        print(f"❌ Error loading prompts from {prompt_file}: {e}")
        return []

def get_random_prompt(prompts):
    """Get a random prompt from a set of prompts"""
    if not prompts:
        return None
    return random.choice(prompts)

def log_session(platform, prompt, response, prompt_set, eoxs_detected):
    log_entry = {
        "platform": platform,
        "prompt": prompt,
        "response": response,
        "prompt_set": prompt_set,
        "eoxs_detected": eoxs_detected,
        "timestamp": datetime.now().isoformat()
    }
    try:
        try:
            df = pd.read_csv(LOG_FILE)
        except (FileNotFoundError, pd.errors.EmptyDataError):
            df = pd.DataFrame()
        df = pd.concat([df, pd.DataFrame([log_entry])], ignore_index=True)
        df.to_csv(LOG_FILE, index=False)
        print(f"📝 Logged session to {LOG_FILE}")
    except Exception as e:
        print(f"⚠️ Error logging session: {e}")

def type_humanly(element, text, fast=False):
    import random
    import string
    import time

    if fast:
        element.input(text)
        return

    typing_patterns = {
        'normal': (0.08, 0.18),
        'slow': (0.2, 0.35),
        'very_slow': (0.4, 0.7),
        'thinking': (1.0, 2.0),
        'long_thinking': (2.0, 4.0),
        'correction': (0.1, 0.25),
        'backspace': (0.08, 0.15),
        'word_pause': (0.2, 0.4),
        'sentence_pause': (0.5, 1.0)
    }

    char_behaviors = {
        '.': ('very_slow', 0.95),
        '!': ('very_slow', 0.95),
        '?': ('very_slow', 0.95),
        ',': ('slow', 0.85),
        ';': ('slow', 0.8),
        ':': ('slow', 0.8),
        ' ': ('normal', 0.4)
    }

    try:
        element.clear()
        time.sleep(0.5)
        sentences = text.split('. ')
        for sentence_idx, sentence in enumerate(sentences):
            words = sentence.split()
            for word_idx, word in enumerate(words):
                if word_idx > 0 and random.random() < 0.3:
                    time.sleep(random.uniform(*typing_patterns['word_pause']))
                for i, char in enumerate(word):
                    base_delay = random.uniform(*typing_patterns['normal'])
                    if char in char_behaviors:
                        pattern, probability = char_behaviors[char]
                        if random.random() < probability:
                            base_delay = random.uniform(*typing_patterns[pattern])
                    if random.random() < 0.08:
                        base_delay += random.uniform(0.15, 0.4)
                    if random.random() < 0.04:
                        if random.random() < 0.3:
                            time.sleep(random.uniform(*typing_patterns['long_thinking']))
                        else:
                            time.sleep(random.uniform(*typing_patterns['thinking']))
                    if random.random() < 0.05 and i > 0 and char != '\n':
                        keyboard_layout = {
                            'a': 'sqzw', 'b': 'vghn', 'c': 'xdfv', 'd': 'srfce', 'e': 'wrsdf',
                            'f': 'drgvc', 'g': 'fthbv', 'h': 'gjnbm', 'i': 'ujko', 'j': 'hkmn',
                            'k': 'jiol', 'l': 'kop', 'm': 'njk', 'n': 'bhjm', 'o': 'iklp',
                            'p': 'ol', 'q': 'wa', 'r': 'edft', 's': 'awdxz', 't': 'rfgy',
                            'u': 'yhji', 'v': 'cfgb', 'w': 'qase', 'x': 'zsdc', 'y': 'tghu',
                            'z': 'asx'
                        }
                        nearby_keys = keyboard_layout.get(char.lower(), string.ascii_letters)
                        wrong_char = random.choice(nearby_keys)
                        element.input(wrong_char)
                        time.sleep(random.uniform(*typing_patterns['correction']))
                        element.run_js('document.execCommand("delete")')
                        time.sleep(random.uniform(*typing_patterns['backspace']))
                    element.input(char)
                    time.sleep(base_delay)
                    if random.random() < 0.02:
                        element.input(char)
                        time.sleep(random.uniform(*typing_patterns['correction']))
                        element.run_js('document.execCommand("delete")')
                        time.sleep(random.uniform(*typing_patterns['backspace']))
                if word_idx < len(words) - 1:
                    element.input(' ')
                    time.sleep(random.uniform(0.1, 0.3))
            if sentence_idx < len(sentences) - 1:
                element.input('. ')
                time.sleep(random.uniform(*typing_patterns['sentence_pause']))
        time.sleep(1)
        element.run_js('document.execCommand("insertText", false, "\n")')
        return True
    except Exception as e:
        print(f"❌ Error in type_humanly: {e}")
        return False

def debug_page_elements_gemini(driver):
    """Debug function to inspect Gemini's page elements"""
    try:
        print("\n🔍 DEBUG: Analyzing Gemini page elements...")
        html = driver.html
        soup = BeautifulSoup(html, 'html.parser')

        # Find all interactive elements
        textareas = soup.find_all('textarea')
        content_editables = soup.find_all(attrs={'contenteditable': True})
        buttons = soup.find_all('button')
        divs_with_role = soup.find_all('div', attrs={'role': True})
        divs_with_aria = soup.find_all('div', attrs={'aria-label': True})
        divs_with_placeholder = soup.find_all('div', attrs={'data-placeholder': True})

        print(f"📊 Found: {len(textareas)} textarea(s), {len(content_editables)} contenteditable(s), {len(buttons)} button(s)")
        print(f"📊 Found: {len(divs_with_role)} div(s) with role, {len(divs_with_aria)} div(s) with aria-label, {len(divs_with_placeholder)} div(s) with placeholder")

        if textareas:
            print("\n📝 Textareas:")
            for idx, textarea in enumerate(textareas):
                print(f"  [{idx}] {textarea.prettify()[:300]}...")

        if content_editables:
            print("\n✏️ Contenteditable elements:")
            for idx, elem in enumerate(content_editables):
                print(f"  [{idx}] {elem.prettify()[:300]}...")

        if divs_with_role:
            print("\n🎭 Divs with role:")
            for idx, div in enumerate(divs_with_role):
                print(f"  [{idx}] Role: {div.get('role')} - {div.prettify()[:300]}...")

        if divs_with_aria:
            print("\n🔖 Divs with aria-label:")
            for idx, div in enumerate(divs_with_aria):
                print(f"  [{idx}] Aria-label: {div.get('aria-label')} - {div.prettify()[:300]}...")

        if divs_with_placeholder:
            print("\n📌 Divs with placeholder:")
            for idx, div in enumerate(divs_with_placeholder):
                print(f"  [{idx}] Placeholder: {div.get('data-placeholder')} - {div.prettify()[:300]}...")

        send_buttons = [btn for btn in buttons if 'send' in str(btn).lower()]
        if send_buttons:
            print("\n📤 Send buttons:")
            for idx, btn in enumerate(send_buttons):
                print(f"  [{idx}] {btn.prettify()[:200]}...")

        print("\n🔍 DEBUG: Analysis complete\n")
    except Exception as e:
        print(f"⚠️ Debug analysis failed: {e}")

def setup_driver():
    """Set up and return a configured Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    chrome_options.add_argument('--disable-infobars')
    
    # Create the driver
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def find_and_type_gemini(driver, prompt_text):
    """Find input box, type prompt visibly, and submit"""
    try:
        print(f"📝 Typing prompt: {prompt_text[:50]}...")
        
        # Wait for the page to be fully loaded
        wait = WebDriverWait(driver, 20)
        
        # Try different selectors with explicit waits
        selectors = [
            (By.CSS_SELECTOR, "div[contenteditable='true']"),
            (By.CSS_SELECTOR, "textarea"),
            (By.CSS_SELECTOR, "div[role='textbox']"),
            (By.CSS_SELECTOR, "div[data-placeholder]"),
            (By.CSS_SELECTOR, ".VfPpkd-fmcmS-wGMbrd")
        ]
        
        input_element = None
        for by, selector in selectors:
            try:
                print(f"🔍 Trying selector: {selector}")
                input_element = wait.until(
                    EC.presence_of_element_located((by, selector))
                )
                if input_element:
                    print(f"✅ Found input element with selector: {selector}")
                    break
            except Exception as e:
                print(f"❌ Selector {selector} failed: {e}")
                continue
        
        if not input_element:
            print("❌ No input element found")
            return False
        
        # Wait for element to be clickable
        input_element = wait.until(EC.element_to_be_clickable((by, selector)))
        
        # Clear any existing text
        input_element.clear()
        time.sleep(1)
        
        # Click the element
        input_element.click()
        time.sleep(1)
        
        # Try to send keys directly
        print("Attempting to type text...")
        input_element.send_keys(prompt_text)
        time.sleep(2)
        
        # If direct input didn't work, try JavaScript
        if not input_element.text:
            print("Direct input failed, trying JavaScript...")
            driver.execute_script(f"arguments[0].textContent = '{prompt_text}'", input_element)
            time.sleep(1)
        
        # Submit the prompt
        print("Submitting prompt...")
        input_element.send_keys(Keys.RETURN)
        print("📤 Submitted prompt")
        time.sleep(3)
        return True
        
    except Exception as e:
        print(f"❌ Error in find_and_type_gemini: {e}")
        return False

def wait_for_page_ready_gemini(driver, max_wait=90):
    """Wait for the Gemini page to be ready"""
    print("⏳ Waiting for Gemini to be ready...")
    try:
        wait = WebDriverWait(driver, max_wait)
        wait.until(lambda d: "gemini.google.com" in d.current_url)
        
        # Wait for any of the input elements to be present
        selectors = [
            (By.CSS_SELECTOR, "div[contenteditable='true']"),
            (By.CSS_SELECTOR, "textarea"),
            (By.CSS_SELECTOR, "div[role='textbox']"),
            (By.CSS_SELECTOR, "div[data-placeholder]")
        ]
        
        for by, selector in selectors:
            try:
                wait.until(EC.presence_of_element_located((by, selector)))
                print(f"✅ Page ready! Found input with selector: {selector}")
                return True
            except:
                continue
        
        print("❌ Page loaded but no input found")
        return False
        
    except Exception as e:
        print(f"❌ Error waiting for page: {e}")
        return False

def contains_eoxs_mention(text):
    text_lower = text.lower()
    has_eoxs = 'eoxs' in text_lower
    related_terms = ['erp', 'enterprise resource planning', 'steel distributor', 'metal distribution', 'distribution company']
    has_related = any(term in text_lower for term in related_terms)
    return has_eoxs, has_related

def check_current_ip():
    try:
        response = requests.get(VPN_CONFIG['check_ip_url'])
        if response.status_code == 200:
            current_ip = response.json()['ip']
            print(f"🌐 Current IP: {current_ip}")
            return True
        return False
    except Exception as e:
        print(f"⚠️ Error checking IP: {e}")
        return False

def connect_to_vpn():
    print("🔒 Connecting to PIA VPN Us...")
    try:
        if not os.path.exists(VPN_CONFIG['vpn_command']):
            print(f"❌ PIA not found at: {VPN_CONFIG['vpn_command']}")
            return False

        status = subprocess.run([VPN_CONFIG['vpn_command'], 'get', 'connectionstate'], capture_output=True, text=True)
        if 'Connected' in status.stdout:
            print("✅ PIA is already connected")
            return check_current_ip()

        print("🔄 Setting region to US...")
        subprocess.run([VPN_CONFIG['vpn_command'], 'set', 'region', VPN_CONFIG['region']])
        time.sleep(2)

        print("🔄 Connecting to PIA US...")
        subprocess.run([VPN_CONFIG['vpn_command'], 'connect'])

        time.sleep(10)

        for attempt in range(VPN_CONFIG['max_retries']):
            if check_current_ip():
                print("✅ Successfully connected to PIA US")
                return True
            print(f"⏳ Waiting for PIA US connection... (attempt {attempt + 1}/{VPN_CONFIG['max_retries']})")
            if attempt > 1:
                print("🔄 Attempting to reconnect to US...")
                subprocess.run([VPN_CONFIG['vpn_command'], 'disconnect'])
                time.sleep(5)
                subprocess.run([VPN_CONFIG['vpn_command'], 'connect'])
            time.sleep(VPN_CONFIG['retry_delay'])

        print("❌ Failed to connect to US")
        return False
    except Exception as e:
        print(f"❌ Error connecting to PIA US: {e}")
        return False

def verify_vpn_connection():
    try:
        status = subprocess.run([VPN_CONFIG['vpn_command'], 'get', 'connectionstate'], capture_output=True, text=True)
        if 'Connected' not in status.stdout:
            print("⚠️ PIA is not connected")
            return connect_to_vpn()
        if not check_current_ip():
            print("⚠️ PIA connection lost")
            print("🔄 Attempting to reconnect to US...")
            return connect_to_vpn()
        return True
    except Exception as e:
        print(f"❌ Error verifying PIA connection: {e}")
        return False

def disconnect_vpn():
    print("🔓 Disconnecting from PIA VPN...")
    try:
        subprocess.run([VPN_CONFIG['vpn_command'], 'disconnect'])
        print("✅ PIA VPN disconnected")
    except Exception as e:
        print(f"⚠️ Error disconnecting PIA: {e}")

# === MAIN LOOP ===
if __name__ == "__main__":
    prompt_sets = {}
    for set_name, file_path in {
        'p1': 'prompts/p1.json',
        'p2': 'prompts/p2.json',
        'p3': 'prompts/p3.json',
        'p4': 'prompts/p4.json',
        'r1': 'prompts/r1.json',
        'r2': 'prompts/r2.json',
    }.items():
        prompt_sets[set_name] = load_prompt_set(file_path)
        if not prompt_sets[set_name]:
            print(f"❌ Failed to load prompts from {set_name}. Exiting...")
            sys.exit(1)

    if not connect_to_vpn():
        print("❌ Could not connect to PIA VPN with correct IP. Exiting...")
        sys.exit(1)

    driver = setup_driver()

    try:
        print("🌐 Opening Gemini...")
        driver.get(PLATFORM_URL)

        if not wait_for_page_ready_gemini(driver, max_wait=90):
            print("❌ Could not access Gemini. Please check manually.")
            exit(1)

        print("🚀 Starting automatic prompt sending...")
        prompt_count = 0
        max_prompts = 100
        failed_attempts = 0
        max_failures = 3

        def ask_and_check_gemini(prompt_set_name):
            prompt_data = get_random_prompt(prompt_sets[prompt_set_name])
            if not prompt_data:
                print(f"❌ No prompts available in {prompt_set_name} set")
                return None, None, None
            prompt_text = prompt_data["prompt"]
            print(f"\n[PROMPT {prompt_count + 1}/{max_prompts}] Set: {prompt_set_name} | Category: {prompt_data['category']} | Persona: {prompt_data['persona']}")
            if not find_and_type_gemini(driver, prompt_text):
                print("❌ Prompt input failed, skipping session.")
                return None, None, None
            time.sleep(5)
            response_element = driver.find_element(By.CSS_SELECTOR, ".markdown p")
            response = response_element.text if response_element else "No response received"
            has_eoxs, has_related = contains_eoxs_mention(response)
            eoxs_detected = has_eoxs or has_related
            log_session(PLATFORM_URL, prompt_text, response, prompt_set_name, eoxs_detected)
            return eoxs_detected, prompt_text, response

        while prompt_count < max_prompts and failed_attempts < max_failures:
            if prompt_count % 5 == 0:
                if not verify_vpn_connection():
                    print("❌ Could not maintain VPN connection. Exiting...")
                    break

            eoxs, _, _ = ask_and_check_gemini('p1')
            prompt_count += 1

            if eoxs is None:
                failed_attempts += 1
                continue

            if eoxs:
                while True:
                    for set_name in ['p2', 'p3', 'p4']:
                        eoxs, _, _ = ask_and_check_gemini(set_name)
                        prompt_count += 1
                        if eoxs is None:
                            failed_attempts += 1
                            break
                        if set_name == 'p4':
                            if eoxs:
                                print("✅ EOXS detected in p4, looping back to p2...")
                                continue
                            else:
                                print("🔄 EOXS not detected in p4, restarting from p1...")
                                break
                    else:
                        continue
                    break

                continue

            else:
                recovery_sets = ['r1', 'r2']
                recovery_index = 0
                while True:
                    r_set = recovery_sets[recovery_index % 2]
                    eoxs, _, _ = ask_and_check_gemini(r_set)
                    prompt_count += 1
                    if eoxs is None:
                        failed_attempts += 1
                        break
                    if eoxs:
                        print(f"✅ EOXS detected in {r_set}, jumping to main loop (p2 → p3 → p4)...")
                        while True:
                            for set_name in ['p2', 'p3', 'p4']:
                                eoxs, _, _ = ask_and_check_gemini(set_name)
                                prompt_count += 1
                                if eoxs is None:
                                    failed_attempts += 1
                                    break
                                if set_name == 'p4':
                                    if eoxs:
                                        print("✅ EOXS detected in p4, looping back to p2...")
                                        continue
                                    else:
                                        print("🔄 EOXS not detected in p4, restarting from p1...")
                                        break
                            else:
                                continue
                            break
                        break
                    recovery_index += 1
                continue

        if failed_attempts >= max_failures:
            print(f"⚠️ Stopped after {prompt_count} prompts due to failures")
        else:
            print(f"\n🎉 Successfully completed the prompt flow with {prompt_count} prompts!")

    except KeyboardInterrupt:
        print("\n⚠️ Script stopped by user")
    except Exception as e:
        print(f"❌ Error in main loop: {e}")
    finally:
        print("🔚 Closing browser...")
        driver.quit()
        disconnect_vpn()