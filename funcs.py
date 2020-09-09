import random
import requests
import urllib.parse
from datetime import datetime
import hashlib
import json
from settings import *
import schedule
import time


class Request:
    def __init__(self):
        self.header = self.authorization()
        self.params = None
        self.URL = "http://api.responder.co.il/main/lists/"

    def authorization(self):
        nonce = hashlib.md5(str(random.randint(0, 100000000)).encode()).hexdigest()
        c_key = urllib.parse.quote('1703D64E2E953C46B2AFC8C94F6D66A4')
        c_secret = hashlib.md5(f'EE03AFEA7AB495AAF2AA70BC5FEE413E{nonce}'.encode()).hexdigest()
        u_key = urllib.parse.quote('ACFE060E3DFC09408178081FA2A33F50')
        u_secret = hashlib.md5(f'9D99D3F32110EB1163EB34EC76CC8559{nonce}'.encode()).hexdigest()
        timestamp = urllib.parse.quote(str(datetime.timestamp(datetime.now())))

        # defining a params dict for the parameters to be sent to the API
        HEADER = {
            'Authorization': f"c_key={c_key},c_secret={c_secret},u_key={u_key},u_secret={u_secret},nonce={nonce},timestamp={timestamp}"}

        return HEADER

    def getSubscribers(self):
        url = f'{self.URL}{WAITING_LIST_ID}/subscribers'
        r = requests.get(url=url, headers=self.header)
        data = r.json()
        return data

    def addSubscribers(self, subscribers):
        url = f'{self.URL}{ACTIVE_LIST_ID}/subscribers'
        r = requests.post(url=url, headers=self.header, params={'subscribers': json.dumps(subscribers)})
        data = r.json()
        return data

    def deleteSubscribers(self, subscribers):
        url = f'{self.URL}{WAITING_LIST_ID}/subscribers'
        r = requests.delete(url=url, headers=self.header, params={'subscribers': json.dumps(subscribers)})
        data = r.json()
        # TODO check if succeed
        return data


def moveSubscribers():
    new_subs = Request().getSubscribers()
    new_subs_json = []
    to_delete = []
    for sub in new_subs:
        if sub['STATUS'] == '1':
            sub_dict = {
                "NAME": sub['NAME'],
                "EMAIL": sub['EMAIL'],
                "PHONE": sub['PHONE']
            }
            new_subs_json.append(sub_dict)
        to_delete.append({"ID": sub['ID']})

    added_subs = Request().addSubscribers(new_subs_json)
    if len(new_subs_json) != len(added_subs["SUBSCRIBERS_CREATED"]) + len(added_subs["EMAILS_EXISTING"]):
        data = added_subs
        # TODO send error email
        return None
    # else:
    # deleted_subs = Request().deleteSubscribers(to_delete)
    # if len(deleted_subs["DELETED_SUBSCRIBERS"]) == len(to_delete):
    #     data = deleted_subs
    #     # TODO send error email


moveSubscribers()

schedule.every().sunday.at(MOVING_TIME).do(moveSubscribers)

while True:
    if STATUS == "ON":
        schedule.run_pending()
    time.sleep(60)

