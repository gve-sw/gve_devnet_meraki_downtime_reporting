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


__author__ = "Josh Ingeniero <jingenie@cisco.com>"
__copyright__ = "Copyright (c) 2021 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"


from flask import render_template, request
from collections import defaultdict
from app import app
from DETAILS import *
import datetime
import logging
import pprint
import pymongo
import meraki
import certifi


client = pymongo.MongoClient(CONNECTION_STRING,  tlsCAFile=certifi.where())
db = client[DBNAME]
pp = pprint.PrettyPrinter(indent=2)
log_db = db['logs']
down_db = db['offline']
device_db = db['devices']
dashboard = meraki.DashboardAPI(api_key=API_KEY, suppress_logging=True)

logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# Mode Selection
@app.route('/', methods=['GET', 'POST'])
def data():
    args = request.args
    nets = dashboard.organizations.getOrganizationNetworks(ORG_ID)
    networks = {item['id']: item for item in nets}
    now = datetime.datetime.utcnow().toordinal()
    start_date = datetime.datetime.combine(datetime.date.today().replace(day=1), datetime.datetime.min.time())
    end_date = datetime.datetime.combine(datetime.date(datetime.datetime.now().year + (datetime.datetime.now().month == 12),
                (datetime.datetime.now().month + 1 if datetime.datetime.now().month < 12 else 1), 1) - datetime.timedelta(1), datetime.datetime.max.time())

    if request.method == 'POST':
        data = request.form.to_dict()
        start_date = datetime.datetime.strptime(data['start'], '%Y-%m-%d')
        end_date = datetime.datetime.combine(datetime.datetime.strptime(data['end'], '%Y-%m-%d'), datetime.datetime.max.time())

    current_devices = list(device_db.find())
    entries = []
    for device in current_devices:
        if 'lastSeen' in device.keys():  # Still offline
            if device['lastSeen'] < start_date:
                dateTimeDifference = datetime.datetime.utcnow() - start_date
                dateTimeDifferenceInHours = dateTimeDifference.total_seconds() / 60
            else:
                dateTimeDifference = datetime.datetime.utcnow() - device['lastSeen']
                dateTimeDifferenceInHours = dateTimeDifference.total_seconds() / 60
            entry = {}
            entry = {
                'date': device['lastSeen'],
                'serial': device['serial'],
                'offline': device['lastSeen'],
                'online': 'Down',
                'downtime': round(dateTimeDifferenceInHours, 2),
                'name': device['name'],
                'network': networks[device['networkId']]['name']
            }
            entries.append(entry)
        if device['downtime']:  # Currently online
            for instance in device['downtime']:
                dateTimeDifference = instance['to'] - instance['from']
                dateTimeDifferenceInHours = dateTimeDifference.total_seconds() / 60
                entry = {}
                entry = {
                    'date': instance['from'],
                    'serial': device['serial'],
                    'offline': instance['from'],
                    'online': instance['to'],
                    'downtime': round(dateTimeDifferenceInHours, 2),
                    'name': device['name'],
                    'network': networks[device['networkId']]['name']
                }
                entries.append(entry)

    filtered = [item for item in entries if start_date < item['offline'] < end_date or item['online'] == 'Down']
    return render_template('data.html', title='Downtime Query',
                           entries=filtered, start_date=start_date.date(), end_date=end_date.date(),
                           dateString=DATESTRING)
