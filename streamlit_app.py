import os
import re
import time
import shutil
import subprocess
from datetime import datetime
from typing import List, Tuple

import pandas as pd
import requests
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# Include the get_public_ip and get_proxy_ip functions

def get_public_ip() -> dict:
    """Get the public IP address and geolocation information of the server."""
    try:
        response = requests.get("https://ipinfo.io/json")
        if response.status_code == 200:
            return response.json()
        else:
            return {"ip": "Unavailable", "country": "Unavailable"}
    except Exception as e:
        return {"ip": "Error", "country": str(e)}

def get_proxy_ip(proxy: str, socksStr: str) -> dict:
    """Get the IP address and geolocation information when using a proxy."""
    proxies = {
        "http": f"{socksStr}://{proxy}",
        "https": f"{socksStr}://{proxy}",
    }
    try:
        response = requests.get("https://ipinfo.io/json", proxies=proxies)
        if response.status_code == 200:
            return response.json()
        else:
            return {"ip": "Unavailable", "country": "Unavailable"}
    except Exception as e:
        return {"ip": "Error", "country": str(e)}

# Add IP information display to the Streamlit app

if __name__ == "__main__":
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

    st.set_page_config(page_title="Selenium Test", page_icon='🕸️', layout="wide", initial_sidebar_state='collapsed')

    screenshot_dir = create_screenshot_dir()

    left, middle, right = st.columns([2, 11, 1], gap="small")

    with middle:
        st.title('Streamlit Cloud Scraper 🕸️')
        st.markdown('''This app allows you to take screenshots of web pages, extract contact information, view and download scraped text, and download the screenshots.''')

        # Display public IP information
        public_ip_info = get_public_ip()
        st.info(f"Server Public IP: {public_ip_info['ip']} (Country: {public_ip_info['country']})", icon="🌐")

        if st.session_state.proxy:
            proxy_ip_info = get_proxy_ip(st.session_state.proxy, 'socks5' if st.session_state.socks5 else 'socks4')
            st.info(f"Proxy IP: {proxy_ip_info['ip']} (Country: {proxy_ip_info['country']})", icon="🔄")

        # Input field for the user to enter a URL
        url = st.text_input("Enter the URL of the website you want to screenshot:", value="https://www.unibet.fr/sport/hub/euro-2024")

        middle_left, middle_right = st.columns([9, 10], gap="medium")

        with middle_left:
            st.header('Proxy')
            st.session_state.useproxy = st.toggle(label='Enable proxy to bypass geoip blocking', value=True, disabled=False)

            if st.session_state.useproxy:
                socks5 = st.toggle(label='Use Socks5 proxy', value=True, disabled=False)

                if socks5 != st.session_state.socks5:
                    st.session_state.socks5 = socks5
                    st.session_state.proxy = None
                    st.session_state.proxies = None
                    st.session_state.df = None

                if st.session_state.socks5:
                    # Gather and use socks5 proxies
                    if st.button(label='Refresh proxies from free Socks5 list'):
                        success, proxies = get_mtproto_socks5()
                        if not success:
                            st.error(f"No socks5 proxies found", icon='🔥')
                            st.error(proxies, icon='🔥')
                            st.session_state.df = None
                        else:
                            if not proxies.empty:
                                countries = sorted(proxies['country'].unique().tolist())
                                st.session_state.df = proxies.copy()
                                st.session_state.countries = countries
                            else:
                                st.session_state.df = None
                                st.session_state.countries = None
                else:
                    # Gather and use socks4 proxies
                    if st.button(label='Refresh proxies from free Socks4 list'):
                        success, proxies = get_proxyscrape_socks4(country='all', protocol='socks4')
                        if not success:
                            st.error(f"No socks4 proxies found", icon='🔥')
                            st.error(proxies, icon='🔥')
                            st.session_state.df = None
                        else:
                            if not proxies.empty:
                                countries = sorted(proxies['ip_data.countryCode'].unique().tolist())
                                st.session_state.df = proxies.copy()
                                st.session_state.countries = countries
                            else:
                                st.session_state.df = None
                                st.session_state.countries = None

                if st.session_state.countries is not None:
                    # Limit countries to a set of allowed countries
                    allowed_countries = ['FR', 'GB', 'DE', 'ES', 'CH', 'US']
                    st.session_state.countries = [country for country in st.session_state.countries if country in allowed_countries]

                if st.session_state.df is not None and st.session_state.countries is not None:
                    selected_country = st.selectbox(label='Select a country', options=st.session_state.countries)
                    selected_country_flag = get_flag(selected_country)
                    st.info(f'Selected Country: {selected_country} {selected_country_flag}', icon='🌍')

                    if st.session_state.socks5:
                        selected_country_proxies = st.session_state.df[st.session_state.df['country'] == selected_country]
                    else:
                        selected_country_proxies = st.session_state.df[st.session_state.df['ip_data.countryCode'] == selected_country]

                    st.session_state.proxies = set(selected_country_proxies[['ip', 'port']].apply(lambda x: f"{x.iloc[0]}:{x.iloc[1]}", axis=1).tolist())

                    if st.session_state.proxies:
                        st.session_state.proxy = st.selectbox(label='Select a proxy from the list', options=st.session_state.proxies, index=0)
                        st.info(body=f'{st.session_state.proxy} {get_flag(selected_country)}', icon='😎')
            else:
                st.session_state.proxy = None
                st.session_state.proxies = None
                st.session_state.df = None
                st.info('Proxy is disabled', icon='🔒')

        with middle_right:
            st.header('Versions')
            st.text('This is only for debugging purposes.\n'
                    'Checking versions installed in environment:\n\n'
                    f'- Python:        {get_python_version()}\n'
                    f'- Streamlit:     {st.__version__}\n'
                    f'- Selenium:      {webdriver.__version__}\n'
                    f'- Chromedriver:  {get_chromedriver_version()}\n'
                    f'- Chromium:      {get_chromium_version()}')

        st.markdown('---')

        if st.button('Start Selenium run and take screenshot'):
            st.info(f'Selected Proxy: {st.session_state.proxy}', icon='☢️')

            if st.session_state.useproxy:
                socksStr = 'socks5' if st.session_state.socks5 else 'socks4'
                st.info(f'Selected Socks: {socksStr}', icon='🧦')
            else:
                socksStr = None

            with st.spinner('Selenium is running, please wait...'):
                screenshot_path, contact_info, text_content = run_selenium_and_screenshot(logpath=logpath, url=url, proxy=st.session_state.proxy, socksStr=socksStr, screenshot_dir=screenshot_dir)

                if screenshot_path:
                    st.success(body='Screenshot taken successfully!', icon='🎉')
                    st.image(screenshot_path, caption="Screenshot of the webpage", use_column_width=True)

                    with open(screenshot_path, "rb") as file:
                        st.download_button(label="Download Screenshot", data=file, file_name=os.path.basename(screenshot_path), mime="image/png")

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
