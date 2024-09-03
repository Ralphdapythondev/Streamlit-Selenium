import os
import re
import time
import shutil
import subprocess
from datetime import datetime
from typing import List, Tuple

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def get_logpath() -> str:
    """Ensure the directory exists and return the log file path."""
    log_dir = os.path.join(os.getcwd(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, 'selenium.log')


def create_screenshot_dir():
    """Create and return the directory for storing screenshots."""
    screenshot_dir = os.path.join(os.getcwd(), "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    return screenshot_dir


def generate_screenshot_filename(url: str, directory: str) -> str:
    """Generate a unique filename for each screenshot based on URL and timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_url = re.sub(r'\W+', '_', url)
    filename = f"{sanitized_url}_{timestamp}.png"
    return os.path.join(directory, filename)


def get_chromedriver_path() -> str:
    """Return the path to the chromedriver executable."""
    return shutil.which('chromedriver')


def get_webdriver_options(proxy: str = None, socksStr: str = None) -> Options:
    """Return configured Selenium WebDriver options."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-features=NetworkService")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument('--ignore-certificate-errors')
    if proxy is not None and socksStr is not None:
        options.add_argument(f"--proxy-server={socksStr}://{proxy}")
    return options


def get_webdriver_service(logpath) -> Service:
    """Create and return a Selenium WebDriver service."""
    service = Service(
        executable_path=get_chromedriver_path(),
        log_output=logpath,
    )
    return service


def validate_and_format_url(url: str) -> str:
    """Ensure the URL starts with http:// or https://, otherwise prepend https://."""
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def run_selenium_and_screenshot(logpath: str, url: str, proxy: str, socksStr: str, screenshot_dir: str) -> Tuple[str, dict]:
    """Run Selenium to navigate to a webpage, take a screenshot, and extract contact information."""
    url = validate_and_format_url(url)
    screenshot_path = generate_screenshot_filename(url, screenshot_dir)
    options = get_webdriver_options(proxy=proxy, socksStr=socksStr)
    service = get_webdriver_service(logpath=logpath)
    
    with webdriver.Chrome(options=options, service=service) as driver:
        try:
            driver.get(url)
            time.sleep(2)
            driver.save_screenshot(screenshot_path)
        except Exception as e:
            st.error(f"Selenium Exception occurred: {str(e)}")
            return None, None
    return screenshot_path, None  # Simplified to just return the screenshot path


def main():
    st.set_page_config(page_title="Selenium Test", page_icon='🕸️', layout="wide")

    screenshot_dir = create_screenshot_dir()
    logpath = get_logpath()
    
    st.title('Selenium on Streamlit Cloud 🕸️')
    st.markdown('This app allows you to take screenshots of web pages and embed web pages within the app.')

    url = st.text_input("Enter the URL of the website you want to screenshot:", value="https://www.unibet.fr/sport/hub/euro-2024")
    
    if st.button('Start Selenium run and take screenshot'):
        with st.spinner('Selenium is running, please wait...'):
            screenshot_path, _ = run_selenium_and_screenshot(logpath=logpath, url=url, proxy=None, socksStr=None, screenshot_dir=screenshot_dir)
            if screenshot_path:
                st.success('Screenshot taken successfully!')
                st.image(screenshot_path, caption="Screenshot of the webpage", use_column_width=True)
            else:
                st.error('Failed to take screenshot.')

    st.markdown("---")

    st.subheader('Embed a Webpage in the App')
    embed_url = st.text_input("Enter the URL to embed:", value="https://www.example.com")
    if st.button("Embed Webpage"):
        if not embed_url.startswith(("http://", "https://")):
            st.error("Please enter a valid URL starting with http:// or https://")
        else:
            st.components.v1.iframe(src=embed_url, width=800, height=600)


if __name__ == "__main__":
    main()
