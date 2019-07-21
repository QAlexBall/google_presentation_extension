import datetime
import sys
import os
import json

# config
TODAY = datetime.date.today() #  - datetime.timedelta(days=1)
YESTERDAY = TODAY - datetime.timedelta(days=1)

URL = ""
PROJECT_NAME = ""
TO = ""

PRESENTATION_ID = ""
PROJECT_PATH = ""
TODAY_PATH = ""
YESTERDAY_PATH = ""
IMAGE_SIZE = ""

MAX_DOWNLOADING_THREAD = 3

def load_settings(settings_string):
    # setting.json
    try:
        settings = json.load(open(str(settings_string), 'r'))
        global URL, PROJECT_NAME, TO, PRESENTATION_ID, PROJECT_PATH, TODAY_PATH, YESTERDAY_PATH, IMAGE_SIZE, MAX_DOWNLOADING_THREAD
        URL = settings.get('url')
        PROJECT_NAME = settings.get('project_name')
        TO = settings.get('to')
        MAX_DOWNLOADING_THREAD = settings.get("MAX_DOWNLOADING_THREAD")

        PRESENTATION_ID = URL.split('/')[5]
        PROJECT_PATH = './history/' + str(PROJECT_NAME) + '/'
        TODAY_PATH = PROJECT_PATH + str(TODAY) + '/'
        YESTERDAY_PATH = PROJECT_PATH + str(YESTERDAY) + '/'
        IMAGE_SIZE = 1600/2, 900/2

        print(TODAY)
        print(YESTERDAY)
        print(URL)
        print(PROJECT_NAME)
        print(TO)
        print(PRESENTATION_ID)
        print(PROJECT_PATH)
        print(TODAY_PATH)
        print(YESTERDAY_PATH)
        print(IMAGE_SIZE)
        print(MAX_DOWNLOADING_THREAD)

    except Exception as e:
        print(e)
        print("[=== * please check your args * ===]")
