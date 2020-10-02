import random
import requests
import urllib.parse
from datetime import datetime
import hashlib
import json
from settings import *
import schedule
import time
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def send_error_email(text, error_data):
    try:
        port = 465  # For SSL
        # Create a secure SSL context
        context = ssl.create_default_context()

        msg = MIMEMultipart()
        # msg['From'] = 'EMAIL_USER'
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = 'הודעה אוטומטית:דיווח על שגיאה במהלך העברת נרשמים לסדנה'

        body = f"{text}\n " \
               f"Returned data:\n" \
               f"{error_data}"

        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        final_msg = msg.as_string().encode('ascii')

        with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, final_msg)

    except Exception as e:
        logger.warning(f'Unable to send error email - {e.args}')
        exit(0)


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
        try:
            url = f'{self.URL}{WAITING_LIST_ID}/subscribers'
            r = requests.get(url=url, headers=self.header)
            data = r.json()
            return data

        except Exception as e:
            send_error_email('Fail to get subscribers', e.args)
            logger.warning(f'Unable to get subscribers - {e.args}')
            exit(0)

    def addSubscribers(self, subscribers):
        try:
            url = f'{self.URL}{ACTIVE_LIST_ID}/subscribers'
            r = requests.post(url=url, headers=self.header, params={'subscribers': json.dumps(subscribers)})
            data = r.json()
            return data

        except Exception as e:
            send_error_email('Fail to add subscribers', e.args)
            logger.warning(f'Unable to add subscribers - {e.args}')
            exit(0)

    # def deleteSubscribers(self, subscribers):
    #     try:
    #         url = f'{self.URL}{WAITING_LIST_ID}/subscribers'
    #         r = requests.delete(url=url, headers=self.header, params={'subscribers': json.dumps(subscribers)})
    #         data = r.json()
    #         return data
    #
    #     except Exception as e:
    #         send_error_email('Fail to delete subscribers', e.args)
    #         logger.warning(f'Unable to delete subscribers - {e.args}')
    #         exit(0)

    def updateSubscribers(self, subscribers):
        try:
            url = f'{self.URL}{WAITING_LIST_ID}/subscribers'
            # r = requests.delete(url=url, headers=self.header, params={'subscribers': json.dumps(subscribers)})
            r = requests.put(url=url, headers=self.header, params={'subscribers': json.dumps(subscribers)})
            data = r.json()
            return data

        except Exception as e:
            send_error_email('Fail to update subscribers', e.args)
            logger.warning(f'Unable to update subscribers - {e.args}')
            exit(0)


def moveSubscribers():
    try:
        new_subs = Request().getSubscribers()
        if len(new_subs) == 0:
            data = new_subs
            send_error_email('Subscribers list is empty.', data)
            exit(0)

        new_subs_json = []
        to_block = []
        for sub in new_subs:
            if sub['STATUS'] == '1':  # TODO check witch status is relevant
                sub_dict = {
                    "NAME": sub['NAME'],
                    "EMAIL": sub['EMAIL'],
                    "PHONE": sub['PHONE'],
                }
                new_subs_json.append(sub_dict)
                to_block.append({"IDENTIFIER": sub['ID'], "STATUS": 0, "STATUS_NUM": 1})

        added_subs = Request().addSubscribers(new_subs_json)
        if len(new_subs_json) != len(added_subs["SUBSCRIBERS_CREATED"]) + len(added_subs["EMAILS_EXISTING"]):
            data = added_subs
            send_error_email('Fail to add all subscribers.', data)
            exit(0)

        else:
            # TODO change delete to block
            blocked_subs = Request().updateSubscribers(to_block)
            if len(blocked_subs["DELETED_SUBSCRIBERS"]) != len(to_block):
                data = blocked_subs
                send_error_email('Fail to delete all subscribers.', data)
                exit(0)

    except Exception as e:
        send_error_email('Error in move subscribers', e.args)
        logger.warning(f'Unable to move subscribers - {e.args}')
        exit(0)


# moveSubscribers()

schedule.every().sunday.at(MOVING_TIME).do(moveSubscribers)

while True:
    if STATUS == "ON":
        schedule.run_pending()
    time.sleep(60)
