import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials


def getsheet(sheet_key, sheet_name):
	scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
	credentials = ServiceAccountCredentials.from_json_keyfile_name('foodpanda-sheets-api.json', scope)
	gc = gspread.authorize(credentials)
	sheet = gc.open_by_key(sheet_key)
	for s in sheet.worksheets():
		if sheet_name == s.title:
			worksheet = sheet.worksheet(sheet_name)
			# print ("Already Sheet", sheet_name)
			csvdata = worksheet.get_all_values()
			return csvdata
	if not 'worksheet' in locals(): #If there is no variable by the name worksheet in the function
		return []

sheetdata = getsheet('1tw23yiZq4-o6G9XhhVVELUODh-FKyobTTt1vjSKpC8I', "Menu")
fpformat = {}
for row in sheetdata[1:]:
	fpformat[row[0]]= row[2]

mybase = {k:v.split('.')[0] for k, v in fpformat.items() if not '.' in k}
myitems =  {k.replace('items.',''):v.split('.')[0] for k, v in fpformat.items() if 'items.' in k and k.count('.')==1}
mymodifier_groups = {k.replace('items.modifier_groups.',''):v.split('.')[0] for k, v in fpformat.items() if 'items.modifier_groups.' in k and k.count('.')==2}
mymodifiers = {k.replace('items.modifier_groups.modifier_options.',''):v.split('.')[0] for k, v in fpformat.items() if 'items.modifier_groups.modifier_options.' in k and k.count('.')==3}

# Checking base
for resindex,res in enumerate(todaysrestaurants):
	data_variables = {}
	for key in res:
		data_variables[key] = type(res[key]).__name__ # Saving the type of each key
	for k in data_variables:
		if not k in mybase:
			print("Extra key", k, "found")
	for k in mybase:
		if not k in data_variables:
			print("Key", k, "not found")
	for k in mybase:
		if not (mybase[k] == data_variables[k] or data_variables[k] == 'NoneType'):
			print(k, '::', data_variables[k], "-->", mybase[k])

# Checking items
for resindex,res in enumerate(todaysrestaurants):
	if len(res['items']) > 0:
		for item in res['items']:
			data_variables = {}
			for key in item:
				data_variables[key] = type(item[key]).__name__ # Saving the type of each key
			for k in data_variables:
				if not k in myitems:
					print("Extra key", k, "found")
			for k in myitems:
				if not k in data_variables:
					print("Key", k, "not found")
			for k in myitems:
				if not (myitems[k] == data_variables[k] or data_variables[k] == 'NoneType'):
					print(k, '::', data_variables[k], "-->", myitems[k])

# Checking modifier_groups
for resindex,res in enumerate(todaysrestaurants):
	if len(res['items']) > 0:
		for item in res['items']:
			if len(item['modifier_groups']) > 0:
				for modd in item['modifier_groups']:
					data_variables = {}
					for key in modd:
						data_variables[key] = type(modd[key]).__name__ # Saving the type of each key
					for k in data_variables:
						if not k in mymodifier_groups:
							print("Extra key", k, "found")
					for k in mymodifier_groups:
						if not k in data_variables:
							print("Key", k, "not found")
					for k in mymodifier_groups:
						if not (mymodifier_groups[k] == data_variables[k] or data_variables[k] == 'NoneType'):
							print(resindex, k, '::', data_variables[k], "-->", mymodifier_groups[k])

# Checking modifiers
for resindex,res in enumerate(todaysrestaurants):
	if len(res['items']) > 0:
		for item in res['items']:
			if len(item['modifier_groups']) > 0:
				for modd in item['modifier_groups']:
					if len(modd['modifier_options']) > 0:
						for moddadd in modd['modifier_options']:
							data_variables = {}
							for key in moddadd:
								data_variables[key] = type(moddadd[key]).__name__ # Saving the type of each key
							for k in data_variables:
								if not k in mymodifiers:
									print("Extra key", k, "found")
									print(json.dumps(data_variables,indent=2))
							for k in mymodifiers:
								if not k in data_variables:
									print("Key", k, "not found")
							for k in mymodifiers:
								if not (mymodifiers[k] == data_variables[k] or data_variables[k] == 'NoneType'):
									print(resindex, k, '::', data_variables[k], "-->", mymodifiers[k])


