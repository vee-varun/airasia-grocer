"""
Extract all the products available on the https://www.airasia.com/grocer/my/en
from API URL - https://bee.apiairasia.com/menu/v1/products-aa?type_id=1
in one go and store the JSON response in a file,
which will be further used to compile the Products data.
"""
import glob
import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode
import requests

from constants import MAX_RETRY, EXTRACTED_STORES_DIRECTORY, EXTRACTED_PRODUCTS_DIRECTORY, REQ_HEADERS, \
    MAX_CONSECUTIVE_FAIL_ALLOWED

EXTRACT_FOR_ALL_STORES = True  # weather extract product for all the stores or only for the new ones

PRODUCTS_BASE_URL = 'https://bee.apiairasia.com/menu/v1/products-aa'

extracted_stores = []
for store_file_path in glob.glob(EXTRACTED_STORES_DIRECTORY+'/*.json'):
    extracted_stores.append(store_file_path.split('/')[-1][:-5])

stores_products_extracted = os.listdir(EXTRACTED_PRODUCTS_DIRECTORY)  # stores for which products already extracted
if not EXTRACT_FOR_ALL_STORES:
    # stores for which products to be extracted
    stores_products_to_be_extracted = list(set(extracted_stores) - set(stores_products_extracted))
else:
    stores_products_to_be_extracted = extracted_stores

failed_requests = {}
consecutive_failed = 0
for slug in stores_products_to_be_extracted:
    store_file_path = os.path.join(EXTRACTED_STORES_DIRECTORY, f'{slug}.json')
    with open(store_file_path, 'r') as f:
        store = json.load(f)
    params = {
        'type_id': 1,
        'store_uuids': store['uuid']
    }
    products_url = PRODUCTS_BASE_URL + f'?{urlencode(params)}'
    for _ in range(MAX_RETRY):
        res = requests.get(products_url, headers=REQ_HEADERS)
        print(res.status_code)
        if res.ok:
            consecutive_failed = 0
            break
    else:
        failed_requests[products_url] = res.status_code
        consecutive_failed += 1
        if consecutive_failed == MAX_CONSECUTIVE_FAIL_ALLOWED:
            raise RuntimeError(
                f'Something wrong with the website. Failed to request {MAX_CONSECUTIVE_FAIL_ALLOWED} '
                f'different URLs consecutively. {failed_requests}'
            )
        continue

    products_data = {
        'extracted_on': datetime.now(timezone.utc).strftime('%Y-%m-%dT%TZ'),
        'products': res.json()['data']
    }
    file_path = os.path.join(EXTRACTED_PRODUCTS_DIRECTORY, f'{slug}.json')
    with open(file_path, 'w') as f:
        json.dump(products_data, f, indent=2)

if failed_requests:
    print(f'Failed Requests: {failed_requests}')
