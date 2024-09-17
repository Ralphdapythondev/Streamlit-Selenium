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
from bs4 import BeautifulSoup

# Additional imports
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from streamlit import components
from streamlit.runtime.scriptrunner import get_script_run_ctx
import validators
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


def extract_contact_info(html_content: str) -> dict:
    """Extract email addresses and phone numbers using regex."""
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    phone_pattern = r"\+?\d[\d\s\-]{7,}\d"

    contact_info = {
        "emails": re.findall(email_pattern, html_content),
        "phone_numbers": re.findall(phone_pattern, html_content)
    }
    return contact_info


def extract_text_content(html_content: str) -> str:
    """Extract all text from the HTML content."""
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator="\n")
    return text


def get_chromedriver_path() -> str:
    """Return the path to the chromedriver executable."""
    return shutil.which('chromedriver')


def get_webdriver_options(proxy: str = None, socks_str: str = None) -> Options:
    """Return configured Selenium WebDriver options."""
    options = Options()
    options.add_argument("--headless=new")  # Use new headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument('--ignore-certificate-errors')
    if proxy is not None and socks_str is not None:
        options.add_argument(f"--proxy-server={socks_str}://{proxy}")
    return options


def get_webdriver_service(logpath) -> Service:
    """Create and return a Selenium WebDriver service."""
    service = Service(
        executable_path=get_chromedriver_path(),
        log_output=logpath,
    )
    return service


def delete_selenium_log(logpath: str):
    """Delete the Selenium log file if it exists."""
    if os.path.exists(logpath):
        os.remove(logpath)


def show_selenium_log(logpath: str):
    """Display the contents of the Selenium log file."""
    if os.path.exists(logpath):
        with open(logpath) as f:
            content = f.read()
            st.code(body=content, language='log', line_numbers=True)
    else:
        st.error('No log file found!', icon='🔥')


def validate_and_format_url(url: str) -> str:
    """Ensure the URL is valid and starts with http:// or https://."""
    if not validators.url(url):
        return None
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url


def run_selenium_and_screenshot(logpath: str, url: str, proxy: str, socks_str: str, screenshot_dir: str) -> Tuple[str, dict, str, str]:
    """Run Selenium to navigate to a webpage, take a screenshot, and extract contact information."""
    url = validate_and_format_url(url)
    if url is None:
        error_msg = "Invalid URL entered."
        return None, None, None, error_msg

    screenshot_path = generate_screenshot_filename(url, screenshot_dir)
    options = get_webdriver_options(proxy=proxy, socks_str=socks_str)
    service = get_webdriver_service(logpath=logpath)

    try:
        with webdriver.Chrome(options=options, service=service) as driver:
            driver.get(url)
            # Wait until the body tag is loaded
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            # Take a screenshot
            driver.save_screenshot(screenshot_path)
            html_content = driver.page_source
            contact_info = extract_contact_info(html_content)
            text_content = extract_text_content(html_content)
        return screenshot_path, contact_info, text_content, None
    except Exception as e:
        error_msg = f'Selenium Exception occurred: {str(e)}'
        logger.error(error_msg)
        return None, None, None, error_msg


def get_python_version() -> str:
    """Return the current Python version."""
    try:
        version = subprocess.check_output(['python', '--version'], stderr=subprocess.STDOUT, text=True)
        return version.strip()
    except Exception as e:
        return str(e)


def get_chromium_version() -> str:
    """Return the Chromium version installed on the system."""
    try:
        version = subprocess.check_output(['chromium', '--version'], stderr=subprocess.STDOUT, text=True)
        return version.strip()
    except Exception as e:
        return str(e)


def get_chromedriver_version() -> str:
    """Return the Chromedriver version installed on the system."""
    try:
        version = subprocess.check_output(['chromedriver', '--version'], stderr=subprocess.STDOUT, text=True)
        return version.strip()
    except Exception as e:
        return str(e)


def get_flag(country_code):
    """Return the emoji flag for a given country code."""
    flags = {
        'FR': '🇫🇷',
        'GB': '🇬🇧',
        'DE': '🇩🇪',
        'ES': '🇪🇸',
        'CH': '🇨🇭',
        'US': '🇺🇸',
        # Add more countries as needed
    }
    return flags.get(country_code.upper(), '')


