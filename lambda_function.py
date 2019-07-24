import os
import json
import requests
import urllib.parse
import re
# import boto3

from datetime import datetime
from pytz import timezone

AZURE_CLIENT_ID = os.environ.get('AZURE_CLIENT_ID')
AZURE_CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
AZURE_REFRESH_TOKEN = os.environ.get('AZURE_REFRESH_TOKEN')

BOOK_ID = os.environ.get('BOOK_ID')

AWS_TOKEN = os.environ.get('ACCESS_TOKEN')
AWS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET')
AWS_S3_BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME')

redirect_uri = 'https://login.microsoftonline.com/common/oauth2/nativeclient'
scopes = 'User.Read Files.ReadWrite.All offline_access',

# s3 = boto3.resource('s3',
#         aws_access_key_id=AWS_TOKEN,
#         aws_secret_access_key=AWS_TOKEN_SECRET,
# )

def lambda_handler(event, context):
    
    qs = urllib.parse.parse_qs(event['body-json'])
    print(qs)
    
    args = qs['text'][0].split(" ")
    
    type = ""
    spec_date = ""
    spec_time = ""
    
    for str in args:
        if re.match("entry|exit", str):
            type = str
        elif re.match("[0-9]{2}\/[0-9]{2}\/[0-9]{2}", str):
            spec_date = str
        elif re.match("[0-9]{2}:[0-9]{2}", str):
            spec_time = str
        else:
            print("")
    
    user = qs['user_name'][0]

    return update_work_sheet(type=type, spec_date=spec_date, spec_time=spec_time, user=user)


def get_access_token():

    # tokens = read_token_csv()
    # azure_refresh_token = tokens[1]

    headers = {
        'Accept' : 'application/json',
        'Content-Type' : 'application/x-www-form-urlencoded'
    }
    payload = {
        'client_id': AZURE_CLIENT_ID,
        'client_secret': AZURE_CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': AZURE_REFRESH_TOKEN,
        'redirect_uri': redirect_uri,
        'scope': scopes,
    }

    response = requests.post(
        'https://login.microsoftonline.com/common/oauth2/v2.0/token',
        headers = headers,
        data = payload
    )
    json_obj = json.loads(response.text)

    return json_obj["access_token"]


def update_work_sheet(type, spec_date=None, spec_time=None, user="someone"):

    access_token = get_access_token()

    headers = {
        'Content-Type' : 'application/json',
        'authorization' : 'Bearer ' + access_token,
    }

    JST = timezone('Asia/Tokyo')
    now = datetime.now(JST)

    if not spec_date:
        date = now.strftime("%y/%m/%d")
    else:
        date = spec_date

    if not spec_time:
        time = now.strftime("%H:%M")
    else:
        time = spec_time

    sheet_name = date[0:5].replace("/", "_")

    col = date[6:8]

    row_time = "B" 
    row_user = "C"
    if type == "exit":
        row_time = "D"
        row_user = "E"

    payload = {
        'values': [
            [time, user]
        ]
    }

    print("stating update...")
    response = requests.patch(
        'https://graph.microsoft.com/v1.0/me/drive/items/' + BOOK_ID + "/workbook/worksheets('" + sheet_name + "')/range(address='" + sheet_name + "!" + row_time + col + ":" + row_user + col + "')",
        headers = headers,
        data = json.dumps(payload)
    )
    print(response.text)
    
    message = {
        'text': '[{0}] {1} {2}'.format(type, date, time),
        'response_type': "ephemeral"
    }
    return message

# def read_token_csv():
#     body = s3.Object(AWS_S3_BUCKET_NAME, 'azure_token.csv').get()['Body'].read().decode('utf-8')
#     tokens = body.split(',')
#     return tokens

def select_work_sheet():

    access_token = get_access_token()

    headers = {
        'Content-Type' : 'application/json',
        'authorization' : 'Bearer ' + access_token,
    }

    response = requests.get(
        'https://graph.microsoft.com/v1.0/me/drive/items/' + BOOK_ID + "/workbook/worksheets('" + sheet_name + "')/usedRange",
        headers = headers,
    )
    json_obj = json.loads(response.text)['text']
    
    for date, time in json_obj:
        print(date + " " + time)
