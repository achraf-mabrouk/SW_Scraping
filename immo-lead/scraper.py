from bs4 import BeautifulSoup
from login import login
from decimal import Decimal
import re
import json

base_url = "https://immo-lead.com/appli/"


def dump_jsonl(json_record, output_path, append=False):
    """
    Write list of objects to a JSON lines file.
    """
    mode = 'a+' if append else 'w'
    with open(output_path, mode, encoding='utf-8') as f:
        json_record = json.dumps(json_record, ensure_ascii=False)
        f.write(json_record + '\n')

def get_soup(response):
    page = response.content
    soup = BeautifulSoup(page, 'lxml')
    return soup


def clean_text(text):
    new_text = ""
    new_text = text.replace(' €', '')
    new_text = new_text.replace(r'\xa0', r' ')
    new_text = " ".join(new_text.split())
    return new_text


def tranform_typo(typo):
    nb_pieces = typo.split(' ')[0]
    if nb_pieces == "Studio":
        typo = "T1"
    else:
        typo = "T"+nb_pieces
    return typo


def convert_montant(montant: str) -> float:
    decimal_montant = Decimal(re.sub(r'[^\d.]', '', montant))
    return int(decimal_montant)


def get_annexes(soup):
    divs = soup.select("div.annexes > div")
    annexes = {}
    total = 0.0
    for div in divs:
        raw_text = div.text
        kv = raw_text.split(' : ')
        annexes[kv[0].lower()] = clean_text(kv[1])
        mesure = kv[1].split()[0].replace(',', '.')
        total += float(mesure)
    
    if total:
        total = round(total, 2)
        total = str(total)+" " + "m²"  
    return annexes, total


def extract_etiquette_fisc(text):
    if "PINEL" in text:
        return "PINEL"
    elif "LMNP-LMP" in text:
        return "LMNP-LMP"
    elif "PLS" in text:
        return "PLS"
    else:
        return "-"


def get_lot_prices(row):
    '''this function extract:
       - Prix du package TVA 20 % 'prix_immo_tva_norm'
       - Prix du package TVA 5.5 % (if exists) 'prix_immo_tva_red'
       - Prix "Appartement" in 20 % (if exists) prix_hors_parking_norm
       - Prix "Appartement" in 5.5 % (if exists) prix_hors_parking_red
       - lot has a parking (return YES or NO)
    '''
    package_detail = row.select_one('.package_detail')
    parking = []
    if package_detail:
        divs = package_detail.select('.prixpackage.wrap')
        # get prix_immo_tva_norm
        try:
            prix_immo_tva_norm = divs[0].select_one('.wrap-head > b').text
            prix_immo_tva_norm = clean_text(prix_immo_tva_norm.split(':')[-1].strip())
            prix_immo_tva_norm = convert_montant(prix_immo_tva_norm)
        except:
            prix_immo_tva_norm = "-"
        # get prix appartement hors parking of 20 % + check whether lot has a parking
        try:
            detail_divs = divs[0].select('.wrap-body > div')
            prix_hp_norm_raw = detail_divs[0].text
            prix_hp_norm_raw = prix_hp_norm_raw.split('-')[-1]
            prix_hors_parking_norm = convert_montant(clean_text(prix_hp_norm_raw))
            divs_detail = divs[0].select('.wrap-body > div')
            for div in divs_detail:
                cleaned_text = clean_text(div.text)
                if "Parking" in cleaned_text:
                    parking_ref = cleaned_text.split(' - ')[1]
                    parking.append(parking_ref)
        except IndexError:
            prix_hors_parking_norm = "-"

        # get prix_immo_tva_red
        try:
            prix_immo_tva_red = divs[1].select_one('.wrap-head > b').text
            prix_immo_tva_red = clean_text(prix_immo_tva_red).split(':')[-1].strip()
            prix_immo_tva_red = convert_montant(prix_immo_tva_red)
        except:
            prix_immo_tva_red = "-"
        # get prix appartement hors parking of 5.5 %
        try:
            raw_text = divs[1].select_one('.wrap-body > .packagesection').text
            prix_hors_parking_red = clean_text(raw_text.split('-')[-1])
            prix_hors_parking_red = convert_montant(prix_hors_parking_red)
        except:
            prix_hors_parking_red = '-'
    else:
        # cas particulé
        try:
            spans = row.select(".prixlotsimple > span")
            prix_immo_tva_norm = clean_text(spans[0].text.split('-')[0])
            prix_immo_tva_norm = convert_montant(prix_immo_tva_norm)
            if len(spans) == 2:
                prix_immo_tva_red = convert_montant(clean_text(spans[1].text.split('-')[0]))
            else:
                prix_immo_tva_red = None
            prix_hors_parking_norm = prix_immo_tva_norm
            prix_hors_parking_red = None
        except:
            prix_immo_tva_norm = None
            prix_immo_tva_red = None
            prix_hors_parking_norm = None
            prix_hors_parking_red = None

    return {
        'parking': parking,
        'prix_immo_tva_norm': prix_immo_tva_norm,
        'prix_hors_parking_norm': prix_hors_parking_norm,
        'prix_immo_tva_red': prix_immo_tva_red,
        'prix_hors_parking_red': prix_hors_parking_red,
    }


