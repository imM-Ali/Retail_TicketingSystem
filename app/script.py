import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

# Define the database model
Base = declarative_base()

category_urls = {
        
            'Dining Tables': 'https://www.harveynorman.ie/furniture/dining-furniture/dining-tables/',
            'Dining Chairs': 'https://www.harveynorman.ie/furniture/dining-furniture/dining-chairs/',
            'Bar Stools and Bar Tables': 'https://www.harveynorman.ie/furniture/dining-furniture/bar-stools-and-bar-tables/',
            'Benches': 'https://www.harveynorman.ie/furniture/dining-furniture/benches/',
            'Office Desks': 'https://www.harveynorman.ie/furniture/home-office-en-2/office-desks/',
            'Office Chairs': 'https://www.harveynorman.ie/furniture/home-office-en-2/office-chairs/',
            'Bookcases and Display Cabinets': 'https://www.harveynorman.ie/furniture/cabinets-and-storage/bookcases-and-display-cabinets/',
            'Coffee Tables': 'https://www.harveynorman.ie/furniture/occasional-furniture/coffee-tables/',
            'Lamp Tables': 'https://www.harveynorman.ie/furniture/occasional-furniture/lamp-tables/',
            'Console Tables': 'https://www.harveynorman.ie/furniture/occasional-furniture/console-tables/',
            'Nests of Tables': 'https://www.harveynorman.ie/furniture/occasional-furniture/nests-of-tables/',
            'Assorted Occasional': 'https://www.harveynorman.ie/furniture/occasional-furniture/assorted-occasional/',
            'Sideboards': 'https://www.harveynorman.ie/furniture/cabinets-and-storage/side-boards/',
            'Display Cases': 'https://www.harveynorman.ie/furniture/cabinets-and-storage/display-cases/',
            'TV Units': 'https://www.harveynorman.ie/furniture/cabinets-and-storage/tv-units/',
            'Outdoor Dining and Living': 'https://www.harveynorman.ie/furniture/outdoor-dining-and-living/all-outdoor-dining-and-living-en/',
            'Gaming Desks and Chairs': 'https://www.harveynorman.ie/furniture/gaming-desks-and-chairs-en/',
            'Corner Sofas': 'https://www.harveynorman.ie/sofas/corner-sofas/',
            'Fabric Sofas': 'https://www.harveynorman.ie/sofas/fabric-sofas/',
            'Sofa Beds': 'https://www.harveynorman.ie/sofas/sofabeds/',
            'Chairs and Footstools': 'https://www.harveynorman.ie/sofas/chairs-and-footstools/',
            'Leather Sofas': 'https://www.harveynorman.ie/sofas/leather-sofas/',
            'Recliner Sofas': 'https://www.harveynorman.ie/sofas/recliner-sofas/'
}

class Product(Base):
    __tablename__ = 'product'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(249))
    original_price = Column(String(249))
    discounted_price = Column(String(249))
    category = Column(String(249))

#Initializing database object
engine = create_engine('sqlite:///instance/hndb.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

#Initializing Selenium
options = webdriver.EdgeOptions()
options.add_argument('headless')
driver_path = './dependencies/msedgedriver.exe'
driver = webdriver.Edge(executable_path=driver_path, options=options)

def add_product_if_not_exists(name, original_price, discounted_price, category):
    try:
        #We do not want multiple of the same products in the DB, hence only allow similar products once
        existing_product = session.query(Product).filter(
            Product.name == name,
            Product.original_price == original_price,
            Product.discounted_price == discounted_price
        ).one()
        
        #If product exists, do not add again
        return

    except NoResultFound:
        #If product does not exist, add it to database
        new_product = Product(
            name=name,
            original_price=original_price,
            discounted_price=discounted_price,
            category=category
        )
        session.add(new_product)
        session.commit()



def scrape(url, cat):
    print(f"Scraping {url}...")
    driver.get(url)
    time.sleep(2)
    try:
        reject_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, 'onetrust-reject-all-handler'))
        )
        reject_button.click()
        print("Skipped Cookies")
    except Exception as e:
        print("Cookie consent popup did not appear or 'Reject' button was not found")
    results = []
    while True:
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        products_details = soup.find_all('a', class_='product-title')
        products_prices = soup.find_all('div', class_='product-footer')

        for index, product in enumerate(products_prices):
            product_name = products_details[index].get_text(strip=True) if index < len(products_details) else 'N/A'
            
            discounted_price = product.find('span', id=re.compile(r'sec_discounted_price_\d+'))
            discounted_price_text = discounted_price.get_text(strip=True).replace('£', '').replace(',', '') if discounted_price else 'N/A'
            
            original_price = product.find('span', id=re.compile(r'sec_list_price_\d+'))
            original_price_text = original_price.get_text(strip=True).replace('£', '').replace(',', '') if original_price else 'N/A'
            
            if discounted_price_text != 'N/A' and original_price_text != 'N/A':
                add_product_if_not_exists(product_name, original_price_text, discounted_price_text, cat)

        #Automatically check the next page link
        next_page_link = soup.find('a', class_='next')
        if next_page_link and 'href' in next_page_link.attrs:
            next_page_url = next_page_link['href']
            scrape(f'https:{next_page_url}', cat)
        else:
            break

    for result in results:
            product = Product(
                name=result["Product Name"],
                original_price=result["Original Price"],
                discounted_price=result["Discounted Price"],
                category=result["Category"]
            )
            session.add(product)

  
for category, url in category_urls.items():
        scrape(url,category)

driver.quit()
session.commit()
session.close()

print("Data has been scraped and stored in the database successfully.")
