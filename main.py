import requests
import json
import urllib.parse
import os
import sys
import argparse
import logging
import datetime
import gspread
import csv

def update_gsheet(dataset):
    logging.info("%s", {key: dataset[key] for key in dataset.keys() & {'gsheet_id', 'gdrive_name', 'gsheet_worksheet_name'}})
    
    csvFile = dataset['filename']
    csvReader = csv.reader(open(csvFile))
    csvData = list(csvReader)

    gc = gspread.service_account(filename='google_serviceaccount_credentials.json')
    sh = gc.open_by_key(dataset['gsheet_id'])
    wsh = sh.worksheet(dataset['gsheet_worksheet_name'])
    wsh.clear()

    sh.values_update(dataset['gsheet_worksheet_name'],
                     params={'valueInputOption': 'USER_ENTERED'},
                     body={'values': csvData})

    logging.info("Read %s lines from file, parsed as %s rows.  Sheet now has %s rows.", 
                 csvReader.line_num, len(csvData), wsh.row_count)

    wsh = sh.worksheet('metadata')
    wsh.update('B1', str(datetime.datetime.today()), raw=False)

    logging.info("Updated metadata worksheet")


parser = argparse.ArgumentParser()
parser.add_argument('--datasets', required=False, nargs='?', default='datasets.json')
parser.add_argument('--persist', action='store_true')
parser.add_argument('--no-persist', dest='persist', action='store_false')
parser.set_defaults(persist=False)
args = parser.parse_args()

## Setup the logging
root = logging.getLogger()
root.setLevel(logging.DEBUG)
log_format = logging.Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
handler = logging.StreamHandler(sys.stdout)                             
handler.setLevel(logging.DEBUG)
handler.setFormatter(log_format)                                        
root.addHandler(handler)

## Load the global configurations
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'configuration.json')
f3 = open(filename,)
configs = json.load(f3)

filename = os.path.join(dirname, 'myturn_credentials.json')
f = open(filename,)
creds = json.load(f)

URL_LOGIN = 'https://' + configs['myturn-server'] + configs['myturn-login-path']
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0'

## Get session cookie
s = requests.Session()

## Login
payload = urllib.parse.urlencode(creds)
headers = {
  'User-Agent': USER_AGENT,
  'Content-Type': 'application/x-www-form-urlencoded'
}
response = s.request("POST", URL_LOGIN, headers=headers, data=payload)

f2 = open(os.path.join(dirname, args.datasets),)
datasets = json.load(f2)

for dataset in datasets:
    filename = dataset['filename']
    url = 'https://' + configs['myturn-server'] + dataset['urlpath']
    logging.info("Fetching from MyTurn: %s", filename)

    response = s.request("GET", url)
    response.raise_for_status() # ensure we notice bad responses
    with open(filename, "w") as f_out:
        f_out.write(response.content.decode('utf-8'))
        f_out.close()
    if args.persist:
        update_gsheet(dataset)