def get_lot_info(s, url):
    url = url.replace('detail', 'lots')
    resp = s.get(url)
    soup = get_soup(resp)
    rows = soup.find_all('tbody')
    list_lots = []
    for row in rows:
        lot = dict()
        tds = row.select('td.searchable.withdetailline')
        typo = clean_text(tds[3].text)
        typo = tranform_typo(typo)
        surf_habit = clean_text(tds[4].text)
        # get status & transform to convenient form
        status = clean_text(tds[12].text)
        if "Optionné" in status or "Indisponible" in status or "Réservé" in status:
            status = "Optionné"
        elif status == "Disponible":
            status = "Libre"
        lot_prices = get_lot_prices(row)
        try:
            prix_int = lot_prices['prix_hors_parking_norm']
            prix_au_m_carre = float(prix_int) / float(surf_habit.split()[0].replace(',', '.'))
            prix_au_m_carre = round(prix_au_m_carre, 2)
        except:
            prix_au_m_carre = 0.0
        # get plan files    
        plan = [base_url+link.get('href') for link in tds[9].select('a.plan')]
        if plan == []:
            plan = [base_url+link.get('href') for link in tds[9].select('a.btnMedia')]

        etiquette_fisc = extract_etiquette_fisc(clean_text(tds[5].text))
        loyer = clean_text(tds[6].text)
        annexes, surface_annexe = get_annexes(row)
        try:
            exposition = row.select_one('div:nth-child(13) > div.dispositif').text
            exposition = clean_text(exposition)
        except:
            exposition = "-"
        lot = {
            "reference": clean_text(tds[1].text),
            "type_residence": clean_text(tds[2].text),
            "typo": typo,
            "surf_habit": surf_habit,
            "etiquette_fisc": etiquette_fisc,
            "rentabilite": clean_text(tds[7].text),
            "etage": clean_text(tds[8].text),
            "plan": plan,
            "status": status,
            "exposition": exposition,
            "loyer_mens": loyer,
            "prix_au_m_carre": prix_au_m_carre,
            "annexes": annexes,
            "surface_annexe": surface_annexe,
        }
        lot.update(lot_prices)

        list_lots.append(lot)

    return list_lots


