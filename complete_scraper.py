from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import urllib.request
import os
import sqlite3
from datetime import datetime
from urllib.parse import urlparse
import re
import json
from PIL import Image

from summary.generator import qa_generation, multi_qa_generation, unwanted_prefixes
from summary.utils import clean_response, adjust_heading_levels
import markdown

# URL and CSS selector
# PROPERTY_PAGE_URLS_CSS_SELECTOR = "div[data-testid='listing-card-wrapper-premiumplus'] a"
PROPERTY_PAGE_URLS_CSS_SELECTOR = "div[data-testid^='listing-card-wrapper-'] a"

START_URL = "https://www.domain.com.au/rent/?suburb=st-leonards-nsw-2065,bellevue-hill-nsw-2023,woollahra-nsw-2025,double-bay-nsw-2028,woolloomooloo-nsw-2011,neutral-bay-nsw-2089,mosman-nsw-2088,paddington-nsw-2021,cremorne-nsw-2090,erskineville-nsw-2043,camperdown-nsw-2050,chippendale-nsw-2008,darlinghurst-nsw-2010,surry-hills-nsw-2010,redfern-nsw-2016,newtown-nsw-2042,ultimo-nsw-2007,north-sydney-nsw-2060,barangaroo-nsw-2000,dawes-point-nsw-2000,haymarket-nsw-2000,millers-point-nsw-2000,pyrmont-nsw-2009,the-rocks-nsw-2000,bondi-nsw-2026,bondi-junction-nsw-2022,bondi-beach-nsw-2026,north-bondi-nsw-2026,glebe-nsw-2037,alexandria-nsw-2015,crows-nest-nsw-2065,marrickville-nsw-2204,coogee-nsw-2034,forest-lodge-nsw-2037,manly-nsw-2095&bedrooms=2-any&price=0-1100&excludedeposittaken=1&sort=dateupdated-desc"

# START_URL = "https://www.domain.com.au/rent/?suburb=erskineville-nsw-2043&bedrooms=2-any&price=0-1100&excludedeposittaken=1&sort=dateupdated-desc"

# Organize the desired features keywords into categories
features_categories = {
    'luxury': ['resort', 'resort-style', 'resort-like', 'luxury', 'luxurious', 'premium', 'high-end', 'upscale', 'exclusive', 'sophisticated', 'refined', 'opulent', 'grand', 'exquisite'],
    'condition': ['new', 'immaculate', 'refurbished', 'modern', 'pristine', 'renovated', 'updated', 'well-maintained', 'spotless', 'contemporary', 'state-of-the-art', 'elegant', 'stylish', 'sleek', 'freshly-painted', 'high-quality', 'top-notch', 'mint-condition', 'meticulous', 'like-new', 'flawless', 'cutting-edge'],
    'uniqueness': ['exceptional', 'superb', 'amazing', 'outstanding', 'stunning', 'fantastic', 'unique', 'breathtaking', 'remarkable', 'extraordinary', 'phenomenal', 'incomparable', 'spectacular', 'prodigious',  'one-of-a-kind', 'custom', 'bespoke', 'artisan', 'handcrafted', 'designer', 'architectural', 'incredible'],
    'light': ['bright', 'light', 'sun-soaked', 'sun-filled', 'luminous', 'sunlit', 'radiant', 'well-lit', 'gleaming', 'sunny', 'daylit', 'illuminated', 'sun-drenched',  'light-filled', 'brightly-lit', 'natural light'],
    'size': ['oversized', 'extra-large', 'enormous', 'huge', 'massive', 'spacious', 'roomy', 'airy', 'large', 'gigantic', 'enormous', 'expansive', 'vast', 'generous', 'ample', 'substantial', 'capacious'],
    'privacy': ['private', 'secluded', 'personal', 'quiet', 'isolated', 'intimate', 'tranquil', 'peaceful', 'undisturbed', 'oasis'],
    'position': ['top', 'upper', 'penthouse', 'top-floor', 'upper-level', 'high-floor', 'elevated'],
    'outdoor_living': ['rooftop', 'loft', 'patio', 'terrace', 'veranda', 'deck', 'balcony', 'courtyard', 'yard', 'garden', 'grounds', 'lawn', 'alfresco', 'outdoor', 'exterior', 'open-air', 'entertainer', 'entertaining', 'sunroom',  'landscaped', 'nature'],
    'work_from_home': ['study', 'office', 'workspace', 'library', 'home office', 'virtual office', 'remote working', 'flex space'],
    'amenities': ['amenities', 'facilities', 'services', 'utilities'],
    'gym': ['gym', 'fitness center', 'health', 'workout', 'exercise room', 'fitness studio', 'training room', 'health club'],
    'pool': ['pool'],
    'spa': ['hot tub', 'jacuzzi', 'sauna', 'steam room'],
    'indoor_features': ['built-in', 'built in', 'in-built', 'laundry', 'integrated', 'inset', 'enclosed', 'storage', 'appliances', 'under-floor', 'air-conditioning'],
    'beach': ['beach', 'seaside', 'oceanfront', 'seafront', 'waterfront', 'coastal', 'shore', 'beachside', 'seaview', 'ocean view'],
    'views': ['views', 'skyline', 'panoramic', 'scenic', 'landscape', 'picturesque', 'horizon'],
    'location': ['minutes', 'moments', 'heart', 'central', 'bars', 'restaurants', 'cafes', 'busy', 'nightlife', 'stroll', 'walking', 'proximity', 'accessible', 'vibrant', 'convenient'],
    'transportation': ['station', 'train', 'bus', 'public transport', 'metro', 'light rail', 'commuter', 'transit', 'ferry']
}

