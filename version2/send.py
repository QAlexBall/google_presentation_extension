from __future__ import print_function

import getpass
import smtplib
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import parseaddr
from PIL import Image
import socks
import sys

from config import TODAY, YESTERDAY, TO, YESTERDAY_PATH, TODAY_PATH, PROJECT_NAME


def _format_addrs(s):
    name, addr = parseaddr(s)
    return format((Header(name, 'utf-8').encode(), addr))


def send_to_mail(slide_list):
    from config import URL, PROJECT_NAME, TO, PRESENTATION_ID, PROJECT_PATH, TODAY_PATH, YESTERDAY_PATH, IMAGE_SIZE
    print("=== * SENDING MESSAGE * ===")
    # from_addr = input('From: ')
    from_addr = '?@?.com'
    print(from_addr)
    # password = getpass.getpass('Password: ')
    password = "?"
    to_addr = TO
    smtp_server = 'smtp.gmail.com'

    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = _format_addrs('All <%s>' % to_addr)
    msg['Subject'] = Header(str(PROJECT_NAME) + " daily differences check", 'utf-8').encode()
    
    if len(slide_list) == 0:
        msg.attach(MIMEText('Nothing changed today.', 'plain', 'utf-8'))
    i = 0
    for image, image_id, image_type in slide_list:
        print(image)
        yesterday_image_path = YESTERDAY_PATH + str(image) + '.jpg'
        today_image_path = TODAY_PATH + str(image) + '.jpg'
        if image_type == 'deleted':
            cid = '<%i>' % i
            file_name = 'deleted' + str(i)
            image_path = yesterday_image_path
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
                                + '<h3> DELETED : slide number is ' + str(image_id) + '</h3>' \
                                + '<img src="cid:' + str(i) + '" width="500">' \
                                + '</body></html>', 'html', 'utf-8'))
            i = i + 1

        if image_type == 'added':
            cid = '<%i>' % i
            file_name = 'added' + str(i)
            image_path = today_image_path
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
                            + '<h3> ADDED : slide number is ' + str(image_id) + '</p>'
                            + '<p><img src="cid:' + str(i) + '"width="500"></h3>' \
                            + '</body></html>', 'html', 'utf-8'))
            i = i + 1

        if image_type == 'changed':
            cid = '<%i>' % i
            file_name = 'old' + str(i)
            old_image_path = yesterday_image_path
            new_image_path = today_image_path
            old_image = open(old_image_path, 'rb')
            new_image = open(new_image_path, 'rb')


            images = map(Image.open, [old_image_path, new_image_path])
            new_im = Image.new('RGB', (1600, 450))
            x_offset = 0
            for im in images:
                new_im.paste(im, (x_offset,0))
                x_offset += 800
            new_im.save(YESTERDAY_PATH + 'test.jpg')

            # ab = ""
            # for im in images:
            #     ab = im
            #     break

            # new_im = Image.new('RGB', (800, 450))
            # new_im.paste(im,(0,0))
            # new_im.save(YESTERDAY_PATH + 'test.jpg')
            # print(YESTERDAY_PATH + 'test.jpg', total_width, max_height)
            new_image = open(YESTERDAY_PATH + 'test.jpg', 'rb')

            mime = MIMEBase(file_name, 'jpg', filename=file_name + '.jpg')
            mime.add_header('Content-Disposition', 'attachment', filename=file_name + '.jpg')
            mime.add_header('Content-ID', cid)
            mime.add_header('X-Attachment-ID', str(i))
            mime.set_payload(new_image.read())
            encoders.encode_base64(mime)
            msg.attach(mime)
            msg.attach(MIMEText('<html><body>' \
                                + '<h3> CHANGED : slide number is ' + str(image_id) + '</h3>' \
                                + '<p><img src="cid:' + str(i) + '"width="1000">', 'html', 'utf-8'))
            i = i + 1

            # cid1 = '<%i>' % i
            # file_name = 'chanded' + str(i)
            # mime = MIMEBase(file_name, 'jpg', filename=file_name + '.jpg')
            # mime.add_header('Content-Disposition', 'attachment', filename=file_name + '.jpg')
            # mime.add_header('Content-ID', cid1)
            # mime.add_header('X-Attachment-ID', str(i))
            # mime.set_payload(new_image.read())
            # encoders.encode_base64(mime)
            # msg.attach(mime)
            # old_image.close()
            # new_image.close()

            # msg.attach(MIMEText('<img src="cid:' + str(i) + '"width="500"></p>' \
            #                     + '</body></html>', 'html', 'utf-8'))
            # i = i + 1

    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", 1086)
    # socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "192.168.13.87", 11053)
    socks.wrapmodule(smtplib)
    server = smtplib.SMTP_SSL(smtp_server, 465)
    # server.set_debuglevel(1)
    server.login(from_addr, password)
    for to in to_addr:
        try:
            print('send email to..... ' + to)
            server.sendmail(from_addr, to, msg.as_string())
        except smtplib.SMTPRecipientsRefused:
            print('can\'t send to ' + to)
    server.quit()
