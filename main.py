import requests
import json
import urllib.parse
import subprocess
import os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--datasets', required=False, nargs='?', default='datasets.json')
parser.add_argument('--persist', action='store_true')
parser.add_argument('--no-persist', dest='persist', action='store_false')
parser.set_defaults(persist=False)
args = parser.parse_args()

## Load the global configurations
dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'configuration.json')
f3 = open(filename,)
configs = json.load(f3)

filename = os.path.join(dirname, 'credentials.json')
f = open(filename,)
creds = json.load(f)

## TODO - form this URL from configs['myturn-server']
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
    gcs_object = 'gs://' + configs['gs-bucket-name'] + '/' + dataset['gcs-object']
    print(filename, gcs_object)

    response = s.request("GET", url)
    response.raise_for_status() # ensure we notice bad responses
    with open(filename, "w") as f_out:
        f_out.write(response.content.decode('utf-8'))
        f_out.close()
    if args.persist:
        result = subprocess.run(["gsutil", "cp", filename, gcs_object])
