"""
To extract all the stores and their details
"""
import json
from datetime import datetime, timezone
import glob

import requests
import os
from time import sleep

from constants import MAX_RETRY, REQ_HEADERS, EXTRACTED_STORES_DIRECTORY, MAX_CONSECUTIVE_FAIL_ALLOWED

EXTRACT_ALL = False  # if True then extract all the stores otherwise extract only the new ones

FILTER_API_URL = 'https://bee.apiairasia.com/menu/v1/products-filters?type_id=1&filters=store_uuids'

for _ in range(MAX_RETRY):
    print(f'Requesting: {FILTER_API_URL}')
    res = requests.get(FILTER_API_URL, headers=REQ_HEADERS)
    if res.ok:
        break
else:
    raise RuntimeError(f'Unable to request the filter API URL. Status: {res.status_code}')

stores = res.json()['data'][0]['data']

already_extracted_stores = []
for store_file_path in glob.glob(EXTRACTED_STORES_DIRECTORY+'/*.json'):
    already_extracted_stores.append(store_file_path.split('/')[-1][:-5])


failed_requests = {}
consecutive_failed = 0
for store in stores:
    slug = store["slug"]
    if EXTRACT_ALL or slug not in already_extracted_stores:
        print(slug)
        store_api_url = f'https://bee.apiairasia.com/store/v1/store/{slug}'
        for _ in range(MAX_RETRY):
            res = requests.get(store_api_url, headers=REQ_HEADERS)
            print(res.status_code)
            if res.ok:
                consecutive_failed = 0
                break
        else:
            failed_requests[store_api_url] = res.status_code
            consecutive_failed += 1
            if consecutive_failed == MAX_CONSECUTIVE_FAIL_ALLOWED:
                raise RuntimeError(
                    f'Something wrong with the website. Failed to request {MAX_CONSECUTIVE_FAIL_ALLOWED} '
                    f'different URLs consecutively. {failed_requests}'
                )
            continue

        store_data = res.json()['data']
        store_data['extracted_on'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%TZ')
        file_path = os.path.join(EXTRACTED_STORES_DIRECTORY, f'{slug}.json')
        with open(file_path, 'w') as f:
            json.dump(store_data, f, indent=2)

if failed_requests:
    print(f'Failed Requests: {failed_requests}')
