import jsonlines
import pickle
from copy import deepcopy
import json

def dump_jsonl(json_record, output_path, append=False):
    """
    Write list of objects to a JSON lines file.
    """
    mode = 'a+' if append else 'w'
    with open(output_path, mode, encoding='utf-8') as f:
        json_record = json.dumps(json_record, ensure_ascii=False)
        f.write(json_record + '\n')

# done_links_list = []

# def save_pkl(filename, links_list):
#         with open(f'{filename}.pkl', "wb") as f:
#             pickle.dump(links_list, f)




# with open('done_links.pkl', 'rb') as f:
#         done_links_list = pickle.load(f)

# available_links = []
# with open('available_links.txt', 'r') as f:
#         available_links = f.readlines()
#         available_links = [url.replace('\n', '') for url in available_links]


# print('number of available links', len(set(available_links)))
# print('number of done links', len(set(done_links_list)))

# difference = list(set(available_links).symmetric_difference(set(done_links_list)))
# print('to_do_list', len(difference))

# save_pkl("to_do_list", difference)

def remove_duplication(test_list):
        res_list = [i for n, i in enumerate(test_list)
            if i not in test_list[n + 1:]]
        return res_list


# print('before removing duplicates', len(list_objs))

# new_list = remove_duplication(list_objs)
# for obj in new_list:
#         dump_jsonl(obj, "artisans_bat_output_final.jsonl", append=True)

# list_objs = []
# with jsonlines.open('artisans_bat_output_final.jsonl') as reader:
#         for obj in reader:
#                 dump_jsonl(obj, "artisans_bat_output_v2.jsonl", append=True)

def get_zipcode(artisan_address):
        str_list = artisan_address.split()
        for stre in str_list:
                if stre.isdigit() and len(stre) == 5:
                        return(int(stre))


def load_jsonlines(file_path):
        list_objs = []
        with jsonlines.open(file_path) as reader:
                for obj in reader:
                        list_objs.append(obj)
        return list_objs

records = load_jsonlines('artisans_bat_output_v2.jsonl')

zipcode_list = []
for record in records:
        zipcode = get_zipcode(record['artisan_address'])
        record['zipcode'] = zipcode


with open('arisan_bat_output_latest.json', "w") as f:
        json.dump(records, f, indent=4)


