"""
Extract all the products available on the https://www.airasia.com/grocer/my/en
from API URL - https://bee.apiairasia.com/menu/v1/products-aa?type_id=1
in one go and store the JSON response in a file,
which will be further used to compile the Products data.
"""

API_URL = "https://bee.apiairasia.com/menu/v1/products-aa?type_id=1"

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

MAX_RETRY = 3

retry = 0
while retry < MAX_RETRY:
    res = requests.get(API_URL, headers=headers)
    if res.ok:
        break
else:
    raise RuntimeError(f'Not able to request the API URL. Status: {res.status_code}')

products = res.json()['data']
if not products:
    
