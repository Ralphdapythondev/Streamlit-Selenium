import os
import time
import shutil
from typing import Tuple

import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def get_chromedriver_path() -> str:
    """Return the path to the chromedriver executable."""
    return shutil.which('chromedriver')


def get_webdriver_options() -> Options:
    """Return configured Selenium WebDriver options."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    return options


def run_selenium_screenshot(url: str) -> str:
    """Run Selenium to navigate to a webpage and take a screenshot."""
    screenshot_path = os.path.join(os.getcwd(), "screenshot.png")
    options = get_webdriver_options()
    service = Service(executable_path=get_chromedriver_path())

    with webdriver.Chrome(options=options, service=service) as driver:
        try:
            driver.get(url)
            time.sleep(2)
            driver.save_screenshot(screenshot_path)
        except Exception as e:
            st.error(f"Selenium Exception: {e}")
            return None

    return screenshot_path


def main():
    st.set_page_config(page_title="Selenium Test", page_icon='🕸️', layout="wide")

    st.title('Selenium & Iframe Embedder')

    url = st.text_input("Enter the URL for Selenium to screenshot:", value="https://www.example.com")
    
    if st.button('Take Screenshot'):
        st.info("Running Selenium, please wait...")
        screenshot_path = run_selenium_screenshot(url)
        if screenshot_path:
            st.image(screenshot_path, caption="Screenshot", use_column_width=True)
        else:
            st.error("Failed to take screenshot.")

    st.markdown("---")

    embed_url = st.text_input("Enter URL to embed:", value="https://www.example.com")
    if st.button("Embed Webpage"):
        st.components.v1.iframe(src=embed_url, width=800, height=600)


if __name__ == "__main__":
    main()
