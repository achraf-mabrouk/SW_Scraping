from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import json
import traceback


def initiate_driver():
    print("Initiating driver.")
    global driver
    # Chrome configurations
    options = ChromeOptions()
    # options.add_argument("--incognito")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--disable-blink-features=AutomationControlled')
    # options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument("--lang=fr")
    options.add_argument("--start-maximized")
    # options.add_experimental_option('useAutomationExtension', False)
    options.headless = False
    # open driver
    driver = webdriver.Chrome(service=Service(
        ChromeDriverManager().install()), options=options)


def dump_jsonl(json_record, output_path, append=False):
    """
    Write list of objects to a JSON lines file.
    """
    mode = 'a+' if append else 'w'
    with open(output_path, mode, encoding='utf-8') as f:
        json_record = json.dumps(json_record, ensure_ascii=False)
        f.write(json_record + '\n')


def login(url):
    print(f'Logging in...')
    driver.get(url)

    cardNumber = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="main"]//*[@id="cardNumber"]')))
    cardNumber.send_keys('2005015941193')
    cardNumber.send_keys(Keys.ENTER)
    password = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//*[@id="password"]')))
    password.send_keys('Nassim2022!@')
    password.send_keys(Keys.ENTER)


def save_urls(products_urls):
    with open("product_urls.txt", 'a+') as f:
        for product_url in products_urls:
            f.write(product_url + "\n")


def get_products_urls():
    i = 1
    while True:
        products_urls = []
        try:
            url = f"https://www.laplateforme.com/recherche?query=&page={i}"
            driver.get(url)
            products_list = WebDriverWait(driver, 10).until(
                EC.visibility_of_all_elements_located(
                    (By.CSS_SELECTOR, '.card-container-v4.ng-scope'))
            )

            for product in products_list:
                product_url = product.find_element(
                    By.TAG_NAME, value='a').get_attribute('href')
                products_urls.append(product_url)
            save_urls(products_urls)

        except TimeoutException:
            print("reached the last page")
            driver.close()
            break
        i = i + 1

    return products_urls


def get_technical_sheet():
    technical_sheet = {}
    try:
        table = driver.find_element(By.CSS_SELECTOR, "tbody")
        for row in table.find_elements(By.TAG_NAME, 'tr'):
            cols = row.find_elements(By.TAG_NAME, 'td')
            technical_sheet[cols[0].text] = cols[1].text
    except:
        pass

    return technical_sheet


def get_breadcrumb():
    il_elems = driver.find_elements(By.CSS_SELECTOR, value="#breadcrumb > ul > li")
    return [il.text for il in il_elems if il.text != ">"]


def get_product_data(url):
    print('Im in get_product_item')
    driver.get(url)
    pictures_product = []
    try:
        product_name = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#title"))).text
    except:
        product_name = None
    try:
        ref_produit = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, ".product-ref > span"))).text
    except:
        ref_produit = None
    try:
        logo_seller = WebDriverWait(driver, 10).until(EC.presence_of_element_located((
            By.XPATH, '//*[@id="main"]//img'))).get_attribute("src")
    except:
        logo_seller = None
    try:
        product_imgs = WebDriverWait(driver, 10).until(EC.visibility_of_all_elements_located(
            (By.XPATH, '//*[@class="jcarousel"]//*[@class="image-wrapper"]/img')))
        if product_imgs:
            for imgsrc in product_imgs:
                pictures_product.append(imgsrc.get_attribute('src'))
    except:
        product_imgs = None

    try:
        prix_ht_divs = driver.find_elements(By.XPATH, '(//*[@id="intro"]//*[@class="main-price"])[1]//div')
        prix_ht_raw = ' '.join([div.text for div in prix_ht_divs])
        prix_ht = prix_ht_raw.split('€')[0].replace(' ', '')
    except:
        prix_ht = None
    
    try:
        description_ul = driver.find_elements(By.CSS_SELECTOR, ".technical-features > ul > li")
        description_body = ' '.join([li.text for li in description_ul])
    except:
        description_body = None
    

    technical_sheet = get_technical_sheet()
    try:
        breadcrumb = get_breadcrumb()
        breadcrumb[-1] = product_name
    except:
        breadcrumb = None
    try:
        name_seller = technical_sheet['MARQUE']
    except:
        name_seller = None

    try:
        source_parent_category = breadcrumb[1]
    except:
        source_parent_category = None

    try:
        breadcrumb_needed = breadcrumb[-2]
    except:
        breadcrumb_needed = None

    return {
        "breadcrumb": breadcrumb,
        "breadcrumb_needed": breadcrumb_needed,
        "product_name": product_name,
        "ref_produit": ref_produit,
        "logo_seller": logo_seller,
        "name_seller": name_seller,
        "pictures_product": pictures_product,
        "prix_ht": prix_ht,
        "date_published": None,
        "description_body": description_body,
        'description_review': None,
        "description_points": None,
        "original_link": url,
        "technical_sheet": technical_sheet,
        "source_parent_category": source_parent_category
    }


if __name__ == '__main__':
    base_url = "https://www.laplateforme.com/"
    login_url = "https://www.laplateforme.com/users/login"

    initiate_driver()
    login(login_url)

    with open("product_urls.txt", 'r') as f:
        product_url_list = f.readlines()
        product_url_list = [x.replace('\n', '') for x in product_url_list]
        number_of_prod = len(product_url_list)

        counter = 1
        for i in range(number_of_prod) :
            print(f'[{counter}/{number_of_prod}] => processing url', product_url_list[i])
            try:
                product_data = get_product_data(product_url_list[i])
                dump_jsonl(product_data, "output.jsonl", append=True)
            except KeyboardInterrupt:
                break
            except:
                with open("errors.txt", 'a+', encoding='utf-8') as f:
                    f.writelines(product_url_list[i] + "\t\t"+traceback.format_exc())
            counter += 1

        print('Scraping all urls is done successfully!!')
    driver.quit()
