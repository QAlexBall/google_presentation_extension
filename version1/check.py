from __future__ import print_function
import httplib2
import os
import json
import datetime
import numpy as np

from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
import smtplib

import getpass

import requests
from PIL import Image
from io import BytesIO

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import socks


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/presentations.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Slides API Python Quickstart'


def get_credentials():

    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'slides.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def record():
    
    path = './history/' + str(today)

    if os.path.exists(path):
        print("path exists!")
    else:
        os.mkdir(path)


    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('slides', 'v1', http=http)

    presentationId = '157DvBEb2RNCLudQEqIMxH6Gd_IdJenTSPSDfeh9gnvA'
    presentation = service.presentations().get(
        presentationId=presentationId).execute()
    slides = presentation.get('slides')

    slide_list = []
    slides_and_thumbnails = []
    print ('The presentation contains {} slides:'.format(len(slides)))
    for i, slide in enumerate(slides):
        print(slide)
        slide_list.append(slide)
        print('- Slide #{} contains {} elements.'.format(i + 1, len(slide.get('pageElements'))))
        pageObjectId = slide.get('objectId')
        thumbnail = service.presentations().pages().getThumbnail(
            presentationId=presentationId,
            pageObjectId=str(pageObjectId),
        ).execute()
        slides_and_thumbnails.append((slide.get('objectId'), thumbnail.get('contentUrl'), slide.get('pageElements'), ))
        respnose = requests.get(thumbnail.get('contentUrl'))
        image = Image.open(BytesIO(respnose.content))
        image.save(path + '/' + str(slide.get('objectId')) + '.jpg')

    f = open(path + '/slide_id' + '.json', 'w')
    json.dump(slides_and_thumbnails, f, indent=4)
    f.close()
    # save slide complete infomation
    f1 = open(path + '/slides.json', 'w')
    json.dump(slide_list, f1, indent=4)
    f1.close()

def check():

    yesterday_record = open('./history/' + str(yesterday) + '/slide_id' + '.json', 'r')
    today_record = open('./history/' + str(today) + '/slide_id' + '.json', 'r')

    yesterday_detail = json.load(yesterday_record)
    today_detail = json.load(today_record)

    yesterday_id = list(np.array(yesterday_detail)[: , 0])
    today_id = list(np.array(today_detail)[: , 0])
    
    # deteted slides
    deteted_slides = []
    yesterday_remove_id = []
    for i in range(len(yesterday_id)):
        if yesterday_id[i] not in today_id:
            deteted_slides.append(yesterday_detail[i][0])
            yesterday_remove_id.append(i)
    for id in yesterday_id:
        if id in yesterday_remove_id:
            yesterday_id.remove(id)

    # added slides
    added_slides = []
    today_remove_id = []
    for i in range(len(today_id)):
        if today_id[i] not in yesterday_id:
            added_slides.append(today_detail[i][0])
            today_remove_id.append(i)
    for id in today_id:
        if id in today_remove_id:
            today_id.remove(id)

    # changed slides
    changed_slides = []
    for i in range(len(today_id)):
        if today_id[i] in yesterday_id:
            for j in range(len(yesterday_id)): # find index of yesterday_id == today_id
                if yesterday_id[j] == today_id[i]:
                    break
            if today_detail[i][2] != yesterday_detail[j][2]: # check diffrence
                changed_slides.append(today_detail[i][0])

    yesterday_record.close()
    today_record.close()
    return deteted_slides, added_slides, changed_slides


def _format_addrs(s):
    name, addr = parseaddr(s)
    return format((Header(name, 'utf-8').encode(), addr))

