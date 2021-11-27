"""
Compiles extracted store data files as per the required schema of Restaurant
and write it in a file.
Will run after extract_stores.
Pass "--A" to compile all the stores or "--N" for the new ones.'
Ex: python compile_restaurants.py --A
"""
import glob
import json
import os
import sys
from datetime import datetime

from constants import (
    COMPILED_RESTAURANTS_DIRECTORY,
    COUNTRY,
    EXTRACTED_STORES_DIRECTORY,
    SOURCE,
)

# if True then compile all the stores otherwise compile only the new ones
argv = sys.argv[1:]
err_msg = (
    'INVALID OPTIONS: Pass "--A" to compile all the stores '
    'or "--N" to compile new stores.'
)
if argv and len(argv) == 1:
    if argv[0] == '--A':
        COMPILE_ALL = True
    elif argv[0] == '--N':
        COMPILE_ALL = False
    else:
        print(err_msg)
else:
    print(err_msg)

STORE_BASE_URL = 'https://www.airasia.com/grocer/my/en/merchant/'

CURRENCY = 'MYR'  # Malaysian Ringgit
VENDOR_TYPE = 'Grocer'
NULL_KEYS = [
    'timestamp', 'source', 'country_code', 'url', 'name', 'name_with_branch',
    'latitude', 'longitude', 'address', 'chain', 'street_address',
    'postal_code', 'city', 'area', 'phone_number', 'phone_number_secondary',
    'rating', 'number_of_reviews', 'restaurant_id', 'promotion', 'newly_added',
    'allergy_notes', 'restaurant_description', 'currency', 'menu_url',
    'contact_person_name', 'open', 'live_at', 'restaurant_email', 'rank',
    'commission_per_order', 'is_free_delivery', 'total_order',
    'minimum_order_price', 'vendor_type', 'halal', 'restaurant_url',
    'pickup_enabled', 'no_of_seats', 'price_per_pax', 'price_per_pax_symbol',
    'custom_score', 'payment_method', 'address_local', 'shop_holidays',
    'transportation_direction', 'private_dining_rooms', 'private_use',
    'menu_info', 'dining_type', 'location_detail', 'website', 'local_name',
    'unmapped'
]

LIST_KEYS = [
    'opening_hours', 'cuisine_type', 'order_location',
    'fulfillment_methods', 'image_url', 'facilities'
]
ORDER_LOCATION_KEYS = [
    'latitude', 'longitude', 'distance', 'delivery_fee', 'delivery_time'
]
print('Compiling All' if COMPILE_ALL else 'Compiling New')
# make sure dir exists
os.makedirs(COMPILED_RESTAURANTS_DIRECTORY, exist_ok=True)

# getting already compiled stores
compiled_restaurants = []
compiled_restaurants_ids = []
if not COMPILE_ALL:
    compiled_restaurant_files = list(
        glob.glob(COMPILED_RESTAURANTS_DIRECTORY+'/*json')
    )
    if compiled_restaurant_files:
        # picking the previous one
        compiled_restaurant_file = sorted(compiled_restaurant_files)[-1]
        with open(compiled_restaurant_file, 'r') as f:
            compiled_restaurants.extend(
                json.load(f)
            )
        compiled_restaurants_ids.extend(
            [store['restaurant_id'] for store in compiled_restaurants]
        )


def add_blank_values(res):
    for key in NULL_KEYS:
        if key not in res:
            res[key] = None
    for key in LIST_KEYS:
        if key not in res:
            res[key] = []
    if len(res['order_location']) > 0:
        for key in ORDER_LOCATION_KEYS:
            for ol in res['order_location']:
                if key not in ol:
                    ol[key] = None


restaurants = []
store_files_path = glob.glob(EXTRACTED_STORES_DIRECTORY+'/*.json')
if store_files_path:
    total = len(store_files_path)
    done = 0
    compiled = 0
    print(f'Total store to be processed: {total}')
    for store_file_path in store_files_path:
        with open(store_file_path, 'r') as f:
            store = json.load(f)
        slug = store_file_path.split('/')[-1][:-5]
        uuid = store['uuid']
        if COMPILE_ALL or uuid not in compiled_restaurants_ids:
            store_url = f'{STORE_BASE_URL}/{slug}'
            restaurant = {
                'timestamp': store['extracted_on'],
                'source': SOURCE,
                'country_code': COUNTRY.upper(),
                'url': store_url,
                'name': store['name'],
                'latitude': float(store['lat']),
                'longitude': float(store['long']),
                'address': store['location'],
                'street_address': store.get('address_level_2'),
                'postal_code': store.get('postal_code'),
                'city': store.get('address_level_3'),
                'phone_number': store.get('phone'),
                'restaurant_id': store['uuid'],
                'currency': CURRENCY,
                'restaurant_description': store.get('description'),
                'menu_url': store_url,
                'live_at': store.get('opened_at'),
                'is_free_delivery': (
                    True if store['delivery_fee'] else False
                    if 'delivery_fee' in store else None
                ),
                'vendor_type': VENDOR_TYPE,
                'restaurant_url': 'store_url',
                'pickup_enabled': (
                    True if store['is_self_pickup'] else False
                    if 'is_self_pickup' in store else None
                ),
                'unmapped': {}
            }
            add_blank_values(restaurant)
            restaurants.append(restaurant)
            compiled += 1
        done += 1
        if done % 10 == 0 or done == total:
            print(f'Done: [{done} - {total}]')

else:
    print(f'URGENT: No extracted stores @ {EXTRACTED_STORES_DIRECTORY}')

if COMPILE_ALL:
    print(f'Compile All: Compiled {compiled} out of {total} extracted stores ')
else:
    print(f'Compile New: Compiled {compiled} newly extracted stores.')

if restaurants:
    # sorting by key
    restaurants = json.loads(json.dumps(restaurants, sort_keys=True))
    if not COMPILE_ALL:
        restaurants.extend(compiled_restaurants)
    # sorting by time extracted
    restaurants = sorted(restaurants, key=lambda k: k['timestamp'])

    myfilename = (
            datetime.now().strftime("%Y%m%d%H%M%S")
            + f"_{SOURCE.lower()}_"+COUNTRY+"_stores.json"
    )
    myfilepath = os.path.join(COMPILED_RESTAURANTS_DIRECTORY, myfilename)
    with open(myfilepath, 'w') as f:  # noqa
        f.write('[\n'+',\n'.join(['  ' + json.dumps(res) for res in restaurants]) +'\n]')

    print(f'Compiled restaurant has been kept @ "{myfilepath}"')

    if input('\nEnter y/Y to see sample restaurants: ') in ['y', 'Y']:
        print(json.dumps(restaurants[0], indent=2))
        print('='*100)
        print(json.dumps(restaurants[-1], indent=2))
