#!/usr/bin/env python3

'''Get PyPi Download Stats

get-pypi-download-stats.py

Author: David Cruz (davidcruz72@gmail.com)

Python version >= 3.6

Required Python packages:
    None

Features:
    Returns the current download stats
    Command line options
    Platform independent
'''

import argparse
import json
import logging
import logging.handlers
import os
import pypistats
import requests
import signal
import sys

script_path = os.path.dirname(os.path.realpath(__file__))
slack_webhook_url_path = f'{script_path}/slack_webhook_url'
logging_level = logging.DEBUG
log_path = f'{script_path}/logs/pypi.log'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fh_formatter = logging.Formatter('%(asctime)s %(levelname)s : %(message)s')
fh = logging.handlers.RotatingFileHandler(log_path, maxBytes=25000000, backupCount=3)
fh.setLevel(logging.DEBUG)
fh.setFormatter(fh_formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch_formatter = logging.Formatter('%(message)s')
ch.setLevel(logging_level)
ch.setFormatter(ch_formatter)
logger.addHandler(ch)


def sigint_handler(signum, frame):
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('packages', type=str, nargs='*', help='Space separated list of packages to query')
    parser.add_argument('-w', '--webhook_url', metavar='', type=str, help='Webhook URL')
    return parser.parse_args()


def main():
    # Ctrl+C graceful exit
    signal.signal(signal.SIGINT, sigint_handler)

    args = parse_args()

    if os.path.exists(slack_webhook_url_path) and not args.webhook_url:
        logger.debug('Loading Slack webhook URL')
        with open(slack_webhook_url_path, 'r') as f:
            slack_webhook_url = f.read().strip()
    elif args.webhook_url:
        slack_webhook_url = args.webhook_url
    else:
        logger.debug('Prompting for Slack webhook URL')
        slack_webhook_url = input('Slack Webhook URL: ')
        logger.debug(f'Slack webhook URL file is missing, promted user.\nslack_webhook_url variable: {slack_webhook_url}')
        with open(slack_webhook_url_path, 'w') as f:
            f.write(slack_webhook_url)

    for package in args.packages:
        logger.debug(f'Requesting recent stats')
        stats = json.loads(pypistats.recent(package, format='json'))['data']
        logger.debug(f'Requesting total downloads')
        total_downloads = json.loads(pypistats.python_major(package, format='json'))['data']
        total_downloads = sum([ int(i['downloads']) for i in total_downloads ])

        try:
            logger.debug('Sending Slack message')
            slack_msg = {
                'text': f'*Download Stats for {package!r}*\nLast Day: {stats["last_day"]:,d}\nLast week: {stats["last_week"]:,d}\nLast month: {stats["last_month"]:,d}\nTotal: {total_downloads}',
                'username': 'PyPi'
            }
            requests.post(slack_webhook_url, json=slack_msg, headers={'Content-Type': 'application/json'})
        except Exception as e:
            logger.critical(f'Post to Slack failed:\n{e}')
            print(f'Post to Slack failed:\n{e}', file=sys.stderr)
            raise
        

if __name__ == '__main__':
    main()
