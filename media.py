import os
import urllib.parse as up
import re
import logging

from bs4 import BeautifulSoup
import requests

from session import requests_retry_session


def parse(html_string: str):
    """Parses an url and returns
    
    Args:
        url (str): media url, e.g. https://sb-heilbronn.lmscloud.net/cgi-bin/koha/opac-detail.pl?biblionumber=9281833
    
    Returns:
        dict: media description
    """

    media_dict = dict()

    soup = BeautifulSoup(html_string, 'html.parser')

    title = soup.find("h1", class_="title", property="name").contents[0].strip()
    media_dict["title"] = title

    biblionumber = soup.find("input", type="hidden", attrs={"name":"bib"}).get("value")
    media_dict["biblionumber"] = biblionumber

    cover_url_res = soup.find("img", attrs={"title": biblionumber})
    cover_url = None
    if cover_url_res is not None:
        cover_url = cover_url_res.get("src")
    
    media_dict["cover_url"] = cover_url

    try:
        author = soup.find("span", attrs={"typeof": "Person"}).find("span", property="name").text
    except:
        author = None
    media_dict["author"] = author

    regex_year = r"\S*(?P<year>(19|20)\d{2})\S*"
    year_matcher = re.compile(regex_year)

    year_release_str = soup.find_all("span", property="datePublished")[0].text
    year_release = year_matcher.search(year_release_str).group("year")
    media_dict["year_release"] = year_release

    try:
        release_edition = soup.find("span", property="bookEdition").text
    except:
        release_edition = None
    media_dict["release_edition"] = release_edition

    media_type_str = soup.find_all("img", class_="materialtype")[0].get("src")
    media_type = media_type_str.split("/")[-1][:-4]
    media_dict["media_type"] = media_type

    try:
        publisher = soup.find("span", property="publisher").find("span", property="name").text
    except:
        publisher = None
    media_dict["publisher"] = publisher
    
    try:
        regex_isbn = r"\D*(?P<isbn>\d+)\D*"
        isbm_matcher = re.compile(regex_isbn)
        isbn_str = soup.find("span", property="isbn").text
        isbn = isbm_matcher.search(isbn_str).group("isbn")
    except:
        isbn = None

    media_dict["isbn"] = isbn

    try:
        system_key = soup.find("span", class_="results_summary classification").a.text
    except:
        system_key = None
    media_dict["system_key"] = system_key

    elements = soup.select("#holdingst > tbody > tr")
    n_elements = len(elements)
    media_dict["n_elements"] = n_elements

    elements_list = list()
    for i, elem in enumerate(elements):
        elem_status = elem.find("span", class_="item-status").text.strip()
        barcode = elem.find("td", property="serialNumber").text.strip()
        location = elem.find("td", class_="location").span.span.text.strip()
        date_due = elem.find("td", class_="date_due").span.text


        elements_list.append(dict(barcode=barcode,
            elem_status=elem_status,
            location=location,
            date_due=date_due))
    
    media_dict["elements"] = elements_list

    return media_dict
