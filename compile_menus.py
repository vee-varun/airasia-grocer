import os
import glob
import json
from collections import defaultdict
from datetime import datetime

from html2text import html2text

from constants import COMPILED_MENUS_DIRECTORY, EXTRACTED_PRODUCTS_DIRECTORY, SOURCE, COUNTRY

COMPILE_FOR_ALL_STORES = True  # weather to compile products for all the stores or only for the new stores

ITEM_NULL_KEYS = [
    'item_id', 'item_name', 'price', 'price_unit', 'description', 'image_url', 'sort_order',
    'discounted_price', 'takeaway_price', 'discounted_takeaway_price', 'promotion', 'sort_order', 'popular', 'alcohol', 'available'
]
ITEM_LIST_KEYS = ['modifier_groups', 'labels']

CATEGORY_NULL_KEYS = ['category_id', 'name', 'description', 'sort_order']

compiled_menus = []  # stores for which products have been already compiled
compiled_products_stores_ids = []
if not COMPILE_FOR_ALL_STORES:
    compiled_products_store_files = list(glob.glob(COMPILED_MENUS_DIRECTORY+'/*txt'))
    if compiled_products_store_files:
        compiled_restaurant_file = sorted(compiled_products_store_files)[-1]  # picking the previous one
        with open(compiled_restaurant_file, 'r') as f:
            compiled_menus.extend([json.loads(item) for item in f.readlines()])
        compiled_products_stores_ids.extend([product['restaurant_id'] for product in compiled_menus])


def update_items(product, items):
    p_uuid = product['uuid']
    item = {
        'item_name': product['name'],
        'item_id': p_uuid,
        'description': html2text(product['description']),
        'available': True if product['option_groups'][0]['quantity'] else False,
        'price': float(product['discount_price']),
        'price_unit': 'RM',
        'discounted_price': float(product['price']),
        'image_url': float(product['image']),
    }
    item.update({key: None for key in ITEM_NULL_KEYS if key not in item})
    item.update({key: [] for key in ITEM_LIST_KEYS if key not in item})
    items.append(item)


def update_categories(product, categories):
    p_uuid = product['uuid']
    for category in (product['category'], product['parent_category']):
        uuid = category['uuid']
        if uuid:
            if uuid in categories:
                categories[uuid]['items'].append(p_uuid)
            else:
                categories[uuid] = {
                    'uuid': uuid,
                    'name': category,
                    'items': [p_uuid],
                }
                categories[uuid].update({key: None for key in CATEGORY_NULL_KEYS})


menus = []
total = 0
compiled = 0
for products_file_path in glob.glob(EXTRACTED_PRODUCTS_DIRECTORY+'/*.json'):
    with open(products_file_path, 'r') as f:
        data = json.load(f)
        extracted_on = data['extracted_on']
        products = data['products']
    if products:
        slug = products_file_path.split('/')[-1][:-5]
        store_uuid = products[0]['store']['uuid']
        if COMPILE_FOR_ALL_STORES or store_uuid not in compiled_products_stores_ids:
            menu = {
                'timestamp': extracted_on,
                'source': SOURCE,
                'country_code': COUNTRY,
                'restaurant_id': store_uuid,
            }
            p_items = []
            p_categories = defaultdict(dict)
            for product in products:
                update_items(product, p_items)
                update_categories(product, p_categories)
            menu['categories'] = list(p_categories.values())
            menu['items'] = p_items
            menu['unmapped'] = {}
            menus.append(menu)
            compiled += 1
    total += 1

print(f'Total: {total}')
print(f'Compiled: {compiled}')


if menus:
    menus = json.loads(json.dumps(menus, sort_keys=True))  # sorting by key
    if not COMPILE_FOR_ALL_STORES:
        menus.extend(compiled_menus)

    menus = sorted(menus, key=lambda k: k['timestamp'])  # sorting by time extracted

    print(json.dumps(menus[0], indent=2))
    print('='*100)
    print(json.dumps(menus[-1], indent=2))


    myfilename = datetime.now().strftime("%Y%m%d")+f"_{SOURCE.lower()}_"+COUNTRY+"_products.txt"
    with open(os.path.join(COMPILED_MENUS_DIRECTORY, myfilename), 'w') as f:
        f.write('\n'.join(map(json.dumps, menus)))