# Sydney Suburbs list
SYDNEY_SUBURBS = ['Alexandria','Allambie Heights','Annandale','Arncliffe','Ashfield','Artarmon','Auburn','Balgowlah','Balmain','Barangaroo','Beacon Hill','Beaconsfield','Bellevue Hill','Bexley','Birchgrove','Blacktown','Bondi Beach','Bondi Junction','Bondi','Botany','Brookvale','Brighton-Le-Sands','Broadway','Bronte','Burwood','Cabramatta','Cammeray','Camperdown','Castle Hill','Centennial Park','Chatswood','Chippendale','Clemton Park','Clovelly','Concord','Coogee','Cremorne','Cronulla','Crows Nest','Curl Curl','Darling Point','Darlinghurst','Darlington','Dawes Point','Double Bay','Dulwich Hill','Earlwood','Eastlakes','Edgecliff','Elizabeth Bay','Enmore','Erskineville','Fairfield','Fairlight','Five Dock','Forest Lodge','Freshwater','Glebe','Greenwich','Haberfield','Haymarket','Haymarket','Hunters Hill','Hurstville','Kellyville','Kensington','Kingsford','Kirribilli','Kogarah','Kurraba Point','Lane Cove','Lavender Bay','Leichhardt','Lewisham','Lidcombe', 'Manly', 'Marrickville','Mascot','McMahons Point','Menai','Middle Cove','Millers Point','Milsons Point','Miranda','Mosman','Naremburn','Neutral Bay','Newington','Newtown','North Bondi','North Ryde','North Sydney','Northbridge','Paddington','Parramatta','Penrith','Petersham','Point Piper','Potts Point','Pymble','Pyrmont','Queenscliff','Queens Park','Randwick','Redfern','Rockdale','Rose Bay','Rosebery','Rushcutters Bay','Ryde','St Leonards','St Peters','Stanmore','Strathfield','Summer Hill','Surry Hills','Sutherland','Sydenham','Sydney','Sydney Olympic Park','Tempe','The Rocks','Turrella','Ultimo','Vaucluse','Waterloo','Waverley','Waverton','Wollstonecraft','Woollahra','Woolloomooloo','Woolooware','Woolwich','Wolli Creek','Zetland']

# Function to resize images
def resize_images(path, max_width):
    for filename in os.listdir(path):
        if filename.endswith(('.jpg', '.png', '.jpeg')):
            img_path = os.path.join(path, filename)
            img = Image.open(img_path)
            width, height = img.size
            if width > max_width:
                new_height = int(max_width * height / width)
                img = img.resize((max_width, new_height), Image.ANTIALIAS)
                img.save(img_path)
  