def send_to_mail(deleted, added, changed):

    from_addr = input('From: ')
    print(from_addr)
    password = getpass.getpass('Password: ')
    to_addr = ['example@gmail.com']
    smtp_server = ('smtp.gmail.com')

    msg = MIMEMultipart()
    msg['From'] = _format_addrs('Chris <%s>' % from_addr)
    msg['To'] = _format_addrs('All <%s>' % to_addr)
    msg['Subject'] = Header('From SMTP ...', 'utf-8').encode()
    
    i = 0
    for image in deleted:
        cid = '<%i>' % i
        file_name='deleted' + str(i)
        image_path = './history/' + str(yesterday) + '/' + str(image) + '.jpg'
        image = open(image_path, 'rb')
        mime = MIMEBase(file_name, 'jpg', filename=file_name + '.jpg')
        mime.add_header('Content-Disposition', 'attachment', filename=file_name + '.jpg')
        mime.add_header('Content-ID', cid)
        mime.add_header('X-Attachment-ID', str(i))
        mime.set_payload(image.read())
        encoders.encode_base64(mime)
        msg.attach(mime)
        image.close()
        msg.attach(MIMEText('<html><body>' \
            + '<p> deleted! </p>' \
	        + '<img src="cid:' + str(i) + '" width="500">' \
	        + '</body></html>', 'html', 'utf-8'))
        i = i + 1
    
    for image in added:
        cid = '<%i>' % i
        file_name='added' + str(i)
        image_path = './history/' + str(today) + '/' + str(image) + '.jpg'
        image = open(image_path, 'rb')
        mime = MIMEBase(file_name, 'jpg', filename=file_name + '.jpg')
        mime.add_header('Content-Disposition', 'attachment', filename=file_name + '.jpg')
        mime.add_header('Content-ID', cid)
        mime.add_header('X-Attachment-ID', str(i))
        mime.set_payload(image.read())
        encoders.encode_base64(mime)
        msg.attach(mime)
        image.close()
    
        msg.attach(MIMEText('<html><body>' \
            + '<p> added! </p>'
	        + '<p><img src="cid:' + str(i) + '"width="500"></p>' \
	        + '</body></html>', 'html', 'utf-8'))
        i = i + 1

    for image in changed:
        cid = '<%i>' % i
        file_name='old' + str(i)
        old_image_path = './history/' + str(yesterday) + '/' + str(image) + '.jpg'
        new_image_path = './history/' + str(today) + '/' + str(image) + '.jpg'
        old_image = open(old_image_path, 'rb')
        new_image = open(new_image_path, 'rb')
        mime = MIMEBase(file_name, 'jpg', filename=file_name + '.jpg')
        mime.add_header('Content-Disposition', 'attachment', filename=file_name + '.jpg')
        mime.add_header('Content-ID', cid)
        mime.add_header('X-Attachment-ID', str(i))
        mime.set_payload(old_image.read())
        encoders.encode_base64(mime)
        msg.attach(mime)
        msg.attach(MIMEText('<html><body>' \
            + '<p> old presentation </p>' \
	        + '<p><img src="cid:' + str(i) + '"width="500">', 'html', 'utf-8'))

        i = i + 1
        cid1= '<%i>' %i
        file_name='chanded' + str(i)
        mime = MIMEBase(file_name, 'jpg', filename=file_name + '.jpg')
        mime.add_header('Content-Disposition', 'attachment', filename=file_name + '.jpg')
        mime.add_header('Content-ID', cid1)
        mime.add_header('X-Attachment-ID', str(i))
        mime.set_payload(new_image.read())
        encoders.encode_base64(mime)
        msg.attach(mime)
        old_image.close()
        new_image.close()

        msg.attach(MIMEText('<img src="cid:' + str(i) + '"width="500"></p>' \
	        + '</body></html>', 'html', 'utf-8'))
        i = i + 1
 
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "0.0.0.0", 0000)
    socks.wrapmodule(smtplib)
    server = smtplib.SMTP_SSL(smtp_server, 465)
    server.set_debuglevel(1)
    server.login(from_addr, password)
    server.sendmail(from_addr, to_addr, msg.as_string())
    server.quit()

if __name__ == '__main__':

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days = 1)
    record()

    deleted, added, changed = [], [], []
    deleted, added, changed = check()
    print(deleted, added, changed)
    send_to_mail(deleted, added, changed)
