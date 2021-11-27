"""
Extracts all the products for the extracted stores
and store the JSON response in a file.
This script will run after the extract_stores script.
Pass "--A" to extract products for all the stores or "--N" for new ones.
Ex: python extract_products.py --A
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urlencode

import requests
from requests import RequestException

from constants import (
    EXTRACTED_PRODUCTS_DIRECTORY,
    EXTRACTED_STORES_DIRECTORY,
    MAX_CONSECUTIVE_FAIL_ALLOWED,
    MAX_RETRY,
    REQ_HEADERS,
)

# weather extract product for all the stores or only for the new ones
# will also help to run for the failed requests again
argv = sys.argv[1:]
err_msg = (
    'INVALID OPTIONS: Pass "--A" to extract products for all the stores '
    'or "--N" for the new ones.'
)
if argv and len(argv) == 1:
    if argv[0] == '--A':
        EXTRACT_FOR_ALL_STORES = True
    elif argv[0] == '--N':
        EXTRACT_FOR_ALL_STORES = False
    else:
        raise ValueError(err_msg)
else:
    raise ValueError(err_msg)


PRODUCTS_API_BASE_URL = 'https://bee.apiairasia.com/menu/v1/products-aa'

# make sure dir exists
os.makedirs(EXTRACTED_PRODUCTS_DIRECTORY, exist_ok=True)

extracted_stores = []
for store_file_path in glob.glob(EXTRACTED_STORES_DIRECTORY+'/*.json'):
    extracted_stores.append(store_file_path.split('/')[-1][:-5])

if not EXTRACT_FOR_ALL_STORES:
    # stores for which products already extracted
    stores_products_extracted = []
    for store_products_file_path in glob.glob(EXTRACTED_PRODUCTS_DIRECTORY+'/*.json'):  # noqa
        stores_products_extracted.append(
            store_products_file_path.split('/')[-1][:-5]
        )

    # stores for which products to be extracted
    stores_products_to_be_extracted = list(
        set(extracted_stores) - set(stores_products_extracted)
    )
else:
    stores_products_to_be_extracted = extracted_stores

if stores_products_to_be_extracted:
    failed_requests = {}
    consecutive_failed = 0
    done = 0
    total = len(stores_products_to_be_extracted)
    print(f'No. of stores for which products are going to extract: {total}')  # noqa
    for slug in stores_products_to_be_extracted:
        try:
            store_file_path = os.path.join(
                EXTRACTED_STORES_DIRECTORY, f'{slug}.json'
            )
            with open(store_file_path, 'r') as f:
                store = json.load(f)
            params = {
                'type_id': 1,
                'store_uuids': store['uuid']
            }
            products_url = PRODUCTS_API_BASE_URL + f'?{urlencode(params)}'
            for _ in range(MAX_RETRY):
                res = requests.get(products_url, headers=REQ_HEADERS)
                if res.ok:
                    consecutive_failed = 0
                    break
            else:
                failed_requests[products_url] = res.status_code
                consecutive_failed += 1
                if consecutive_failed == MAX_CONSECUTIVE_FAIL_ALLOWED:
                    raise RequestException(
                        f'URGENT: Something wrong with the website. '
                        f'Failed to request {MAX_CONSECUTIVE_FAIL_ALLOWED} '
                        f'different URLs consecutively.\n{failed_requests}'
                    )
                continue

            products_data = {
                'extracted_on': (
                    datetime.now(timezone.utc).strftime('%Y-%m-%dT%TZ')
                ),
                'products': res.json()['data']
            }
            file_path = os.path.join(EXTRACTED_PRODUCTS_DIRECTORY, f'{slug}.json')
            with open(file_path, 'w') as f:
                json.dump(products_data, f, indent=2)
            done += 1
            if done % 10 == 0:
                print(f'Done: [{done} - {total}]')
        except Exception as err:
            raise Exception(
                f'Got Error while extracting products for {slug}. Error: {err}'
            )
    print(
        f'All the extracted stores have been kept '
        f'@ {EXTRACTED_STORES_DIRECTORY}'
    )
    if failed_requests:
        print("="*100)
        print(f'Failed Requests:\n{failed_requests}')
else:
    if EXTRACT_FOR_ALL_STORES:
        print(f'URGENT: No extracted store found in {EXTRACTED_STORES_DIRECTORY}')  # noqa
    else:
        print('No new found for products extraction.')