def get_prog_medias(s, url):
    url = url.replace('detail', 'medias')
    type_media = ['document', 'media']
    # get prog documents
    resp = s.get(url, params={'typeMedia': type_media[0]})
    soup = get_soup(resp)
    doc_tds = soup.select('tbody > tr > td:nth-child(2)')
    doc_list = []
    for doc_td in doc_tds:
        dicct = {}
        pdf_url = doc_td.find('a').get('href')
        dicct['doc_url'] = base_url + pdf_url
        dicct['doc_name'] = doc_td.select_one('p > strong').text
        doc_list.append(dicct)
    # get prog images (media)
    resp = s.get(url, params={'typeMedia': type_media[1]})
    soup = get_soup(resp)
    img_tds = soup.select('tbody > tr > td:nth-child(2)')
    images_prog = []
    for img_td in img_tds:
        dicct = {}
        img_url = img_td.select_one('a > img').get('src')
        dicct['img_url'] = img_url
        dicct['img_name'] = img_td.select_one('p > strong').text
        images_prog.append(dicct)

    return {
        "documents": doc_list,
        "images_prog": images_prog
    }


def get_localisation(adresse):
    words = adresse.split()
    for i in range(len(words)):
        if words[i].isdigit() and len(words[i]) == 5:
            zipcode_index = i
            break
    loc = " ".join(words[i] for i in range(zipcode_index, len(words)))
    # convert to format "department + linespace + postal_code"
    loc = reversed(loc.split())
    return " ".join(loc)


def get_prog_data(s, url):
    resp = s.get(url)
    soup = get_soup(resp)
    date_livraision = soup.select_one('#dateLivraison > span').text.strip()
    miniature_img = base_url + soup.select_one('#imgProgramme > img').get('src')
    description = soup.select_one('#descriptif_programme > p').text
    adresses = soup.select("p.mb0")
    try:
        adresse = clean_text(adresses[0].text)
    except:
        adresse = None
    try:
        adresse_b_vente = clean_text(adresses[1].text)
    except:
        adresse_b_vente = None
    localisation = get_localisation(adresse)
    zone_fiscale = soup.select_one("#caratProg > p").text.split()[-1]
    # get nbr lots
    lot_details_url = url
    lot_details_url = lot_details_url.replace('detail', 'lots')
    resp = s.get(lot_details_url)
    soup = get_soup(resp)
    nbr_lots = soup.select_one("p#listing_count").text
    nbr_lots = int(nbr_lots.split()[0])
    print('processing lots data')
    lots_list = get_lot_info(s,url)
    # min max price program
    prices_list = []
    for lot in lots_list:
        price = lot['prix_immo_tva_norm']
        
        if price not in [None, '-']:
            prices_list.append(price)

    min_price = min(prices_list)
    max_price = max(prices_list)

    prog_prix = f"De {str(min_price)} à {str(max_price)}"

    return {
        "description": description,
        "livraison": date_livraision,
        "miniature_img": miniature_img,
        "program_url": url,
        "adresse": adresse,
        "adresse_b_vente": adresse_b_vente,
        "localisation": localisation,
        "nbr_lots": nbr_lots,
        "zone_fiscale": zone_fiscale,
        "promoteur": "IMMOLEAD",
        "commission_nette": None,
        "prix_prog": prog_prix,
        "medias": get_prog_medias(s, url),
        "lots_list" : lots_list,
        
    }


def get_progs_urls(s):
    resp = s.get('https://immo-lead.com/appli/ajax-liste-lot?typeaction=filterLots&form=types%255B%255D%3D1%26types%255B%255D%3D2%26types%255B%255D%3D3%26types%255B%255D%3D14%26surface%3D%26budget%3D%26livraison%3D')
    soup = get_soup(resp)
    urls_elems = soup.select(".divParamMedia > ul > li:nth-child(2) > a")
    urls = [base_url + url_elem.get('href') for url_elem in urls_elems]
    return list(set(urls))


if __name__ == '__main__':
    url = "https://immo-lead.com/"
    # prog_url = "https://immo-lead.com/appli/detail-programme-52632"
    s = login(url)
    urls = get_progs_urls(s)
    data = []
    for url in urls:
        prog_data = get_prog_data(s, url)
        data.append(prog_data)

    with open('immo_lead_data_v2.json', 'w') as f:
        json.dump(data, f, indent=4)
