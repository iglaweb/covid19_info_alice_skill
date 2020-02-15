# -*- coding: utf-8 -*-
"""Virus utils Module"""
from string import Template

import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from typing import Optional

import json

import db_utils
from virus_model import VirusData, StatsData, Region


t_total_l18n = Template('В мире погибло от коронавируса $cases человек, инфицировано $confirmed человек.')
t_country_l18n = Template('Погибло от коронавируса $cases человек, инфицировано $confirmed человек.')
total_not_found = 'Информация по общей статистике не найдена. Попробуйте позже.'
country_not_found = 'Статистика по запрашиваемой стране не найдена.'

# country localizations ru -> en
country_localizations = {
    'россия': 'russia',
    'рф': 'russia',
    'российская федерация': 'russia',
    'китай': 'china',
    'сингапур': 'singapore',
    'тайланд': 'thailand',
    'япония': 'japan',
    'корея': 'republic of korea',
    'тайвань': 'taiwan',
    'малайзия': 'malaysia',
    'вьетнам': 'vietnam',
    'ОАЭ': 'united arab emirates',
    'объединенные арабские эмираты': 'united arab emirates',
    'индия': 'india',
    'филиппины': 'philippines',
    'непал': 'nepal',
    'германия': 'germany',
    'франция': 'france',
    'италия': 'italy',
    'великобритания': 'united kingdom',
    'финляндия': 'finland',
    'бельгия': 'belgium',
    'испания': 'spain',
    'швеция': 'sweden',
    'канада': 'canada',
    'сша': 'united states of america',
    'америка': 'united states of america',
    'австралия': 'australia',
    'египет': 'egypt'
}

url_ecdc = "https://www.ecdc.europa.eu/en/geographical-distribution-2019-ncov-cases"


def num(s):
    try:
        return int(s)
    except ValueError:
        return 0


def parse_str_as_int(s: str):  # e.g. '17 385'
    return num(''.join(s.split()))


def fetch_last_modified_response() -> Optional[datetime]:
    r = requests.head(url_ecdc)
    if r.status_code >= 400:  # if error
        print('Error resolve head request')
        return None

    last_modified_header = r.headers['Last-Modified']
    date = datetime.strptime(last_modified_header, '%a, %d %b %Y %H:%M:%S GMT')
    print(date.__str__())
    return date


def resolve_web_virus_data() -> Optional[VirusData]:
    page = requests.get(url_ecdc)
    if page.status_code >= 400:
        print('Error retrieving page')
        return None

    # Create a BeautifulSoup object
    soup = BeautifulSoup(page.text, 'html.parser')

    # Pull all text from the BodyText div
    infected_table = soup.find(class_='table table-bordered table-condensed table-striped')

    total_stats_confirmed = 0
    total_stats_cases = 0

    data_stats = []
    rows = infected_table.find_all('tr')
    is_first_item = True
    for row in rows:
        if is_first_item:
            is_first_item = False
        else:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]

            if len(cols) == 0:  # header or something like this
                continue

            if cols[0] in Region.__members__:
                stats_data = StatsData(Region[cols[0]], cols[1], cols[2], cols[3])
                data_stats.append(stats_data)
                print(stats_data)
            elif cols[0].lower() == 'total':
                total_stats_confirmed = parse_str_as_int(cols[2])
                total_stats_cases = parse_str_as_int(cols[3])

    pattern = re.compile(r'CET')  # find time by CET
    so = soup(text=pattern)
    # for elem in so:
       # print(elem.parent)

    if len(so) == 0:
        return None

    date_time_str = so[0]  # contains 1 February 13:00 CET
    print(f"Date time str: {date_time_str}")

    datetime_match = re.findall(
        r"(\d{1,2}\s(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{1,2}:\d{2})",
        date_time_str)
    if len(datetime_match) == 0:
        datetime_match = re.findall(
            r"(\d{1,2}\s(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}\s\d{1,2}:\d{2})",
            date_time_str)

    for match in datetime_match:
        # print(f"Exact match: {match}")
        try:
            # 7 February 2020 8:00 #https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
            date = datetime.strptime(match, '%d %B %Y %H:%M')
        except ValueError:
            date = datetime.strptime(match, '%d %B %H:%M')  # 7 February 2020
            # raise ValueError("Incorrect data format, should be YYYY-MM-DD")

        now = datetime.now()
        date = date.replace(year=now.year)  # add year
        print(f"Exact datetime: {date}")
        return VirusData(total_stats_confirmed, total_stats_cases, date, data_stats)

    return None


def fetch_data() -> Optional[list]:
    """Return a list of all non-overlapping matches in the string."""
    data = resolve_web_virus_data()
    if data is None:
        # print("No data extracted")
        return None
    else:  # cache data
        db_data = db_utils.get_by_date(data.date)
        if db_data is None or len(db_data) == 0:
            db_utils.insert_date(data)  # insert first item
            return [data]
        else:  # insert newest
            db_last_date = db_data[-1].date
            if data.date > db_last_date:
                db_utils.insert_date(data)

            return db_data


def obtain_virus_data() -> Optional[list]:
    """Return a list of all non-overlapping matches in the string."""
    virus_data_obj = db_utils.get_latest_db_virus_data()
    virus_data = None if virus_data_obj is None else [virus_data_obj]
    if virus_data_obj is None:
        virus_data = fetch_data()
    else:
        last_modified_page_date = fetch_last_modified_response()
        if last_modified_page_date is not None:  # has modified date
            last_modified_page_date = last_modified_page_date.replace(hour=0, minute=0, second=0, microsecond=0)

            virus_date_time = virus_data_obj.date
            virus_date_time = virus_date_time.replace(hour=0, minute=0, second=0, microsecond=0)

            if last_modified_page_date > virus_date_time:  # need to update
                virus_data = fetch_data()
    return virus_data


def get_total_confirmed():
    virus_data = obtain_virus_data()
    if virus_data is not None and len(virus_data) > 0:
        rows = virus_data[0].total_stats_confirmed
        return rows
    return None


def get_total_cases():
    virus_data = obtain_virus_data()
    if virus_data is not None and len(virus_data) > 0:
        rows = virus_data[0].total_stats_cases
        return rows
    return None


def get_total_rus():
    virus_data = obtain_virus_data()
    if virus_data is not None and len(virus_data) > 0:
        cases = virus_data[0].total_stats_cases
        confirmed = virus_data[0].total_stats_confirmed
        return t_total_l18n.substitute({'cases': cases, 'confirmed': confirmed})
    return total_not_found


def find_country_by_name_rus(original_name: str):
    enum_country = country_localizations[original_name] \
        if original_name in country_localizations else original_name

    country = find_country_by_name(enum_country)
    if country is None:
        return country_not_found

    cases = country['cases']
    confirmed = country['confirmed']
    return t_country_l18n.substitute({'cases': cases, 'confirmed': confirmed})


def is_country_supported(name: str) -> bool:
    name = name.lower()
    if name in country_localizations:
        return True
    return name in country_localizations.values()


def find_country_by_name(name: str) -> Optional[dict]:
    if name.strip() == '':
        return None

    name = name.lower()  # use lower name
    virus_data = obtain_virus_data()
    print(virus_data)

    if virus_data is not None and len(virus_data) > 0:
        rows = virus_data[0].data_list

        decoded_rows = json.loads(rows)

        for row in decoded_rows:
            country = row['area'].lower()
            if country == name:
                return row

    return None
