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

# Google Sheets
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Check/Change this before every run:
folder_name_input = 'Jul-04-VN'
country = 'vn'
folder_name = 'Jul-04-VN'
bucket_name = 'grab-vietnam'
for_all = '' # '-all' or ''
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
os.system("aws s3 sync s3://"+bucket_name+"/"+folder_name+"-remaining-restaurants/ "+"get_menu_data/"+bucket_name+"/"+folder_name+"-remaining-restaurants/")
print("Extracted", len(glob.glob("get_menu_data/"+bucket_name+"/"+folder_name+"-remaining-restaurants/*.json")), "/",len(remaining), "restaurants!")

file_time = {}
for obj in finalbucket.objects.filter(Prefix = folder_name+"-remaining-restaurants"):
	if ".json" in obj.key:
		file_time[obj.key.split('/')[-1].split('.')[0]]=obj.last_modified.isoformat("T").replace("+00:00","Z")

res_done = []
for gi, globfile in enumerate(glob.glob("get_menu_data/"+bucket_name+"/"+folder_name+"-remaining-restaurants/*.json")):
	if gi%2000 == 0:
		print(gi,'/', len(glob.glob("get_menu_data/"+bucket_name+"/"+folder_name+"-remaining-restaurants/*.json")))
	with open(globfile, 'r') as f:
		xxx = json.load(f)
		try:
			xxx['timestamp'] = file_time[xxx['ID']]
		except:
			xxx['timestamp'] = None
		res_done.append(xxx)


# --------------------------------------------------------> COMPILING RESTAURANTS IN WEN WAY!
todaysrestaurants = res_done
todaysrestaurants = sorted(todaysrestaurants, key=lambda k: k['ID'])
print(len(list(set([res['ID'] for res in todaysrestaurants]))))

# todaysrestaurants = [ff for ff in todaysrestaurants if 'latitude' in ff['latlng']]

finalrestaurants = []
restaurant_keys = ['restaurant_id', 'name', 'cuisine_type', 'opening_hours', 'rating', 
					'number_of_reviews', 'latitude', 'longitude', 'vendor_type',
				 'address', 'city']
for restaurantsdata in todaysrestaurants:
	restaurant = { key : None for key in restaurant_keys}
	restaurant['timestamp'] = restaurantsdata['timestamp']
	restaurant['source'] = 'grab'
	restaurant['country_code'] = country.upper()
	restaurant['currency'] = "MYR" if country.lower() == "my" else "SGD" if country.lower() == "sg" else "THB"  if country.lower() == "th" else "VND" if country.lower() == "vn" else "PHP"  if country.lower() == "ph" else None
	restaurant['restaurant_id'] = restaurantsdata['ID'] if 'ID' in restaurantsdata else None
	restaurant['restaurant_url'] = 'https://food.grab.com/'+country+'/en/restaurant/grab/'+str(restaurant['restaurant_id'])
	restaurant['menu_url'] = restaurant['restaurant_url']
	restaurant['name'] = restaurantsdata['name'] if 'name' in restaurantsdata else None
	restaurant['name_with_branch'] = restaurant['name']
	restaurant['cuisine_type'] = restaurantsdata['cuisine'].split(',') if 'cuisine' in restaurantsdata else []
	restaurant['rating'] = str(restaurantsdata['rating']) if 'rating' in restaurantsdata else None
	restaurant['number_of_reviews'] = str(restaurantsdata['voteCount']) if 'voteCount' in restaurantsdata else None
	restaurant['latitude'] = float(restaurantsdata['latlng']['latitude']) if 'latlng' in restaurantsdata and 'latitude' in restaurantsdata['latlng'] else None
	restaurant['longitude'] = float(restaurantsdata['latlng']['longitude']) if 'latlng' in restaurantsdata and 'longitude' in restaurantsdata['latlng'] else None
	restaurant['vendor_type'] = str(restaurantsdata['businessType']).lower() if 'businessType' in restaurantsdata else None
	restaurant['vendor_type'] = 'restaurant' if 'food' in restaurant['vendor_type'] else 'grocer'
	restaurant['image_url'] = [restaurantsdata['photoHref']] if 'photoHref' in restaurantsdata else []
	restaurant['delivered-by'] = restaurantsdata['deliverBy'] if 'deliverBy' in restaurantsdata else None
	if 'promo' in restaurantsdata:
		restaurant['promotion'] = restaurantsdata['promo']['description'] if 'description' in restaurantsdata['promo'] else None
	if 'address' in restaurantsdata:
		restaurant['address'] = restaurantsdata['address']['combined_address'] if 'combined_address' in restaurantsdata['address'] else None
		restaurant['city'] = restaurantsdata['address']['city'] if 'city' in restaurantsdata['address'] else None
		restaurant['postal_code'] = restaurantsdata['address']['postcode'] if 'postcode' in restaurantsdata['address'] else None
	try:
		restaurant['opening_hours'] = ["Sunday: " + restaurantsdata['openingHours']['sun'], "Monday: " + restaurantsdata['openingHours']['mon'], "Tuesday: " + restaurantsdata['openingHours']['tue'], "Wednesday: " + restaurantsdata['openingHours']['wed'], "Thursday: " + restaurantsdata['openingHours']['thu'], "Friday: " + restaurantsdata['openingHours']['fri'], "Saturday: " + restaurantsdata['openingHours']['sat']]
	except:
		pass
	restaurant['fulfillment_methods'] = [ff.capitalize() for ff in restaurantsdata['deliveryOptions']] if 'deliveryOptions' in restaurantsdata else []
	restaurant['order_location'] = [{ 	'latitude' : float(restaurantsdata.get('request_latitude', None)),
										'longitude' :  float(restaurantsdata.get('request_longitude', None)),
										'distance' : float(restaurantsdata['distanceInKm']) if 'distanceInKm' in restaurantsdata else None,
										'delivery_time' : str(restaurantsdata['ETA']) if 'ETA' in restaurantsdata else None,
										'delivery_fee' : restaurantsdata['estimatedDeliveryFee']['priceDisplay'] if 'estimatedDeliveryFee' in restaurantsdata and 'priceDisplay' in restaurantsdata['estimatedDeliveryFee'] else None }]
	finalrestaurants.append(restaurant)

