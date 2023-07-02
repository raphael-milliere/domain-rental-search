from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import time
from bs4 import BeautifulSoup
import urllib.request
import os

def scrape_domain_listing(url):
    webdriver_service = Service('chromedriver')  # Enter your chromedriver path here
    options = Options()
    # options.add_argument('--headless')  # Use if you want to not display the browser
    driver = webdriver.Chrome(service=webdriver_service, options=options)
    driver.get(url)
    time.sleep(1) 
    
    # Click 'Read more' button to expand description
    read_more_button = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="listing-details__description-button"]')
    read_more_button.click()

    # Wait for page to load updated content 
    time.sleep(1) 
    soup = BeautifulSoup(driver.page_source, 'html.parser') 

    # Property Features
    try: 
        features = soup.find(id='property-features').find_all('li') 
        features = [feature.get_text() for feature in features] 
    except AttributeError:
        features = ['N/A']

    # Address
    address = soup.find("div", {"data-testid":"listing-details__button-copy-wrapper"}).h1.get_text()

    # Price
    price = soup.find("div", {"data-testid":"listing-details__summary-title"}).get_text()

    # Bedrooms, Bathrooms and Parking
    main_features = soup.find_all("span", {"data-testid":"property-features-feature"})
    bedrooms = main_features[0].get_text()
    bathrooms = main_features[1].get_text()
    parking = main_features[2].get_text()

    # Date Available and Bond 
    summary_strip = soup.find_all("li")
    for li in summary_strip:
        if 'date available' in li.text.lower() or 'available from' in li.text.lower(): 
            date_available = li.find('strong').text
        elif 'bond' in li.text.lower():
            bond_text = li.text.lower()
            if 'bond' in bond_text and '$' in bond_text:  
                bond = li.find('strong').text

    # Full description 
    description = soup.find("div", {"name":"listing-details__description"}).div.get_text()

    # Images
    images = driver.execute_script('return digitalData.page.pageInfo.property.images')
    if not os.path.exists('images'):
        os.makedirs('images')
    for i, img_url in enumerate(images):
        urllib.request.urlretrieve(img_url, f'images/img_{i}.jpg')

    driver.quit()

    data = {
        "address": address,
        "price": price,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "parking": parking,
        "date_available": date_available,
        "bond": bond,
        "features": features,
        "description": description,
    }

    return data

url = "https://www.domain.com.au/1-21-warners-avenue-bondi-beach-nsw-2026-16505976"
print(scrape_domain_listing(url))


# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import time
# import requests

# # make sure the path to chromedriver is correct and it matches the version of your Chrome browser  # noqa: E501
# driver = webdriver.Chrome()

# # open the webpage
# driver.get("https://www.domain.com.au/111-81-macdonald-street-erskineville-nsw-2043-16507284")

# # Wait for the "Read more" button to be visible and click it to reveal the full description
# WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//button[text()="Read more"]'))).click()

# # wait for the page to load
# time.sleep(5)

# # scrape the data
# address = driver.find_element(By.CSS_SELECTOR, "h1.css-164r41r").text
# price = driver.find_element(By.CSS_SELECTOR, "div.css-1texeil").text
# bedrooms = driver.find_element(By.XPATH, "//span[contains(text(),'Beds')]/preceding-sibling::span").text
# bathrooms = driver.find_element(By.XPATH, "//span[contains(text(),'Bath')]/preceding-sibling::span").text
# parking = driver.find_element(By.XPATH, "//span[contains(text(),'Parking')]/preceding-sibling::span").text
# availability = driver.find_element(By.XPATH, "//li[contains(text(),'Available Now')]").text
# bond = driver.find_element(By.XPATH, "//li[contains(text(),'Bond')]").text
# description = driver.find_element(By.XPATH, "//div[@class='css-jg4hce']/p").text

# # print the data
# print(f"Address: {address}")
# print(f"Price: {price}")
# print(f"Bedrooms: {bedrooms}")
# print(f"Bathrooms: {bathrooms}")
# print(f"Parking: {parking}")
# print(f"Availability: {availability}")
# print(f"Bond: {bond}")
# print(f"Description: {description}")

# # download and save the images
# images = driver.find_elements_by_xpath('//img[@class="css-k008qs"]')
# for i, img in enumerate(images):
#     response = requests.get(img.get_attribute('src'))
#     with open(f'image_{i}.jpg', 'wb') as file:
#         file.write(response.content)

# # close the driver
# driver.quit()