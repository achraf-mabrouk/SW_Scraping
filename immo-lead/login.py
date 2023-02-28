import requests
from bs4 import BeautifulSoup


def get_soup(response):
    page = response.content
    soup = BeautifulSoup(page, 'lxml')
    return soup


def generate_headers_after_login(ssid_cookie, idcrm_cookie):
    headers = {
        'authority': 'immo-lead.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9,ar;q=0.8,fr;q=0.7,zh-TW;q=0.6,zh;q=0.5',
        'cache-control': 'max-age=0',
        'cookie': 'PHPSESSID={}; _ga=GA1.2.874273879.1666791156; _gid=GA1.2.814587334.1666791156; idcrm={};'.format(ssid_cookie, idcrm_cookie),
        'referer': 'https://immo-lead.com/',
        'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    }
    return headers


def generate_headers(cookies):
    headers = {
        'authority': 'immo-lead.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'accept-language': 'en-US,en;q=0.9,ar;q=0.8,fr;q=0.7,zh-TW;q=0.6,zh;q=0.5',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': 'PHPSESSID={}; _ga=GA1.2.874273879.1666791156; _gid=GA1.2.814587334.1666791156'.format(cookies['PHPSESSID']),
        'origin': 'https://immo-lead.com',
        'referer': 'https://immo-lead.com/',
        'sec-ch-ua': '"Chromium";v="106", "Google Chrome";v="106", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36'
    }
    return headers

def login(url)-> requests.Session:
    s = requests.Session()

    resp1 = s.get(url)

    headers = generate_headers(s.cookies)
    # getting cnxtoken
    soup = get_soup(resp1)
    token = soup.find('input', {'name': 'cnxtoken'}).get('value')

    payload = 'cnxtoken={}&acceslogin=rachid.bouhlila%40ficap-partners.com&accespwd=Ficap2017!&ssoid=&url=&authentification=auth'.format(
        token)
    # logging in...
    response = s.request("POST", url, headers=headers, data=payload)
    resp2 = s.get('https://immo-lead.com/appli/')

    new_headers = generate_headers_after_login(s.cookies['PHPSESSID'], s.cookies['idcrm'])
    s.headers.update(new_headers)
    return s

