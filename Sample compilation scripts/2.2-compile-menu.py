# Major Modules
import os
import re
import ssl
import time
import json
import copy
import glob
import boto3
import random
import requests
import urllib.request
from datetime import datetime

# Check/Change this before every run:
folder_name_input = 'Jun-27-TH'
country = 'th'
folder_name = 'Jun-27-TH'
bucket_name = 'grab-thailand-new'
for_all = '-all' # '-all' or ''
# -------------------------------------------------------- ALL INPUT ENDS HERE
# TWO OUTPUTS in SG-APAC FORMAT:
# 1. Restaurant Data
# 2. Menu Data
# -------------------------------------------------------- 

with open(bucket_name+"/"+folder_name_input+"-remaining-ids"+for_all+".json", 'r') as f:
	remaining = json.load(f)

# Starting S3:
s3 = boto3.resource('s3')
finalbucket = next((bucket for bucket in s3.buckets.all() if bucket.name == bucket_name),'')

# Downloading files to find the restaurant IDs which have been extracted
os.system("aws s3 sync s3://"+bucket_name+"/"+folder_name+"-remaining-restaurants1/ "+"get_menu_data/"+bucket_name+"/"+folder_name+"-remaining-restaurants1/")
print("Extracted", len(glob.glob("get_menu_data/"+bucket_name+"/"+folder_name+"-remaining-restaurants1/*.json")), "/",len(remaining), "restaurants!")

file_time = {}
for obj in finalbucket.objects.filter(Prefix = folder_name+"-remaining-restaurants1"):
	if ".json" in obj.key:
		file_time[obj.key.split('/')[-1].split('.')[0]]=obj.last_modified.isoformat("T").replace("+00:00","Z")

res_done = []
for gi, globfile in enumerate(glob.glob("get_menu_data/"+bucket_name+"/"+folder_name+"-remaining-restaurants1/*.json")):
	if gi%2000 == 0:
		print(gi,'/', len(glob.glob("get_menu_data/"+bucket_name+"/"+folder_name+"-remaining-restaurants1/*.json")))
	with open(globfile, 'r') as f:
		xxx = json.load(f)
		try:
			xxx['timestamp'] = file_time[xxx['ID']]
		except:
			xxx['timestamp'] = None
		res_done.append(xxx)

# -------------------------------------------------------- COMPILING MENU IN WEN WAY STARTS NOW! 

todaysrestaurants = res_done
for resindex,res in enumerate(todaysrestaurants):
	res['country_code'] = country.lower()
	res['source'] = 'grab'
	res['restaurant_id'] = res['ID']
	res['number_of_reviews'] = res['voteCount'] if 'voteCount' in res else None # Wen wants this
	res['rating_detail'] = res['ratingDetail'] if 'ratingDetail' in res else [] # Goes to unmapped
	res['delivered-by'] = res['deliverBy'] if 'deliverBy' in res else None
	res['items'] = []
	if 'menu' in res:
		if 'categories' in res['menu']:
			res['category'] = [{'name': dd['name'], 
							'category_id': dd['ID'] if 'ID' in dd else None,
							'description': None,
							'sort_order': dd['sortOrder'] if 'sortOrder' in dd else None,
							'items': [item['ID'] for item in dd['items']] if 'items' in dd else [] } for dd in res['menu']['categories']]
			for dd in res['menu']['categories']:
				moreitems = [ff for ff in dd['items']] if 'items' in dd else []
				res['items'].extend(moreitems)
	if 'popularItems' in res:
		for dd in res['popularItems']:
			dd['popular'] = True
		res['items'].extend(res['popularItems'])
	if len(res['items']) > 0:
		for itemindex, item in enumerate(res['items']):
			item['item_name'] = item['name']  if 'name' in item else None
			item['item_id'] = item['ID'] if 'ID' in item else None
			item['takeaway_price'] = float(item['takeawayPriceInMin']/100) if 'takeawayPriceInMin' in item else None
			item['discounted_takeaway_price'] = float(item['discountedTakeawayPriceInMin']/100) if 'discountedTakeawayPriceInMin' in item else None
			item['price'] = float(item['priceInMinorUnit']/100) if 'priceInMinorUnit' in item else item['takeaway_price']
			item['discounted_price'] = float(item['discountedPriceInMin']/100) if 'discountedPriceInMin' in item else item['discounted_takeaway_price']
			item['image_url'] = item['imgHref'] if 'imgHref' in item else None
			item['price_unit'] = item['currency'] if 'currency' in item else None
			item['promotion'] = item['campaignName']  if 'campaignName' in item else None
			item['sort_order'] = item['sortOrder']  if 'sortOrder' in item else None
			item['modifier_groups'] = []
			if 'modifierGroups' in item:
				item['modifier_groups'] = item['modifierGroups']
				for mod in item['modifier_groups']:
					mod['modifier_groups_id'] = str(mod['ID']) if 'ID' in mod else None
					mod['max_selection_points'] = int(mod['selectionRangeMax']) if 'selectionRangeMax' in mod else None
					mod['min_selection_points'] = int(mod['selectionRangeMin']) if 'selectionRangeMin' in mod else None
					mod['modifier_options'] = []
					if 'modifiers' in mod:
						mod['modifier_options'] = mod['modifiers']
						for moddd in mod['modifier_options']:
							moddd['option_id'] = str(moddd['ID']) if 'ID' in moddd else None
							if 'priceInMinorUnit' in moddd:
								moddd['price'] = float(moddd['priceInMinorUnit']/100)
							elif 'priceV2' in moddd:
								if 'amountInMinor' in moddd['priceV2']:
									moddd['price'] = float(moddd['priceV2']['amountInMinor']/100)
								elif 'amountDisplay' in moddd['priceV2']:
									moddd['price'] = float(moddd['priceV2']['amountDisplay'])
								else:
									moddd['price'] = None
							else:
								moddd['price'] = None