def main():
    # Initialize session state variables
    if "proxy" not in st.session_state:
        st.session_state.proxy = None
    if "proxies" not in st.session_state:
        st.session_state.proxies = None
    if "socks5" not in st.session_state:
        st.session_state.socks5 = False
    if "df" not in st.session_state:
        st.session_state.df = None
    if "countries" not in st.session_state:
        st.session_state.countries = None

    logpath = get_logpath()
    delete_selenium_log(logpath=logpath)

    st.set_page_config(page_title="Selenium Cloud Scraper", page_icon='🕸️', layout="wide", initial_sidebar_state='expanded')

    screenshot_dir = create_screenshot_dir()

    # Organize inputs in the sidebar
    with st.sidebar:
        st.title('Selenium Cloud Scraper 🕸️')
        st.markdown('This app allows you to take screenshots of web pages, extract contact information, and download scraped text and screenshots.')

        st.header('Input Parameters')
        url = st.text_input("Enter the URL of the website you want to screenshot:", value="https://www.example.com")

        st.header('Proxy Settings')
        st.session_state.useproxy = st.checkbox('Enable proxy to bypass geo-blocking', value=False)

        if st.session_state.useproxy:
            st.session_state.socks5 = st.checkbox('Use SOCKS5 proxy', value=True)

            if st.session_state.socks5:
                st.info('Using SOCKS5 proxy.')
                # Implement or fetch SOCKS5 proxies
                st.warning("⚠️ Proxy functionality is not implemented in this demo.")
            else:
                st.info('Using SOCKS4 proxy.')
                # Implement or fetch SOCKS4 proxies
                st.warning("⚠️ Proxy functionality is not implemented in this demo.")
            st.warning("⚠️ Be cautious when using free proxies. They may be unreliable or insecure.")
        else:
            st.session_state.proxy = None
            st.session_state.proxies = None
            st.session_state.df = None
            st.info('Proxy is disabled', icon='🔒')

        st.header('Version Information')
        st.text('''
This is for debugging purposes.
Checking versions installed in the environment:

- Python:        {}
- Streamlit:     {}
- Selenium:      {}
- Chromedriver:  {}
- Chromium:      {}
        '''.format(
            get_python_version(),
            st.__version__,
            webdriver.__version__,
            get_chromedriver_version(),
            get_chromium_version()
        ))

    st.header('Webpage Screenshot and Data Extraction')

    if st.button('Start Selenium run and take screenshot'):
        if not url:
            st.error("Please enter a valid URL.")
        else:
            st.info(f'Selected Proxy: {st.session_state.proxy}', icon='☢️')

            if st.session_state.useproxy:
                socks_str = 'socks5' if st.session_state.socks5 else 'socks4'
                st.info(f'Selected Proxy Type: {socks_str}', icon='🧦')
            else:
                socks_str = None

            with st.spinner('Selenium is running, please wait...'):
                screenshot_path, contact_info, text_content, error_msg = run_selenium_and_screenshot(
                    logpath=logpath,
                    url=url,
                    proxy=st.session_state.proxy,
                    socks_str=socks_str,
                    screenshot_dir=screenshot_dir
                )

                if error_msg:
                    st.error(error_msg)
                else:
                    if screenshot_path:
                        st.success('Screenshot taken successfully!', icon='🎉')
                        st.image(screenshot_path, caption="Screenshot of the webpage", use_column_width=True)

                        with open(screenshot_path, "rb") as file:
                            st.download_button(label="Download Screenshot", data=file.read(), file_name=os.path.basename(screenshot_path), mime="image/png")
                    else:
                        st.error('Failed to take screenshot.', icon='🔥')

                    if contact_info:
                        st.header('Extracted Contact Information')
                        if contact_info["emails"]:
                            st.subheader("Emails Found")
                            st.write(contact_info["emails"])
                        else:
                            st.write("No emails found.")

                        if contact_info["phone_numbers"]:
                            st.subheader("Phone Numbers Found")
                            st.write(contact_info["phone_numbers"])
                        else:
                            st.write("No phone numbers found.")

                    if text_content:
                        st.header("Extracted Text Content")
                        st.text_area("All Text Content", text_content, height=300)

                        st.download_button(
                            label="Download Text Content",
                            data=text_content,
                            file_name="scraped_text.txt",
                            mime="text/plain"
                        )

                    st.info('Selenium log files are shown below...', icon='⬇️')
                    show_selenium_log(logpath=logpath)
                    st.balloons()

    st.markdown("---")
    st.warning("⚠️ Please ensure you have permission to scrape the target website and comply with all local laws and regulations.")

    st.subheader('Embed a Webpage in the App')
    embed_url = st.text_input("Enter the URL to embed:", value="https://www.example.com")
    if st.button("Embed Webpage"):
        if not embed_url.startswith(("http://", "https://")) or not validators.url(embed_url):
            st.error("Please enter a valid URL starting with http:// or https://")
        else:
            try:
                response = requests.head(embed_url)
                if 'X-Frame-Options' in response.headers:
                    st.error("This webpage cannot be embedded due to its security policies.")
                else:
                    components.v1.iframe(src=embed_url, width=800, height=600)
            except Exception as e:
                st.error(f"An error occurred while trying to embed the webpage: {str(e)}")


if __name__ == "__main__":
    main()
