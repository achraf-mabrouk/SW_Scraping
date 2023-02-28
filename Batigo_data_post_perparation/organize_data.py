import json
import jsonlines


categories = ['Plomberie', 'Peintre', 'Électricien', 'Sanitaire', 'Chauffage', 'Menuisier Serrurier', 'Carreleur', 'Outillage & Protection', 'Maçon']

# with open('BatiImmo\CVC.json', 'r') as f:
#     data = json.load(f)
#     chauffage = []
#     for item in data:
#         if "Chauffage" in item['breadcrumb']:
#             chauffage.append(item)



for category in categories:
    with jsonlines.open('output_laplatforme.jsonl') as reader:
        list_items =[]
        for obj in reader:
            if obj['source_parent_category'] == category:
                list_items.append(obj)
        with open(f'laplatform_data/{category}.json', "w") as f:
            print(category, len(list_items))
            json.dump(list_items, f, indent=4)



