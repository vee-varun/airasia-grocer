"""
Compiles products files as per the required Schema of Menus and
dumps it down in a file.
Will run after extract_products.
Pass "--A" to compile products for  all the stores or "--N" for the new ones.'
Ex: python compile_menus.py --N
"""
import glob
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

from html2text import html2text

from constants import (
    COMPILED_MENUS_DIRECTORY,
    COUNTRY,
    EXTRACTED_PRODUCTS_DIRECTORY,
    SOURCE,
)

# weather to compile products for all the stores or only for the new stores
argv = sys.argv[1:]
err_msg = (
    'INVALID OPTIONS: Pass "--A" to compile products for all the stores '
    'or "--N" to compile for the new ones.'
)
if argv and len(argv) == 1:
    if argv[0] == '--A':
        COMPILE_FOR_ALL_STORES = True
    elif argv[0] == '--N':
        COMPILE_FOR_ALL_STORES = False
    else:
        raise ValueError(err_msg)
else:
    raise ValueError(err_msg)

ITEM_NULL_KEYS = [
    'item_id', 'item_name', 'price', 'price_unit', 'description', 'image_url',
    'sort_order', 'discounted_price', 'takeaway_price',
    'discounted_takeaway_price', 'promotion', 'sort_order', 'popular',
    'alcohol', 'available'
]
ITEM_LIST_KEYS = ['modifier_groups', 'labels']
CATEGORY_NULL_KEYS = ['category_id', 'name', 'description', 'sort_order']

print('Compiling All' if COMPILE_FOR_ALL_STORES else 'Compiling New')

os.makedirs(COMPILED_MENUS_DIRECTORY, exist_ok=True)  # make sure dir exists

compiled_menus = []  # stores for which products have been already compiled
compiled_products_stores_ids = []
if not COMPILE_FOR_ALL_STORES:
    compiled_products_store_files = list(
        glob.glob(COMPILED_MENUS_DIRECTORY+'/*json')
    )
    if compiled_products_store_files:
        # picking the previous one
        compiled_products_store_file = sorted(compiled_products_store_files)[-1]  # noqa
        with open(compiled_products_store_file, 'r') as f:
            compiled_menus.extend(json.load(f))
        compiled_products_stores_ids.extend(
            [product['restaurant_id'] for product in compiled_menus]
        )


def update_items(product, items):
    p_uuid = product['uuid']
    item = {
        'item_name': product['name'],
        'item_id': p_uuid,
        'description': (
            html2text(product['description']) if product['description'] else ""
        ),
        'available': (
            True if product['option_groups'] and product['option_groups'][0]['quantity'] else False  # noqa
        ),
        'price': float(
            product['discount_price'] if product['discount_price']
            else product['price']
        ),
        'price_unit': 'RM',
        'discounted_price': float(product['price']),
        'image_url': product['image'],
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
                    'category_id': uuid,
                    'name': category['name'],
                    'items': [p_uuid]
                }
                categories[uuid].update({key: None for key in CATEGORY_NULL_KEYS if key not in categories[uuid]})


menus = []
no_products = []
products_files_path = glob.glob(EXTRACTED_PRODUCTS_DIRECTORY+'/*.json')
if products_files_path:
    total = len(products_files_path)
    compiled = 0
    done = 0
    for products_file_path in products_files_path:
        p_id = None
        try:
            slug = products_file_path.split('/')[-1][:-5]
            with open(products_file_path, 'r') as f:
                data = json.load(f)
                extracted_on = data['extracted_on']
                products = data['products'] or []
            if products:
                store_uuid = products[0]['store']['uuid']
                if COMPILE_FOR_ALL_STORES or store_uuid not in compiled_products_stores_ids:  # noqa
                    menu = {
                        'timestamp': extracted_on,
                        'source': SOURCE,
                        'country_code': COUNTRY,
                        'restaurant_id': store_uuid,
                    }
                    p_items = []
                    p_categories = defaultdict(dict)
                    for product in products:
                        p_id = product['uuid']
                        update_items(product, p_items)
                        update_categories(product, p_categories)
                    menu['category'] = list(p_categories.values())
                    menu['items'] = p_items
                    menu['unmapped'] = {}
                    menus.append(menu)
                    compiled += 1
            else:
                no_products.append(slug)
            done += 1
            if done % 10 == 0 or done == total:
                print(f'Done: [{done} - {total}]')
        except Exception as err:
            raise Exception(
                f'Got Error while compiling '
                f'Product id: {p_id} from {products_file_path}. Error: {err}'
            )
else:
    print(f'URGENT: No extracted products @ {EXTRACTED_PRODUCTS_DIRECTORY}')

if COMPILE_FOR_ALL_STORES:
    print(
        f'Compiled All:\n'
        f'    Total: {total}\n'
        f'    Compiled: {compiled}\n'
        f'    No Products: {len(no_products)}'
    )
else:
    print(
        f'Compiled New:\n'
        f'    Total: {total}\n'
        f'    Compiled: {compiled}\n'
        f'    No Products: {len(no_products)}'
    )
if no_products:
    print(f'No Products: {no_products}')

if menus:
    menus = json.loads(json.dumps(menus, sort_keys=True))  # sorting by key
    if not COMPILE_FOR_ALL_STORES:
        menus.extend(compiled_menus)
    # sorting by time extracted
    menus = sorted(menus, key=lambda k: k['timestamp'])

    myfilename = (
            datetime.now().strftime("%Y%m%d%H%M%S")
            + f"_{SOURCE.lower()}_"+COUNTRY+"_products.json"
    )
    myfilepath = os.path.join(COMPILED_MENUS_DIRECTORY, myfilename)
    with open(myfilepath, 'w') as f:
        f.write('[\n'+',\n'.join(['  ' + json.dumps(res) for res in menus]) +'\n]') # noqa

    print(f'Compiled menus has been kept @ "{myfilepath}"')

    if input('\nEnter y/Y to see sample menus: ') in ['y', 'Y']:
        print(json.dumps(menus[0], indent=2))
        print('='*100)
        print(json.dumps(menus[-1], indent=2))
