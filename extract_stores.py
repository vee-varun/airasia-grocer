"""
To extract all the stores and their details
"""
import requests
from lxml import html

MAX_RETRY = 3
MAX_CONSECUTIVE_FAIL_ALLOWED = 10
FILTER_API_URL = 'https://bee.apiairasia.com/menu/v1/products-filters?type_id=1&filters=store_uuids'

REQ_HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7,pt;q=0.6,de;q=0.5',
    'Connection': 'keep-alive',
    'Host': 'bee.apiairasia.com',
    'Origin': 'https://www.airasia.com',
    'Referer': 'https://www.airasia.com/',
    'sec-ch-ua': '"Google Chrome";v="93", " Not;A Brand";v="99", "Chromium";v="93"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
    'X-CHANNEL': '1',
    'X-CLIENT-ID': '4415a5de-bb03-4cd7-b614-4b699ae83789',
    'X-DEVICE-ID': '4415a5de-bb03-4cd7-b614-4b699ae83789',
    'X-DEVICE-TYPE': 'phone',
    'X-LANG': 'en',
    'X-PLATFORM': 'WEBDESKTOP'
}

for _ in range(MAX_RETRY):
    res = requests.get(FILTER_API_URL, headers=REQ_HEADERS)
    if res.ok:
        break
else:
    raise RuntimeError(f'Unable to request the filter API URL. Status: {res.status_code}')

stores = res.json()['data'][0]['data']

stores_details = []
failed_responses = {}
consecutive_failed = 0
for store in stores:
    store_url = f'https://www.airasia.com/grocer/my/en/merchant/{store["slug"]}'
    for _ in range(MAX_RETRY):
        res = requests.get(store_url, headers=REQ_HEADERS)
        if res.ok:
            consecutive_failed = 0
            break
    else:
        failed_responses[store_url] = res.status_code
        consecutive_failed += 1
        if consecutive_failed == MAX_CONSECUTIVE_FAIL_ALLOWED:
            raise RuntimeError(
                f'Something wrong with the website. Failed to request {MAX_CONSECUTIVE_FAIL_ALLOWED} '
                f'different URLs consecutively.'
            )
        continue

    html_text = res.text
    root = html.fromstring(html_text)
    data_script_tag = "//script[contains(@id, '__NEXT_DATA__')]/text()"
    
    