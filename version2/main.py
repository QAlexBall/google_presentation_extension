from config import *
from oauth2client import tools

import argparse



def main():
    print('=== * RUN VERSTION 0.1 * ===')
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.add_argument('-c', type=str, help='settings file', dest="settings")
    args = parser.parse_args()
    settings = args.settings
    load_settings(settings)

    from record import start_download
    from check import get_diff_list
    from send import send_to_mail
    start_download(args)
    # slide_list = get_diff_list()
    # send_to_mail(slide_list)

if __name__ == '__main__':
    main()
