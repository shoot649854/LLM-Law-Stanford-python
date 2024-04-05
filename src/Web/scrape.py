import os
import re
import time
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

PARENT_DIR = os.path.dirname(os.getcwd()) # os.path.dirname
OUTPUT_DIR = os.path.join(PARENT_DIR, 'output')
INPUT_DIR = os.path.join(PARENT_DIR, 'intput')
DATA_DIR = os.path.join(PARENT_DIR, 'data')
ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
API_KEY = os.getenv('API_KEY')

class DataScraper:
    def __init__(self, id_column: str = 'Slug', target_id: int = 283):
        self.id_column = id_column
        self.target_id = target_id
        self.header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

    def send_request(self, url):
        logging.info(f"Sending request to {url}...")
        response = requests.get(url, headers=self.header)
        return response
    
    def extract_article_details(self, search_results):
        articles_list = []
        for result in search_results:
            title = result.find("h3").get_text()
            link = result.find("a")["href"]
            articles_list.append({"title": title, "link": link})
        return articles_list
    
    def extract_articles(self, response):
        articles_list = []
        soup = BeautifulSoup(response.content, "html.parser")
        search_results = soup.find_all("div", class_="tF2Cxc") 

        if search_results:
            logging.info("Articles found:")
            articles_list = self.extract_article_details(search_results)
        else:
            logging.info("No articles found on the page.")
        return articles_list
    
    def parse_articles(self, response, top_article_index: int):
        articles_list = []
        if response.status_code == 200:
            logging.info("Request successful. Parsing articles...")
            articles_list = self.extract_articles(response)
        else:
            logging.info(f"Failed to retrieve articles. Status code: {response.status_code}")
        return articles_list[:top_article_index]

    def google_scrape_articles(self, search_keyword: str, top_article_index: int, sleep_time: int = 3):
        time.sleep(sleep_time)
        url = f"https://google.com/search?q={search_keyword}" 
        response = self.send_request(url)
        articles_list = self.parse_articles(response, top_article_index)
        return articles_list
    
    def scrape_article_content(self, article_link: str):
        headers = self.header
        response = requests.get(article_link, headers=headers)
        if(response.status_code == 200):
            soup = BeautifulSoup(response.content, "html.parser")
            paragraphs = soup.find_all("p")
            article_content = "\n".join(p.get_text() for p in paragraphs)
        else:
            article_content = None        
        return article_content
    
    def find_author(self, article_link: str) -> str:
        headers = self.header
        response = requests.get(article_link, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            author = soup.find("meta", attrs={"name": "author"})
            if author:
                return author["content"]
        return "Not Found"
    
    def find_legal_country_region(self, article_link: str) -> str:
        headers = self.header
        response = requests.get(article_link, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            country_region_tag = soup.find("meta", attrs={"name": "country"})
            if country_region_tag:
                return country_region_tag["content"]
        return "Not Found"
    
    def process(self, search_keyword: str, top_article_index_param: int):
        articles_list = self.google_scrape_articles(search_keyword, top_article_index = top_article_index_param)
        result = []
        for item in articles_list:
            title = item['title']
            source = item['link']
            content = self.scrape_article_content(source)
            author = self.find_author(source)
            legal_country_region = self.find_legal_country_region(source)
            result.append({"title": title, "text": content, "source": source, "author": author, "legal_country_region": legal_country_region})
        return result
    
    