import os
from io import BytesIO
import requests
from config import *
import json
import threading
import numpy as np
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
from datetime import datetime
import httplib2
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import queue
QUEUE = queue.Queue(MAX_DOWNLOADING_THREAD)
Flags = None
# try:
# import argparse
# flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
# except ImportError:
# flags = None

# flags = "--noauth_local_webserver"
# flags.logging_level = "INFO"

SCOPES = 'https://www.googleapis.com/auth/presentations.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
# CLIENT_SECRET_FILE1 = 'client_secret1.json'
APPLICATION_NAME = 'Google Slides API Python Quickstart'

def get_credentials(secret_file):
    # home_dir = os.path.expanduser('~')
    # credential_dir = os.path.join(home_dir, '.credentials')
    credential_dir = '.credentials'
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'slides.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(secret_file, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if Flags:
            credentials = tools.run_flow(flow, store, Flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def get_service(secret_file):
    credentials = get_credentials(secret_file)
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('slides', 'v1', http=http)
    return service

def record(service):
    from config import URL, PROJECT_NAME, TO, PRESENTATION_ID, PROJECT_PATH, TODAY_PATH, YESTERDAY_PATH, IMAGE_SIZE
    if os.path.exists(PROJECT_PATH):
        print('project path exists!')
    else:
        os.mkdir(PROJECT_PATH)
    if os.path.exists(TODAY_PATH):
        print("today path exists!")
    else:
        os.mkdir(TODAY_PATH)
    presentation = service.presentations().get(
        presentationId=PRESENTATION_ID).execute()
    slides = presentation.get('slides')
    slide_list = []
    print('The presentation contains {} slides:'.format(len(slides)))
    for i, slide in enumerate(slides):
        print('- Slide #{} contains {} elements.'.format(i + 1, len(slide.get('pageElements'))))
        slide_list.append((slide, i))
    f1 = open(TODAY_PATH + '/slides.json', 'w')
    json.dump(slide_list, f1, indent=4)
    f1.close()
    return slide_list

def download_thumbnails(service, slide, i, slides_and_thumbnails, download_error):
    from config import URL, PROJECT_NAME, TO, PRESENTATION_ID, PROJECT_PATH, TODAY_PATH, YESTERDAY_PATH, IMAGE_SIZE
    print('downloading... #{} slide with id #{}'.format(i + 1, slide.get('objectId')))
    page_object_id = slide.get('objectId')
    try:
        thumbnail = service.presentations().pages().getThumbnail(
                presentationId=PRESENTATION_ID,
                pageObjectId=page_object_id,
            ).execute()
        slides_and_thumbnails.append((slide.get('objectId') + '~*~' + str(i + 1), 
                                      thumbnail.get('contentUrl'), 
                                      slide.get('pageElements')))
    except Exception as e:
        print(e)
        print('ERROR => get thumbnail url error')
    try:
        response = requests.get(thumbnail.get('contentUrl'))
    except Exception as e:
        print(e)
        print('ERROR => get url error')
    try:
        image = Image.open(BytesIO(response.content))
        image.thumbnail(IMAGE_SIZE, Image.ANTIALIAS)
        image.save(TODAY_PATH + '/' + str(slide.get('objectId')) + '.jpg')
    except Exception as e: 
        print(e)        
        download_error.append((slide, i))
        print('ERROR => download... #{} slide with id #{}'.format(i + 1, slide.get('objectId')))
    
def concurrent_download(slide_list, service, slides_and_thumbnails, download_error):
    # from config import URL, PROJECT_NAME, TO, PRESENTATION_ID, PROJECT_PATH, TODAY_PATH, YESTERDAY_PATH, IMAGE_SIZE
    for slide, i in slide_list:
        # _thread.start_new_thread(download_thumbnails, (service, slide, i, slides_and_thumbnails, download_error))
        download_thumbnails(service, slide, i, slides_and_thumbnails, download_error)
    f = open(TODAY_PATH + '/slide_id.json', 'w')
    json.dump(slides_and_thumbnails, f, indent=4)
    f.close()
    # print('=== * RETRY ERROR LIST * ===', str(download_error))
    # for slide, i in download_error:
    #     download_error.remove((slide, i))
    #     print('RE downloading... #{} slide'.format(i + 1))
    #     download_thumbnails(service, slide, i, slides_and_thumbnails, download_error)

def start_download(args):
    print("=== * START DOWNLOADING * ===")
    global Flags
    Flags = args
    slides_and_thumbnails = []
    download_error = []
    service = get_service(CLIENT_SECRET_FILE)
    slide_list = record(service)
    concurrent_download2(slide_list, service, slides_and_thumbnails, download_error)

def concurrent_download2(slide_list, service, slides_and_thumbnails, download_error):
    start_time = datetime.now()
    threads = []
    for slide, i in slide_list:
        QUEUE.put(i)
        # _thread.start_new_thread(download_thumbnails, (service, slide, i, slides_and_thumbnails, download_error))
        # download_thumbnails(service, slide, i, slides_and_thumbnails, download_error)
        # service2 = get_service(CLIENT_SECRET_FILE)
        thread = DownloadThread(slide, i, slides_and_thumbnails)
        thread.start()
        # threads.append(thread)
    QUEUE.join()
    print(len(slide_list), " slides use ", datetime.now() - start_time)

    # for thread in threads:
        # thread.join()

    f = open(TODAY_PATH + '/slide_id.json', 'w')
    json.dump(slides_and_thumbnails, f, indent=4)
    f.close()

def download_thumbnails2(slide, i, slides_and_thumbnails):
    print('downloading... #{} slide with id #{}'.format(i + 1, slide.get('objectId')))
    service = get_service(CLIENT_SECRET_FILE)
    page_object_id = slide.get('objectId')
    try:
        thumbnail = service.presentations().pages().getThumbnail(
                presentationId=PRESENTATION_ID,
                pageObjectId=page_object_id,
            ).execute()
        slides_and_thumbnails.append((slide.get('objectId') + '~*~' + str(i + 1), 
                                      thumbnail.get('contentUrl'), 
                                      slide.get('pageElements')))
    except Exception as e:
        print(e)
        print('ERROR => get thumbnail url error')
    try:
        response = requests.get(thumbnail.get('contentUrl'))
    except Exception as e:
        print(e)
        print('ERROR => get url error')
    try:
        image = Image.open(BytesIO(response.content))
        image.thumbnail(IMAGE_SIZE, Image.ANTIALIAS)
        image.save(TODAY_PATH + '/' + str(slide.get('objectId')) + '.jpg')
        print("Thread " + str(i) + " is done.")
    except Exception as e: 
        print(e)        
        # download_error.append((slide, i))
        print('ERROR => download... #{} slide with id #{}'.format(i + 1, slide.get('objectId')))
 


class DownloadThread(threading.Thread):
    def __init__(self, slide, i, slides_and_thumbnails):      
        threading.Thread.__init__(self)
        self.slide = slide
        self.slides_and_thumbnails = slides_and_thumbnails
        self.i = i

    def run(self):
        print ("Start thread:" + self.name)
        download_thumbnails2(self.slide, self.i, self.slides_and_thumbnails)
        QUEUE.get()
        QUEUE.task_done()
