"""
1. Items present on the page or all items(21734), type id - 1?
2. why s3 bucket and all?
3. Vendors from items or there is any page where I can get all the listed vendors?
4. delivered-by?
5. data extracted, json?
6.  HTML or JSON files?
7. Schedule of scripts?
8. from scratch?
9. timestamp?
"""

import requests
# url = "https://bee.apiairasia.com/menu/v1/products-aa?limit=18&page=1&type_id=1&tag_carousel_uuid=fresh-express-same-day-delivery&postal_codes="
url = "https://bee.apiairasia.com/menu/v1/products-aa?multiple_category=1&alcohol=0&tag_uuid=&limit=20&page=5&type_id=1&tag_carousel_uuid=2021-malaysian-favourites&postal_codes="
url = "https://bee.apiairasia.com/menu/v1/products-aa?category_uuid=9969adfb-2062-4ba1-a3a3-866ff8c69bfa&multiple_category=1&alcohol=0&limit=20&page=1&type_id=1&postal_codes="
url = "https://bee.apiairasia.com/menu/v1/products-aa?type_id=1"

headers = {'Accept': '*/*',
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
           'X-PLATFORM': 'WEBDESKTOP'}

res = requests.get(url, headers=headers)

if res.ok:
    data = res.json()
    print(len(data['data']))
    for i in data['data']:
        print(i['name'])
else:
    print(f'Non OK reponse: {res.status}')

all_product_names = []
for i in data['data']:
    all_product_names.append(i['name'])

for i in all_products[:20]:
    print(data['store']['slug'])

for i in data['data']:
    print(i['store'])

t = 0
for tag_uuid in t_ids:
    url = f'https://bee.apiairasia.com/menu/v1/products-aa?type_id=1&category_tag_uuid={tag_uuid}'
    res = requests.get(url, headers=headers)
    if res.ok:
        data = res.json()['data']
        t += len(data)
        print(t)
        cat_data.append(data)
    else:
        print(f'Non OK response: {res.status}, {url}')

"""
Total product count
21734 - 21 Nov, Night
21089 - 22 Nov, Morning
21090 - 22 Nov, Evening
For products extraction we will use the API URL
 https://bee.apiairasia.com/menu/v1/products-aa?type_id=1

For vendor's details we will go the merchant URL which will have the JSON in the script tag
    Merchant URL - https://www.airasia.com/grocer/my/en/merchant/<slug of the vendor>
    
Merchant and Store <- Types of vendor
If store, then merchant URL redirected to below URL on the browser but not when you request through script.
Ex. - https://www.airasia.com/grocer/my/en/merchant/bright-cow

Two Cases
1. Adding
2. Updating

Can add check in case of searching and adding new restaurant, that process those slugs which already 
present in the store directory
"""

"""
RoadMap

1. A script to extract the JSON response for all the products and reate a JSON file in the local to store that data.
    https://bee.apiairasia.com/menu/v1/products-aa?type_id=1
    
2. For vendor's details we will go the merchant URL which will have the JSON in the script tag
    Merchant URL - https://www.airasia.com/grocer/my/en/merchant/<slug of the vendor>
    
3. 
"""


"https://bee.apiairasia.com/menu/v1/products-aa?store_uuids=835fe4e7-bc7f-47f3-8791-82fecc28aa35&type_id=1"
"https://bee.apiairasia.com/menu/v1/products-aa?store_category_uuids=516328bd-3959-4ea1-97ba-18099e5b4c43&limit=20&store_uuids=835fe4e7-bc7f-47f3-8791-82fecc28aa35&type_id=1"