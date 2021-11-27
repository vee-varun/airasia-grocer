"""
Extracts all the stores of AirAsia Grocer using AirAsia API
and store them in to separate json files.
This is first script that will run.
Pass "--A" to extract all the stores or "--N" for the new ones.
Ex: python extract_stores.py --A
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone

import requests
from requests import RequestException

from constants import (
    EXTRACTED_STORES_DIRECTORY,
    MAX_CONSECUTIVE_FAIL_ALLOWED,
    MAX_RETRY,
    REQ_HEADERS, EXTRACTED_PRODUCTS_DIRECTORY,
)

# if True then extract all the stores otherwise extract only the new ones
# will also help to run for the failed requests again
argv = sys.argv[1:]
err_msg = (
    'INVALID OPTIONS: Pass "--A" to extract all the stores '
    'or "--N" for the new ones.'
)
if argv and len(argv) == 1:
    if argv[0] == '--A':
        EXTRACT_ALL = True
    elif argv[0] == '--N':
        EXTRACT_ALL = False
    else:
        raise ValueError(err_msg)
else:
    raise ValueError(err_msg)


FILTER_API_URL = (
    'https://bee.apiairasia.com/menu/v1/products-filters?'
    'type_id=1&filters=store_uuids'
)
STORE_API_BASE_URL = "https://bee.apiairasia.com/store/v1/store"

# to get all the available stores on the platform
for _ in range(MAX_RETRY):
    print(f'Requesting: {FILTER_API_URL}')
    res = requests.get(FILTER_API_URL, headers=REQ_HEADERS)
    if res.ok:
        break
else:
    raise RequestException(
        f'Unable to request the filter API URL. Status: {res.status_code}'
    )

stores = res.json()['data'][0]['data']
stores = [store['slug'] for store in stores]

os.makedirs(EXTRACTED_STORES_DIRECTORY, exist_ok=True)  # make sure dir exists

if not EXTRACT_ALL:
    # will store slugs of already extracted stores
    already_extracted_stores = []
    for store_file_path in glob.glob(EXTRACTED_STORES_DIRECTORY+'/*.json'):
        already_extracted_stores.append(store_file_path.split('/')[-1][:-5])
    stores_to_be_extracted = list(set(stores) - set(already_extracted_stores))
else:
    stores_to_be_extracted = stores


if stores_to_be_extracted:
    failed_requests = {}
    consecutive_failed = 0
    done = 0
    total = len(stores_to_be_extracted)
    print(f'Stores to be extracted: {total}')
    for slug in stores_to_be_extracted:
        store_api_url = f'{STORE_API_BASE_URL}/{slug}'
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
                    f'URGENT: Something wrong with the website. '
                    f'Failed to request {MAX_CONSECUTIVE_FAIL_ALLOWED} '
                    f'different URLs consecutively. {failed_requests}'
                )
            continue

        store_data = res.json()['data']
        store_data['extracted_on'] = (
            datetime.now(timezone.utc).strftime('%Y-%m-%dT%TZ')
        )
        file_path = os.path.join(EXTRACTED_STORES_DIRECTORY, f'{slug}.json')  # noqa
        with open(file_path, 'w') as f:
            json.dump(store_data, f, indent=2)
        done += 1
        if done % 10 == 0:
            print(f'Done: [{done} - {total}]')
    print(
        f'All the extracted products have been kept '
        f'@ {EXTRACTED_PRODUCTS_DIRECTORY}'
    )
    if failed_requests:
        print("="*100)
        print(f'Failed Requests:\n{failed_requests}')
else:
    if EXTRACT_ALL:
        print('URGENT: No stores found in the filter API.')
    else:
        print('No new store found.')


