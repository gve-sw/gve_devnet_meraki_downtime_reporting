#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (c) 2021 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

from __future__ import absolute_import, division, print_function

__author__ = "Josh Ingeniero <jingenie@cisco.com>"
__copyright__ = "Copyright (c) 2021 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


# Meraki Details
API_KEY = ""
ORG_ID = 999999

# MongoDB Details
DBNAME = ""
PASSWORD = ""
CONNECTION_STRING = f"mongodb+srv://user:{PASSWORD}@cluster0.ip/{DBNAME}?retryWrites=true&w=majority"
INTERVAL = 60

import logging
import meraki
import logging.handlers
import pymongo
import certifi
import requests
import pprint

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from collections import defaultdict
from datetime import datetime


client = pymongo.MongoClient(CONNECTION_STRING,  tlsCAFile=certifi.where())
db = client[DBNAME]
pp = pprint.PrettyPrinter(indent=2)
log_db = db['logs']
down_db = db['offline']
device_db = db['devices']

SCHEMA = {
    "timestamp": "",
    "type": "8021x_auth",
    "ssid": "",
    "gateway_device_mac": "",
    "client_mac": "",
    "last_known_client_ip": "",
    "identity": ""
}

# print(list(db['logs'].find()))

sched = BlockingScheduler()
saving = BackgroundScheduler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
dashboard = meraki.DashboardAPI(api_key=API_KEY, suppress_logging=True)


def setup_logger(name, log_file, level=logging.DEBUG):
    """To setup as many loggers as you want"""

    # handler = logging.FileHandler(log_file, mode='a')
    handler = logging.handlers.RotatingFileHandler(log_file, mode='a', maxBytes=100000000, backupCount=10)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def check_device_status():
    '''
    Function defines device statuses from meraki
    :return: response - whatever this is
    '''
    current_devices = list(device_db.find())
    pruned_response = defaultdict(dict)
    offline = defaultdict(dict)
    url = f"https://api.meraki.com/api/v1/organizations/{ORG_ID}/devices/statuses"
    payload = None
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Cisco-Meraki-API-Key": f"{API_KEY}"
    }
    response = requests.request('GET', url, headers=headers, data=payload).json()
    # response[:] = [d for d in response if d.get('authorization') != 'failure']  # Remove failed logins
    # pruned_response = [{k: v for k, v in d.items() if k == 'name' or 'mac' or 'serial' or 'networkId' or 'status' or 'lastReportedAt'} for d in response]
    pruned_response['devices'] = list()
    offline['devices'] = list()
    for item in response:
        temp = {}
        temp['serial'] = item['serial']
        temp['status'] = item['status']
        pruned_response['devices'].append(temp)
        pruned_response['timedate'] = datetime.utcnow().replace(second=0, microsecond=0)
        if item['status'] == 'offline':
            offline['devices'].append(item['serial'])
            offline['timedate'] = datetime.utcnow().replace(second=0, microsecond=0)
            device_entry = next((device for device in current_devices if device["serial"] == item['serial']), None)
            if not device_entry:
                temp_device = {}
                temp_device['status'] = 'offline'
                temp_device['serial'] = item['serial']
                temp_device['name'] = item['name']
                temp_device['networkId'] = item['networkId']
                temp_device['lastSeen'] = datetime.utcnow().replace(second=0, microsecond=0)
                device_db.insert_one(temp_device)
            elif device_entry['status'] == 'online':
                device_db.update_one(
                    {'_id': device_entry['_id']},
                    {
                        '$set': {
                            'status': 'offline',
                            'lastSeen': datetime.utcnow().replace(second=0, microsecond=0),
                            'name': item['name'],
                            'networkId': item['networkId']
                        }
                    }
                )
            elif device_entry['status'] == 'offline':
                device_db.update_one(
                    {'_id': device_entry['_id']},
                    {
                        '$set': {
                            'name': item['name'],
                            'networkId': item['networkId']
                        }
                    }
                )
        if item['status'] == 'online':
            device_entry = next((device for device in current_devices if device["serial"] == item['serial']), None)
            if not device_entry:
                pass
            elif device_entry['status'] == 'offline':
                device_db.update_one(
                    {'_id': device_entry['_id']},
                    {
                        '$set': {
                            'status': 'online',
                            'name': item['name'],
                            'networkId': item['networkId']

                        },
                        '$unset': {
                            'lastSeen': ''
                        },
                        '$push': {
                            'downtime': {
                                'from': device_entry['lastSeen'],
                                'to': datetime.utcnow().replace(second=0, microsecond=0)
                            }
                        }
                    }
                )
            elif device_entry['status'] == 'online':
                device_db.update_one(
                    {'_id': device_entry['_id']},
                    {
                        '$set': {
                            'name': item['name'],
                            'networkId': item['networkId']
                        }
                    }
                )
    return [pruned_response, offline]


def store_response(data, database):
    database.insert_one(data)


def main():
    backlogger.info("Starting Meraki Downtime Logging")
    current = check_device_status()  # Check the current data for the last 1 minute
    backlogger.debug(f"Current Payload: {current[1]}")
    store_response(current[0], log_db)  # Store new entries
    store_response(current[1], down_db)  # Store offline only


if __name__ == '__main__':
    backlogger = setup_logger('backendLog', 'app.log')  # Back end logger
    setup_logger('apscheduler', 'app.log')  # apscheduler job logs
    sched.add_job(main, trigger='interval', seconds=INTERVAL, next_run_time=datetime.utcnow(), misfire_grace_time=10)  # main thread to query meraki
    sched.start()