modifier_options_keys = ['option_id', 'available', 'price', 'name']
for resindex,res in enumerate(todaysrestaurants):
	if 'items' in res:
		for itemindex, item in enumerate(res['items']):
			if 'modifier_groups' in item:
				for modindex,mod in enumerate(item['modifier_groups']):
					if 'modifier_options' in mod:
						for modddindex,moddd in enumerate(mod['modifier_options']):
							yalla_found = {}
							yalla_notfound = {}
							yalla_found = {k : v for k, v in todaysrestaurants[resindex]['items'][itemindex]['modifier_groups'][modindex]['modifier_options'][modddindex].items() if k in modifier_options_keys}
							# print(json.dumps(yalla_found,indent=2))
							yalla_notfound = {k : None for k in modifier_options_keys if not k in yalla_found}
							# print(json.dumps(yalla_notfound,indent=2))
							todaysrestaurants[resindex]['items'][itemindex]['modifier_groups'][modindex]['modifier_options'][modddindex] = {**yalla_found, **yalla_notfound}
							# print(json.dumps(todaysrestaurants[resindex]['items'][itemindex]['modifier_groups'][modindex]['modifier_options'][modddindex],indent=2))
							# input()

modifier_keys = ['modifier_groups_id', 'available', 'max_selection_points', 'min_selection_points', 'name',  'modifier_options', 'description', 'allow_multiple_same_item']
for resindex,res in enumerate(todaysrestaurants):
	if 'items' in res:
		for itemindex, item in enumerate(res['items']):
			if 'modifier_groups' in item:
				for modindex,mod in enumerate(item['modifier_groups']):
					yalla_found = {}
					yalla_notfound = {}
					yalla_found = {k : v for k, v in todaysrestaurants[resindex]['items'][itemindex]['modifier_groups'][modindex].items() if k in modifier_keys}
					# print(json.dumps(yalla_found,indent=2))
					yalla_notfound = {k : None for k in modifier_keys if not k in yalla_found}
					# print(json.dumps(yalla_notfound,indent=2))
					todaysrestaurants[resindex]['items'][itemindex]['modifier_groups'][modindex] = {**yalla_found, **yalla_notfound}
					# print(json.dumps(todaysrestaurants[resindex]['items'][itemindex]['modifier_groups'][modindex],indent=2))
					# input()

item_keys = ['item_id', 'item_name', 'price', 'price_unit', 'description', 'image_url', 'sort_order',
				'discounted_price', 'takeaway_price', 'discounted_takeaway_price', 'promotion', 'modifier_groups',
				'labels', 'sort_order', 'popular', 'alcohol', 'available']
for resindex,res in enumerate(todaysrestaurants):
	if 'items' in res:
		for itemindex, item in enumerate(res['items']):
			yalla_found = {}
			yalla_notfound = {}
			yalla_found = {k : v for k, v in todaysrestaurants[resindex]['items'][itemindex].items() if k in item_keys}
			yalla_notfound = {k : None for k in item_keys if not k in yalla_found}
			todaysrestaurants[resindex]['items'][itemindex] = {**yalla_found, **yalla_notfound}
			# print(json.dumps(yalla_found,indent=2))
			# print(json.dumps(yalla_notfound,indent=2))
			# print(json.dumps(todaysrestaurants[resindex]['items'][itemindex], indent=2))
			# input()

menu_keys = ['category', 'items', # These variables contain menu data
			'timestamp' , 'source', 'country_code', 'restaurant_id']
unmapped_keys = ['delivered-by', 'rating_detail', 'number_of_reviews', 'rating'] # Wen wants rating and number_of_reviews
for resindex, res in enumerate(todaysrestaurants):
	unmapped = {k : v for k, v in todaysrestaurants[resindex].items() if k in unmapped_keys}
	yalla_found = {}
	yalla_notfound = {}
	yalla_found = {k : v for k, v in todaysrestaurants[resindex].items() if k in menu_keys}
	yalla_notfound = {k : None for k in menu_keys if not k in yalla_found}
	# Adding unmapped in the same line:
	todaysrestaurants[resindex] = { **yalla_found, **yalla_notfound, **{'unmapped': str(json.dumps(unmapped,sort_keys=True))} }

todaysrestaurants = sorted(todaysrestaurants, key=lambda k: k['timestamp']) # Sorting by time extracted
todaysrestaurants = json.loads(json.dumps(todaysrestaurants,sort_keys=True)) # Sorting by key name

myfilename = datetime.now().strftime("%Y%m%d")+"_grab_"+country+"_item.json"
print(myfilename)

print(json.dumps(todaysrestaurants[0],indent=2))
print(json.dumps(todaysrestaurants[-1],indent=2))

with open(bucket_name+"/"+myfilename, 'w') as f:
	f.write('\n'.join(map(json.dumps, todaysrestaurants)))

os.system("rm -r "+bucket_name+"/"+myfilename+".gz")
os.system("gzip -k "+bucket_name+"/"+myfilename)
finalbucket.upload_file(bucket_name+"/"+myfilename, myfilename)
finalbucket.upload_file(bucket_name+"/"+myfilename+".gz", myfilename+".gz")
