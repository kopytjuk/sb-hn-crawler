import argparse
import os
import urllib.parse as up
import logging
import time

from bs4 import BeautifulSoup
import requests
from tqdm.auto import tqdm
import pandas as pd

from session import requests_retry_session

sess = requests_retry_session()

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

QUERY_URL = "https://sb-heilbronn.lmscloud.net/cgi-bin/koha/opac-search.pl?&limit=copydate%2Cst-numeric%3D-2020&sort_by=relevance"
save_path = "./pages/"

resp = sess.get(QUERY_URL)
first_page_soup = BeautifulSoup(resp.content, 'html.parser')

num_pages = int(first_page_soup.select("#top-pages > div > ul > li:nth-child(4) > a")[0].text)

logging.info("Found %d pages to crawl!"%num_pages)

start_page = 0

for i in tqdm(range(start_page, num_pages), total=num_pages):

    offset = i*20
    page_url = QUERY_URL + "&offset=%d" % offset

    resp = sess.get(page_url)
    soup = BeautifulSoup(resp.content, 'html.parser')

    tr_list = soup.select("#bookbag_form > table > tr")

    entry_list = list()

    for tr_entry in tr_list:

        entry_uri = tr_entry.find_all("a", class_="title")[0].get("href")
        entry_url = up.urljoin("https://sb-heilbronn.lmscloud.net/", entry_uri)

        entry_cover_url = None
        try:
            entry_cover_url = tr_entry.select("td:nth-child(1) > div > a > img")[0].get("src")
        except IndexError as err:
            pass

        entry_summary = None
        try:
            entry_summary = tr_entry.find_all("span", class_="results_summary summary")[0].text
        except IndexError as err:
            pass

        entry_list.append(dict(entry_url=entry_url, 
            entry_cover_url=entry_cover_url,
            entry_summary=entry_summary))

    df_page = pd.DataFrame(entry_list)
    page_path = os.path.join(save_path, "page_%08d.csv" % i)
    df_page.to_csv(page_path, index=False)
