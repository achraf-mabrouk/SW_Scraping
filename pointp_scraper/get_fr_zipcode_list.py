import requests
import json
import pickle


url = "https://apiv1.2l-courtage.com/search_city"
resp = requests.get(url)
data = resp.json()
data = data['data']

list_zipcodes = []

for i in range(len(data)):
   list_zipcodes.append(data[i]['codePostal'])

print("before removing duplicates", len(list_zipcodes))
new_list = list(set(list_zipcodes))
print("after removing duplicates", len(new_list))

with open('fr_zipcodes.pkl', 'wb') as f:
    pickle.dump(new_list, f)