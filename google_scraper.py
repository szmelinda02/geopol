from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import random
import pandas as pd
import pickle
import os
from typing import List
from datetime import datetime

def scroll(driver, pause_time):
    scroll_available = True
    full_height = driver.execute_script("return document.body.scrollHeight;")

    driver.execute_script("window.scrollTo(0, Math.ceil(document.body.scrollHeight));")
    time.sleep(pause_time+random.uniform(2, 1))

    full_height_after_scroll = driver.execute_script("return document.body.scrollHeight;")

    if full_height == full_height_after_scroll:

        try:
            driver.find_element(By.XPATH, "//span[text()='További találatok']").click()
            time.sleep(pause_time+random.uniform(2, 1))

        except:
            #print('No more place to scroll')
            scroll_available = False
    time.sleep(pause_time+random.uniform(2, 1))
    return scroll_available

def get_all_href(link, pausetime):
    driver = webdriver.Chrome()
    driver.maximize_window()
    driver.get(link)

    driver.find_element(By.XPATH, "//div[text()='Az összes elfogadása']").click() 

    scroll_available=True
    while scroll_available:
        scroll_available = scroll(driver,pausetime)

    hrefek = driver.find_elements(By.CLASS_NAME, "g")
    href_lst = []
    for href in hrefek:
        href_lst.append(href.find_elements(By.TAG_NAME, "a")[0].get_attribute("href"))

    return href_lst

def google_scraper(topic, topic_list: List[str], site_list: List[str]):
    folder = 'scraped_files'
    os.makedirs(folder, exist_ok=True)
    current_date = datetime.now().strftime("%Y%m%d")
    file_name = f"{topic}_{current_date}"
    temp_folder = os.path.join(folder,file_name,"raw")
    os.makedirs(temp_folder, exist_ok=True)
    results = {}
    for s in topic_list:
        for site in site_list:
            results[(s,site)] = get_all_href(f"https://www.google.com/search?q={s}+site:{site}&source=lnt&tbs=qdr:y", 1)
            with open(f'{temp_folder}/article_urls.pkl', 'wb') as fp:
                pickle.dump(results, fp)
    return file_name