# Calculate greatness score based on desired feature keywords
def calculate_greatness_score(features, description):
    score = 0
    greatness_details = {}
    if features is not None:
        for category, category_features in features_categories.items():
            found_features = [feature for feature in category_features if feature in features.lower() or feature in description.lower()]
            if found_features:
                score += 1
                greatness_details[category] = found_features
    else:
        features = ''  # Assign an empty string to features if it is None
        for category, category_features in features_categories.items():
            found_features = [feature for feature in category_features if feature in description.lower()]
            if found_features:
                score += 1
                greatness_details[category] = found_features
    return score, json.dumps(greatness_details)

# Database setup
conn = sqlite3.connect('listings.db')
cursor = conn.cursor()

# Create "listings" table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS listings (
        id INTEGER PRIMARY KEY,
        property_id INTEGER,
        url TEXT UNIQUE, 
        address TEXT,
        suburb TEXT,
        property_type TEXT,
        price INTEGER, 
        heading TEXT,
        bedrooms INTEGER, 
        bathrooms INTEGER,
        parking INTEGER, 
        features TEXT,
        description TEXT,
        date_available TEXT,
        bond INTEGER,
        images_path TEXT,
        date_added DATE,
        greatness_score INTEGER,
        greatness_details TEXT
    );
''')

# Create "favorites" table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY,
        listing_id INTEGER,
        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        positive_notes TEXT,
        negative_notes TEXT
    );
''')

# Function to check if a listing with a given URL already exists in the database
def listing_exists(url):
    cursor.execute("SELECT COUNT(*) FROM listings WHERE url = ?", (url,))
    count = cursor.fetchone()[0]
    return count > 0

# Extract suburb from address using the Sydney suburbs list
def extract_suburb_from_address(address):
    # Remove numerical characters (postcode)
    address = re.sub(r'\d', '', address)
    for suburb in SYDNEY_SUBURBS:
        if suburb.lower() in address.lower():
            return suburb
    return None

# Crawl pages and get urls
def crawl_pages(url): 
    options = Options()
    driver = webdriver.Chrome(options=options)  
    driver.get(url)
    # wait = WebDriverWait(driver, 10) # Waits for 10 seconds
    property_links = driver.find_elements(By.CSS_SELECTOR, PROPERTY_PAGE_URLS_CSS_SELECTOR)
    property_urls = [link.get_attribute("href") for link in property_links]
    driver.quit()
    return property_urls

