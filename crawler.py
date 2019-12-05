import argparse
import os
import urllib.parse as up
import logging
import time
import json
import traceback
import sys

from bs4 import BeautifulSoup
import requests
from tqdm.auto import tqdm
import pandas as pd

from session import requests_retry_session
from media import parse

sess = requests_retry_session()

# Create a custom logger
logger = logging.getLogger("crawler")
logger.setLevel(logging.DEBUG)
c_handler = logging.StreamHandler()
#c_handler.setLevel(logging.DEBUG)
c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
c_handler.setFormatter(c_format)
logger.addHandler(c_handler)

QUERY_URL = "https://sb-heilbronn.lmscloud.net/cgi-bin/koha/opac-search.pl?&limit=copydate%2Cst-numeric%3D-2020&sort_by=relevance"
save_path = "./pages/"

logger.info('Starting with the first page ...')

resp = sess.get(QUERY_URL)
first_page_soup = BeautifulSoup(resp.content, 'html.parser')

num_pages = int(first_page_soup.select("#top-pages > div > ul > li:nth-child(4) > a")[0].text)

logger.info("Found %d pages to crawl!"%num_pages)

start_page = 0

for i in tqdm(range(start_page, num_pages), total=num_pages, disable=True):

    logger.info("Processing page %06d/%06d" % (i+1, num_pages))

    offset = i*20
    page_url = QUERY_URL + "&offset=%d" % offset

    resp = sess.get(page_url)
    soup = BeautifulSoup(resp.content, 'html.parser')

    tr_list = soup.select("#bookbag_form > table > tr")

    entry_list = list()

    for j, tr_entry in enumerate(tr_list):

        logger.info("Processing entry %03d/%03d" % (j+1, len(tr_list)))

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

        entry_html = sess.get(entry_url).content
        try:
            entry_data = parse(entry_html)
        except:
            print(entry_url, "failed")
            print(traceback.print_exc())

        entry_list.append(entry_data)
    
    logger.info("Saving entries to jsonl.")

    # save to jsonl
    page_path = os.path.join(save_path, "page_%08d.jsonl" % i)
    with open(page_path, 'w') as fout:
        for dic in entry_list:
            json.dump(dic, fout) 
            fout.write("\n")