contents = open(bucket_name+"/"+folder_name+"-Restaurants-Data-1-WEN-NEW.json", "r").read() 
myrestaurants = [json.loads(str(item)) for item in contents.strip().split('\n')]

myrestaurantsids = [ff['restaurant_id'] for ff in myrestaurants]

# EXTRACTING ONLY NEW RESTAURANTS
# xxx = list(set([ff['restaurant_id'] for ff in finalrestaurants])-set(myrestaurantsids))
# newfinalrestaurants = []
# for ffindex,ff in enumerate(finalrestaurants):
# 	if ffindex%20000 == 0:
# 		print(ffindex, len(finalrestaurants))
# 	if ff['restaurant_id'] in xxx:
# 		newfinalrestaurants.append(ff)

newfinalrestaurants = []
for ffindex,ff in enumerate(finalrestaurants):
	if ffindex%5000 == 0:
		print(ffindex, len(finalrestaurants))
	if not ff['restaurant_id'] in myrestaurantsids:
		newfinalrestaurants.append(ff)

null_keys = ['timestamp', 'source', 'country_code', 'url', 'name', 'name_with_branch', 
			'latitude', 'longitude', 'address', 'chain', 'street_address', 'postal_code', 
			'city', 'area', 'phone_number', 'phone_number_secondary', 'rating', 'number_of_reviews', 
			'restaurant_id', 'promotion', 'newly_added', 'allergy_notes', 'restaurant_description', 
			'currency', 'menu_url', 'contact_person_name', 'open', 'live_at', 'restaurant_email', 'rank', 
			'commission_per_order', 'is_free_delivery', 'total_order', 'minimum_order_price', 
			'vendor_type', 'halal', 'restaurant_url', 'pickup_enabled', 'no_of_seats', 
			'price_per_pax', 'price_per_pax_symbol', 'custom_score', 'payment_method', 'address_local', 
			'shop_holidays', 'transportation_direction', 'private_dining_rooms', 'private_use', 
			'menu_info', 'dining_type', 'location_detail', 'website', 'local_name', 'unmapped']

list_keys = ['opening_hours', 'cuisine_type', 'order_location', 
			'fulfillment_methods', 'image_url', 'facilities']

order_location_keys = ['latitude', 'longitude', 'distance', 'delivery_fee', 'delivery_time']

# Adding keys with blank values
for res in newfinalrestaurants:
	for key in null_keys:
		if not key in res:
			res[key] = None
	for key in list_keys:
		if not key in res:
			res[key] = []
	if len(res['order_location']) > 0:
		for key in order_location_keys:
			for yalla in res['order_location']:
				if not key in yalla:
					yalla[key] = None

# Moving all unknown keys into unmapped
for res in newfinalrestaurants:
	unmapped = {}
	for key in list(res):
		if not key in (null_keys+list_keys):
			unmapped[key] = res.pop(key)
	res['unmapped'] = str(json.dumps(unmapped,sort_keys=True))

myrestaurants.extend(newfinalrestaurants)
myrestaurants = sorted(myrestaurants, key=lambda k: k['timestamp']) # Sorting by time extracted
myrestaurants = json.loads(json.dumps(myrestaurants,sort_keys=True)) # Sorting by key name

print(json.dumps(myrestaurants[0],indent=2))
print(json.dumps(myrestaurants[-1],indent=2))

myfilename = datetime.now().strftime("%Y%m%d")+"_grab_"+country+"_vendors.json"
print(myfilename)

with open(bucket_name+"/"+myfilename, 'w') as f:
	f.write('\n'.join(map(json.dumps, myrestaurants)))

os.system("rm -r "+bucket_name+"/"+myfilename+".gz")
os.system("gzip -k "+bucket_name+"/"+myfilename)
finalbucket.upload_file(bucket_name+"/"+myfilename, myfilename)
finalbucket.upload_file(bucket_name+"/"+myfilename+".gz", myfilename+".gz")

print("TOTAL RESTAURANTS", len(myrestaurants))