# Scrape domain listing
def scrape_domain_listing(url):
    options = Options()
    driver = webdriver.Chrome(options=options)  # replace './chromedriver' with your chromedriver path
    driver.get(url)
    # time.sleep(1)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    images = driver.execute_script('return digitalData.page.pageInfo.property.images')
    
    # Extract property_id
    parsed_url = urlparse(url)
    property_id = parsed_url.path.split('-')[-1]

    # Click 'Read more' button to expand description
    # wait = WebDriverWait(driver, 5)
    # wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="listing-details__description-button"]')))
    read_more_button = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="listing-details__description-button"]')
    driver.execute_script("arguments[0].click();", read_more_button)

    # Wait for page to load updated content 
    # time.sleep(1) 
    soup = BeautifulSoup(driver.page_source, 'html.parser') 

    # Property Features
    try: 
        features = ', '.join([str(feature.get_text()) for feature in soup.find(id='property-features').find_all('li')])

    except AttributeError:
        features = None

    print(f"Features found: {features}")

    # Address
    address = soup.find("div", {"data-testid":"listing-details__button-copy-wrapper"}).h1.get_text()
    suburb = extract_suburb_from_address(address)

    print(f"Suburb found: {suburb}")

    # Price
    price_div = soup.find("div", {"data-testid":"listing-details__summary-title"}).get_text()
    # Extract the price from the string
    price_matches = re.findall(r'\$[\d,.]+', price_div)
    # If a price was found, remove the dollar sign and comma, and convert to a float, otherwise use None
    price = float(price_matches[0].replace('$', '').replace(',', '')) if price_matches else None

    print(f"Price found: {price}")

    # Bedrooms, Bathrooms and Parking
    main_features = soup.find_all("span", {"data-testid":"property-features-feature"})
    bedrooms = main_features[0].get_text()
    bedrooms = int(re.search(r'\d+', bedrooms).group()) if re.search(r'\d+', bedrooms) else 0 # extract number
    bathrooms = main_features[1].get_text()
    bathrooms = int(re.search(r'\d+', bathrooms).group()) if re.search(r'\d+', bathrooms) else 0 # extract number
    parking = main_features[2].get_text()
    parking = int(re.search(r'\d+', parking).group()) if re.search(r'\d+', parking) else 0 # extract number

    print(f"Bedrooms found: {bedrooms}")
    print(f"Bathrooms found: {bathrooms}")
    print(f"Parking found: {parking}")

    # Date Available and Bond 
    summary_strip = soup.find_all("li")
    date_available = None
    bond = None
    for li in summary_strip:
        if 'date available' in li.text.lower() or 'available from' in li.text.lower(): 
            try:
                date_available = li.find('strong').text
            except AttributeError:
                date_available = None
        elif 'bond' in li.text.lower():
            try:
                bond_text = li.text.lower()
                if 'bond' in bond_text and '$' in bond_text:  
                    bond = li.find('strong').text
                    # Extract numbers and decimal point from the bond string
                    bond = re.findall(r'\d+\.?\d*', bond)
                    # Join the numbers and convert to a float
                    bond = float(''.join(bond)) if bond else 0
            except AttributeError:
                bond = None

    print(f"Date available found: {date_available}")
    print(f"Bond available found: {bond}")
    
    # Property type
    property_type_element = soup.find("div", {"data-testid": "listing-summary-property-type"})
    property_type = property_type_element.get_text().strip() if property_type_element else None

    print(f"Property type found: {property_type}")

    # Full description
    description_section = soup.find("div", {"data-testid":"listing-details__description"})

    # Modified Heading Extraction (Now looking for <h3> tag)
    original_heading = description_section.find('h3')
    heading = original_heading.text.title() if original_heading else None

    print(f"Description heading found: {heading}")

    # Formatting <br> and <p> tags (Unchanged)
    for br in description_section.find_all("br"):
        br.replace_with("\\n")
    for p in description_section.find_all("p"):
        p.replace_with('\\n\\n' + p.text)

    # Description reformatting (Unchanged)
    main_text = description_section.get_text(separator='\\n', strip=True)
    lines = main_text.split('\\n')
    clean_lines = [line.strip() for line in lines if line.strip()]
    description = '\\n\\n'.join(clean_lines)

    # Remove heading and property type from description (Updated for new HTML structure)
    if heading:
        description = description.replace(heading, '')
    description = description.replace("Property Description", '')
    description = description.replace("Read less", '')
    # Assuming property_type is defined elsewhere in the script
    if 'property_type' in globals() and property_type:
        description = description.replace("Property type: " + property_type, '') 

    # Remove empty lines at the beginning and end (Unchanged)
    description = description.strip()

    # Image storage
    dir_name = f'static/images/{property_id}'
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    for i, img_url in enumerate(images):
        urllib.request.urlretrieve(img_url, f'{dir_name}/img_{i}.jpg')

    # Resize images
    resize_images(dir_name, 800)

    driver.quit()

    return property_id, url, address, suburb, property_type, price, heading, bedrooms, bathrooms, parking, features, description, date_available, bond, dir_name

# Loop through pages, get urls and scrape details
for i in range(1, 101):
    url = START_URL if i == 1 else f"{START_URL}&page={i}" 
    urls = crawl_pages(url)
    urls_dedup = list(set(urls))
    for url in urls_dedup:
        if listing_exists(url):
            print(f"Listing {url} is already in the database. Skipping...")
            continue
        try:
            details = scrape_domain_listing(url)
            for detail in details:
                print(detail)
            greatness_score, greatness_details = calculate_greatness_score(details[10], details[11])  # features and description
            cursor.execute('''
                INSERT INTO listings (property_id, url, address, suburb, property_type, price, heading, bedrooms, bathrooms, parking, features, description, date_available, bond, images_path, date_added, greatness_score, greatness_details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*details, datetime.now(), greatness_score, greatness_details))
            conn.commit()
            print(f"Successfully inserted {details[1]}")
        except Exception as e:
            print(f"Error occurred while inserting {url}: {e}")

conn.close()
