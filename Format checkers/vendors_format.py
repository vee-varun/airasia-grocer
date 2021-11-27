import json

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
#
#
# def getsheet(sheet_key, sheet_name):
# 	scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# 	credentials = ServiceAccountCredentials.from_json_keyfile_name('foodpanda-sheets-api.json', scope)
# 	gc = gspread.authorize(credentials)
# 	sheet = gc.open_by_key(sheet_key)
# 	for s in sheet.worksheets():
# 		if sheet_name == s.title:
# 			worksheet = sheet.worksheet(sheet_name)
# 			# print ("Already Sheet", sheet_name)
# 			csvdata = worksheet.get_all_values()
# 			return csvdata
# 	if not 'worksheet' in locals(): #If there is no variable by the name worksheet in the function
# 		return []
#
# sheetdata = getsheet('1tw23yiZq4-o6G9XhhVVELUODh-FKyobTTt1vjSKpC8I', "Restaurant")
# fpformat = {}
# for row in sheetdata[1:]:
# 	fpformat[row[0]] = row[2]
import glob

from constants import COMPILED_RESTAURANTS_DIRECTORY

compiled_restaurant_files = list(
	glob.glob(COMPILED_RESTAURANTS_DIRECTORY+'/*txt')
)
compiled_restaurants = []
if compiled_restaurant_files:
	# picking the previous one
	compiled_restaurant_file = sorted(compiled_restaurant_files)[-1]
	with open(compiled_restaurant_file, 'r') as f:
		compiled_restaurants = [json.loads(item) for item in f.readlines()]


finalrestaurants = compiled_restaurants
myformat = []
for resindex,res in enumerate(finalrestaurants):
	data_variables = {}
	for key in res:
		data_variables[key] = type(res[key]).__name__ # Saving the type of each key
		if type(res[key]).__name__ == 'list': # Proceed inside only if it is a list
			if len(res[key]) > 0: # Proceed only if it is not empty
				data_variables[key+'.'] = [type(dd).__name__ for dd in res[key]] # Temporary saving to FIND the type of elements in the list
				if len(list(set([type(dd).__name__ for dd in res[key]]))) == 1 or (len(list(set([type(dd).__name__ for dd in res[key]]))) == 2 and 'NoneType' in list(set([type(dd).__name__ for dd in res[key]]))): # If all the elements have the same variable type or if one is NoneType
					data_variables[key] = type(res[key]).__name__+'.'+list(set([type(dd).__name__ for dd in res[key]]))[0] # Save as one variable type
					del data_variables[key+'.'] # Delete the variable we created to check
					if list(set([type(dd).__name__ for dd in res[key]]))[0] == 'dict': # Proceed inside only if it is a dict
						data_variables[key+'.'] = [{kk : type(dd[kk]).__name__ for kk in dd} for dd in res[key]] # Temporary saving to FIND the type of elements in the list of dicts
						list_of_keys = list(set([kk for dd in res[key] for kk in dd]))
						for otherkey in list_of_keys: # Checking for each key
							if len(list(set([type(dd[kk]).__name__ for dd in res[key] for kk in dd if kk == otherkey]))) == 1 or (len(list(set([type(dd[kk]).__name__ for dd in res[key] for kk in dd if kk == otherkey]))) == 2 and 'NoneType' in list(set([type(dd[kk]).__name__ for dd in res[key] for kk in dd if kk == otherkey]))):
								data_variables[key+'.'+otherkey] = list(set([type(dd[kk]).__name__ for dd in res[key] for kk in dd if kk == otherkey]))[0]
							else:
								print("Multiple Data Types found INSIDE DICT "+otherkey+" OF finalrestaurants["+str(resindex)+"]["+key+"]", list(set([type(dd[kk]).__name__ for dd in res[key] for kk in dd if kk == otherkey])))
							if not len(list([type(dd[kk]).__name__ for dd in res[key] for kk in dd if kk == otherkey])) == len(list([type(dd[kk]).__name__ for dd in res[key] for kk in dd]))/len(list_of_keys):
								print("Length inconsistent INSIDE DICT "+otherkey+" OF finalrestaurants["+str(resindex)+"]["+key+"]")
						del data_variables[key+'.']
				else:
					print("Multiple Data Types found in finalrestaurants["+str(resindex)+"]["+key+"]")
	myformat.append(data_variables)

# mf = myformat[0]
# Checking if the format of each matches or not:
for mf in myformat:
	if list(set(list(mf.keys()))-set(list(fpformat.keys()))) != []:
		print("EXTRA KEYS:", list(set(list(mf.keys()))-set(list(fpformat.keys()))),"\n\n")
	elif list(set(list(fpformat.keys()))-set(list(mf.keys()))) != []:
		if str(list(set(list(fpformat.keys()))-set(list(mf.keys())))).count('order_location.') > 5:
			print("LESS KEYS:", list(set(list(fpformat.keys()))-set(list(mf.keys()))),"\n\n")
	for mfk in mf:
		if mf[mfk] == fpformat[mfk]:
			# print("--------------------------------------------", mfk, mf[mfk], fpformat[mfk])
			pass
		elif fpformat[mfk] != 'list' and mf[mfk] == 'NoneType':
			# print("----------------------------",mfk, mf[mfk], fpformat[mfk])
			pass
		elif fpformat[mfk].split('.')[0] == 'list' and mf[mfk] == 'list':
			# print(mfk, mf[mfk], fpformat[mfk])
			pass
		else:
			print(mfk, '::', mf[mfk], '-->', fpformat[mfk])

