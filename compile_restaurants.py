"""
Compile store data files as per the required schema of Restaurant
"""
import glob
import json
import os
from datetime import datetime

from constants import COMPILED_RESTAURANTS_DIRECTORY, EXTRACTED_STORES_DIRECTORY

COMPILE_ALL = False   # if True then compile all the stores otherwise compile only the new ones

STORE_BASE_URL = 'https://www.airasia.com/grocer/my/en/merchant/'

COUNTRY = 'my'  # Malaysia
CURRENCY = 'MYR'  # Malaysian Ringgit
VENDOR_TYPE = 'Grocer'
NULL_KEYS = [
    'timestamp', 'source', 'country_code', 'url', 'name', 'name_with_branch',
    'latitude', 'longitude', 'address', 'chain', 'street_address', 'postal_code',
    'city', 'area', 'phone_number', 'phone_number_secondary', 'rating', 'number_of_reviews',
    'restaurant_id', 'promotion', 'newly_added', 'allergy_notes', 'restaurant_description',
    'currency', 'menu_url', 'contact_person_name', 'open', 'live_at', 'restaurant_email', 'rank',
    'commission_per_order', 'is_free_delivery', 'total_order', 'minimum_order_price',
    'vendor_type', 'halal', 'restaurant_url', 'pickup_enabled', 'no_of_seats',
    'price_per_pax', 'price_per_pax_symbol', 'custom_score', 'payment_method', 'address_local',
    'shop_holidays', 'transportation_direction', 'private_dining_rooms', 'private_use',
    'menu_info', 'dining_type', 'location_detail', 'website', 'local_name', 'unmapped'
]

LIST_KEYS = [
    'opening_hours', 'cuisine_type', 'order_location',
    'fulfillment_methods', 'image_url', 'facilities'
]
ORDER_LOCATION_KEYS = ['latitude', 'longitude', 'distance', 'delivery_fee', 'delivery_time']

compiled_restaurants = []
compiled_restaurants_ids = []
if not COMPILE_ALL:
    # getting already compiled stores
    compiled_restaurant_files = list(glob.glob(COMPILED_RESTAURANTS_DIRECTORY+'/*txt'))
    if compiled_restaurant_files:
        compiled_restaurant_file = sorted(compiled_restaurant_files)[-1]  # picking the previous one
        with open(compiled_restaurant_file, 'r') as f:
            compiled_restaurants.extend([json.loads(item) for item in f.readlines()])
        compiled_restaurants_ids.extend([store['restaurant_id'] for store in compiled_restaurants])


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
total = 0
compiled = 0
for store_file_path in glob.glob(EXTRACTED_STORES_DIRECTORY+'/*.json'):
    with open(store_file_path, 'r') as f:
        store = json.load(f)
    slug = store_file_path.split('/')[-1][:-5]
    uuid = store['uuid']
    if COMPILE_ALL or uuid not in compiled_restaurants_ids:
        store_url = f'{STORE_BASE_URL}/{slug}'
        restaurant = {
            'timestamp': store['extracted_on'],
            'source': 'AirAsia Grocer',
            'country_code': COUNTRY.upper(),
            'url': store_url,
            'name': store.get('name'),
            'latitude': float(store['lat']) if 'lat' in store else None,
            'longitude': float(store['long']) if 'long' in store else None,
            'address': store.get('location'),
            'street_address': store.get('address_level_2'),
            'postal_code': store.get('postal_code'),
            'city': store.get('address_level_3'),
            'phone_number': store.get('phone'),
            'restaurant_id': store.get('uuid'),
            'currency': CURRENCY,
            'restaurant_description': store.get('description'),
            'menu_url': store.get('store_url'),
            'live_at': store.get('opened_at'),
            'is_free_delivery': True if store.get('delivery_fee') else False,
            'vendor_type': VENDOR_TYPE,
            'restaurant_url': store.get('store_url'),
            'pickup_enabled': True if store.get('is_self_pickup') else False,
            'unmapped': {}
        }
        add_blank_values(restaurant)
        restaurants.append(restaurant)
        compiled += 1
    total += 1

print(f'Total: {total}')
print(f'Compiled: {compiled}')
if restaurants:
    restaurants = json.loads(json.dumps(restaurants, sort_keys=True))  # sorting by key
    if not COMPILE_ALL:
        restaurants.extend(compiled_restaurants)

    restaurants = sorted(restaurants, key=lambda k: k['timestamp'])  # sorting by time extracted

    print(json.dumps(restaurants[0], indent=2))
    print('='*100)
    print(json.dumps(restaurants[-1], indent=2))

    myfilename = datetime.now().strftime("%Y%m%d")+"_airasia_"+COUNTRY+"_stores.txt"
    with open(os.path.join(COMPILED_RESTAURANTS_DIRECTORY, myfilename), 'w') as f:
        f.write('\n'.join(map(json.dumps, restaurants)))
