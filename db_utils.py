# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional

import os

from virus_model import VirusData
from tinydb_serialization import SerializationMiddleware, Serializer
from tinydb import TinyDB, where

virus_table_db = 'virus_data'


def is_local_run() -> bool:
    host_name = os.uname().nodename
    return 'MacBook-Air.local' in host_name


dir_path = '' if is_local_run() else '/tmp/'  # for Now
print(dir_path)


class DateTimeSerializer(Serializer):
    OBJ_CLASS = datetime  # The class this serializer handles

    def encode(self, obj):
        return obj.strftime('%Y-%m-%dT%H:%M')

    def decode(self, s):
        return datetime.strptime(s, '%Y-%m-%dT%H:%M')


def insert_date(data: VirusData):
    database = create_tinydb_connection()
    with database as db:
        table_virus_data = db.table(virus_table_db)
        table_virus_data.insert({
            'date': data.date,
            'cases': data.total_stats_cases,
            'confirmed': data.total_stats_confirmed,
            'data_list': data.data_list.__str__()
        })


def get_latest_db_virus_data() -> Optional[VirusData]:
    """return db object"""
    database = create_tinydb_connection()
    with database as db:
        table_virus_data = db.table(virus_table_db)
        res = table_virus_data.all()

        if len(res) > 0:
            last_data = res[-1]
            return VirusData(last_data['confirmed'], last_data['cases'],
                             last_data['date'], last_data['data_list'])

    return None


def get_by_date(date: datetime) -> Optional[list]:
    database = create_tinydb_connection()
    with database as db:
        table_virus_data = db.table(virus_table_db)

        query = where('date') == date
        res = table_virus_data.search(query)
        if res is None or len(res) == 0:
            return None
        res = res[0]
        virus_data = VirusData(res['confirmed'], res['cases'],
                               res['date'], res['data_list'])
        return [virus_data]


def create_tinydb_connection():
    serialization = SerializationMiddleware()
    serialization.register_serializer(DateTimeSerializer(), 'TinyDate')

    return TinyDB(f'{dir_path}db_stats_data.json', storage=serialization)
