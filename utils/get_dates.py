from bs4 import BeautifulSoup
import requests 
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import re


def get_euractiv_date(url):
    
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        date_str = soup.find('span', class_='ea-dateformat').text.replace('\n', '').strip()
    except:
        date_str = None
    return date_str

def get_dw_date(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    date_string = re.findall(r'\d{1,2}/\d{1,2}/\d{4}', str(soup))
    if len(date_string) > 0:
        
        return date_string[0]
    else:
        return None


def get_euronews_date(url):
    date_regex = r'\d{4}/\d{2}/\d{2}'
    
    try:
        date_str = re.findall(date_regex, url)[0].replace('/', '')
    except:
        date_str = None
    return date_str

def get_france24_date(url):
    try:
        return url.split('/')[-1][0:8]
    except:
        return None
    
def get_politico_date(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    try:
        date_str = soup.find_all('span', class_='date-time__date')[0].text.replace('\n','').replace('\t', '')
    except:
        date_str = ''
    return date_str

def format_dw_date(date_string):
    if date_string is None:
        return None
    try:
        formatted_date = datetime.strptime(date_string, '%m/%d/%Y')
    except:
        formatted_date = datetime.strptime(date_string, '%d/%m/%Y')
    return formatted_date


def format_euractiv_date(date_string):
    if date_string is None:
        return None
    try:
        formatted_date = datetime.strptime(date_string, '%m-%d-%Y')
    except:
        formatted_date = datetime.strptime(date_string, '%d-%m-%Y')
    return formatted_date

def format_politico_date(date_string):
    if len(date_string.split(',')) > 2:
        date_string = ",".join(date_string.split(',')[1:])
        
    else:
        date_string = date_string.split('-')[0].strip()
    try:
        return datetime.strptime(date_string ,'%B %d, %Y')
    except:
        return None  
    
    
def get_date_for_url(url):
    
    if 'euractiv' in url:
        date = format_euractiv_date(get_euractiv_date(url))
        return date
    elif 'dw' in url:
        date = format_dw_date(get_dw_date(url))
        return date
    elif 'euronews' in url:
        date = get_euronews_date(url)
        return date
    elif 'france24' in url:
        date = get_france24_date(url)
        return date
    elif 'politico' in url:
        date = format_politico_date(get_politico_date(url))
        return date
    return date
    
        
    
    
    
