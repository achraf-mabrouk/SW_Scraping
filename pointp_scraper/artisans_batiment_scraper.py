import requests
from bs4 import BeautifulSoup
import json
import pickle
import traceback


user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'}


def dump_jsonl(json_record, output_path, append=False):
    """
    Write list of objects to a JSON lines file.
    """
    mode = 'a+' if append else 'w'
    with open(output_path, mode, encoding='utf-8') as f:
        json_record = json.dumps(json_record, ensure_ascii=False)
        f.write(json_record + '\n')


def get_soup(resp):
    page = resp.content
    soup = BeautifulSoup(page, 'lxml')
    return soup


def get_cerif_urls(soup):
    imgs_urls = None
    labels_div = soup.find(
        'div', class_='m-infos__label to-animate helloUp hidden')
    if labels_div:
        imgs_urls = [img.get('src') for img in labels_div.find_all("img")]
        return imgs_urls

    return imgs_urls


def get_artisan_data(soup: BeautifulSoup, url):
    artisan_title = soup.select_one("h1.m-content__title").text.strip()
    artisan_logo = soup.select_one('.o-headerArtisan__img > img').get('src')
    artisan_owner = soup.select_one("h2.m-infos_title").text.strip()
    artisan_address_raw = soup.select_one(".m-infos__adress").text.strip()
    artisan_address = " ".join(artisan_address_raw.split())
    artisan_email = soup.select_one('div.a-el__link')
    if artisan_email:
        artisan_email = artisan_email.get_text().strip().replace(' at ', '@')
    else:
        artisan_email = None
    try:
        job = soup.find('h5').text
    except:
        job = None
    specialities_ul1 = soup.select_one('.m-spe__listInline')
    specialities_li = soup.find_all(
        'li', class_='m-spe__list to-animate helloUp hidden')
    cerificates_urls = get_cerif_urls(soup)

    specialities_list = []
    if specialities_ul1:
        specialities = specialities_ul1.find_all('li')
        specialities_list = [speciality.text.strip()
                             for speciality in specialities]
    elif specialities_li:
        specialities_list = [speciality.text.strip()
                             for speciality in specialities_li]
    else:
        specialities_div = soup.select_one('.o-infoSpe__spe')
        specialities = specialities_div.find_all('p')

        if specialities and specialities[0] != "":
            specialities_list = [speciality.text.strip()
                                 for speciality in specialities]

    phone_nums = soup.select("a.a-el__link")
    try:
        phone1 = phone_nums[0].get_text().strip()
    except:
        phone1 = None
    try:
        phone2 = phone_nums[1].get_text().strip()
    except:
        phone2 = None
    try:
        artisan_site = soup.find(
            'a', {'class': 'a-el__link', 'target': "_blank"}).get('href')
    except:
        artisan_site = None

    return {
        "artisan_title": artisan_title,
        "artisan_logo": artisan_logo,
        "artisan_owner": artisan_owner,
        "artisan_address": artisan_address,
        "phone1": phone1,
        "phone2": phone2,
        "artisan_email": artisan_email,
        "artisan_site": artisan_site,
        "job": job,
        "specialities_list": specialities_list,
        'certificates_urls': cerificates_urls,
        'original_link': url
    }

# scrape artisans urls
def get_urls(soup):
    artisan_urls = []
    artisan_urls_elem = soup.find_all("a", class_="a-artisanTease__link")

    for url_elem in artisan_urls_elem:
        url = url_elem.get('href')
        print(url)
        artisan_urls.append(url)

    return artisan_urls

# file writer
def write_links(urls):
    with open('available_links.txt', "a+") as f:
        for url in urls:
            f.write(url + '\n')


def load_pkl_file(filename):
    with open(f'{filename}.pkl', 'rb') as f:
        data = pickle.load(f)
    return data


# get all artisans urls and save them to txt file
def get_all_urls():
    base_url = "https://www.artisans-du-batiment.com/trouver-un-artisan-qualifie/"
    zipcode_list = load_pkl_file("fr_zipcodes")

    jobs = ['Carreleur', 'Charpentier', 'Couvreur', 'Electricien', 'Plombier', 'Chauffagiste', 'Maçon',
            'Menuisier', 'Peintre', 'Platrier', 'Plaquiste', 'Serrurier', 'Métallier', 'Tailleur de Pierre']

    for job in jobs:
        urls = []
        print('getting urls of', job)
        for place in zipcode_list:
            params = {'job': job, 'place': place}
            try:
                resp = requests.get(base_url, params=params,
                                    headers=user_agent, verify=False)
                print("getting urls...")
                soup = get_soup(resp)
                urls = get_urls(soup)
                print("Writing urls to the file...")
                write_links(urls)
                print('Done!')
            except KeyboardInterrupt:
                break
            except:
                with open("errors.txt", 'a+', encoding='utf-8') as f:
                    f.writelines(traceback.format_exc())


def scrape_all_artisans(urls):
    print('scraping starts now...\n')
    for url in urls:
        print('Processing url:', url)
        try:
            resp = requests.get(url)
            soup = get_soup(resp)
            data = get_artisan_data(soup, url)
            dump_jsonl(data, "artisans_bat_output_v2.jsonl", append=True)
        except KeyboardInterrupt:
            break
        except:
            with open("errors.txt", 'a+', encoding='utf-8') as f:
                f.writelines(url + "\t\t"+traceback.format_exc())


if __name__ == '__main__':
    # get_all_urls()
    to_do_links = load_pkl_file('to_do_list')
    scrape_all_artisans(to_do_links)
    print("Scraping done successfully!")
