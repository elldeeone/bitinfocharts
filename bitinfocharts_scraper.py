from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
import time
import pytesseract
from PIL import Image
import io
import numpy as np
import cv2
from io import BytesIO
import re

def get_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-notifications')
    options.add_argument('--start-maximized')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')
    return options

def draw_debug_rectangle(image, crop_coords, filename):
    """Draw a red rectangle on the screenshot to show capture area"""
    debug_img = image.copy()
    debug_img_cv = cv2.cvtColor(np.array(debug_img), cv2.COLOR_RGB2BGR)
    
    # Draw rectangle (left, top, right, bottom)
    cv2.rectangle(
        debug_img_cv,
        (crop_coords[0], crop_coords[1]),
        (crop_coords[2], crop_coords[3]),
        (0, 0, 255),  # Red in BGR
        2  # Thickness
    )
    
    cv2.imwrite(filename, debug_img_cv)

def scrape_crypto_transactions(url, coin_name, output_filename):
    driver = None
    try:
        print(f"\nStarting {coin_name} transaction scraping...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=get_chrome_options()
        )
        
        # Maximize the window
        driver.maximize_window()
        
        print(f"Navigating to {coin_name} page...")
        driver.get(url)
        
        print("Waiting for initial page load...")
        time.sleep(5)
        
        # Find the chart container
        container = driver.find_element(By.ID, "container")
        
        # Create ActionChains instance
        actions = ActionChains(driver)
        
        # Move to starting position with updated offset
        print("Moving to starting position...")
        actions.move_to_element_with_offset(container, -800, 0).perform()
        time.sleep(1)
        
        data_points = []
        
        steps = 120
        for i in range(steps):
            try:
                print(f"Movement {i+1}/{steps}")
                actions.move_by_offset(15, 0).perform()
                time.sleep(0.4)
                
                screenshot = driver.get_screenshot_as_png()
                image = Image.open(BytesIO(screenshot))
                
                # Updated crop settings
                cropped = image.crop((130, 500, 800, 600))
                cropped = cropped.resize((1340, 200), Image.Resampling.LANCZOS)  # Adjusted for new width
                
                opencv_image = cv2.cvtColor(np.array(cropped), cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
                threshold = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)[1]
                
                text = pytesseract.image_to_string(threshold, config='--psm 6')
                
                if text:
                    print(f"Raw OCR text: {text}")
                    # Adjust search string based on cryptocurrency
                    search_text = f"{coin_name} - Transactions:"
                    if search_text in text:
                        print(f"Found transaction data: {text}")
                        data_points.append(text)
                
            except Exception as e:
                print(f"Error during movement {i}: {e}")
                continue

        if not data_points:
            raise Exception(f"No data points were collected for {coin_name}")
            
        print(f"Collected {len(data_points)} data points for {coin_name}")
        
        # Parse the collected data
        parsed_data = []
        for point in data_points:
            try:
                print(f"Parsing point: {point}")
                point = point.replace('\n', ' ').strip()
                
                date_match = re.search(r'[29]024/[01]\d/\d{2}', point)
                if date_match:
                    date_str = date_match.group(0).replace('9024', '2024')
                    
                    transactions_match = re.search(r'Transactions:\s*([0-9,.]+)k', point)
                    if transactions_match:
                        value_str = transactions_match.group(1)
                        value_str = value_str.replace(' ', '').replace(',', '')
                        try:
                            value = float(value_str)
                            transactions = value * 1000
                            
                            timestamp = pd.to_datetime(date_str).timestamp() * 1000
                            parsed_data.append([timestamp, transactions])
                            print(f"Successfully parsed: Date={date_str}, Transactions={transactions:,.0f}")
                        except ValueError:
                            print(f"Could not convert value: {value_str}")
                    else:
                        print(f"Could not find transaction value in: {point}")
                else:
                    print(f"Could not find valid date in: {point}")
                
            except Exception as e:
                print(f"Failed to parse data point: {point}")
                print(f"Error: {str(e)}")
                continue
        
        print("Creating DataFrame...")
        df = pd.DataFrame(parsed_data, columns=['timestamp', 'transactions'])
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        df = df.drop_duplicates(subset=['date', 'transactions']).sort_values('date')
        final_df = df[['date', 'transactions']]
        
        final_df.to_csv(output_filename, index=False)
        
        print(f"\nData saved to {output_filename}")
        print(f"Sample of collected data for {coin_name}:")
        print(final_df)
        
        return df

    except Exception as e:
        print(f"Error scraping {coin_name}: {str(e)}")
        return None
        
    finally:
        if driver:
            driver.quit()

def main():
    # Define the cryptocurrencies to scrape
    cryptos = [
        {
            'name': 'Bitcoin',
            'url': 'https://bitinfocharts.com/comparison/bitcoin-transactions.html#3m',
            'output': 'bitcoin_transactions.csv'
        },
        {
            'name': 'Litecoin',
            'url': 'https://bitinfocharts.com/comparison/litecoin-transactions.html#3m',
            'output': 'litecoin_transactions.csv'
        },
        {
            'name': 'Ethereum Classic',
            'url': 'https://bitinfocharts.com/comparison/transactions-etc.html#3m',
            'output': 'ethereum_classic_transactions.csv'
        },
        {
            'name': 'Bitcoin Cash',
            'url': 'https://bitinfocharts.com/comparison/transactions-bch.html#3m',
            'output': 'bitcoin_cash_transactions.csv'
        },
        {
            'name': 'Dogecoin',
            'url': 'https://bitinfocharts.com/comparison/dogecoin-transactions.html#3m',
            'output': 'dogecoin_transactions.csv'
        },
    ]
    
    # Scrape each cryptocurrency
    for crypto in cryptos:
        try:
            print(f"\n{'='*50}")
            print(f"Processing {crypto['name']}")
            print(f"{'='*50}")
            
            scrape_crypto_transactions(
                url=crypto['url'],
                coin_name=crypto['name'],
                output_filename=crypto['output']
            )
            
            print(f"Completed {crypto['name']} processing")
            time.sleep(5)  # Wait between cryptocurrencies
            
        except Exception as e:
            print(f"Failed to process {crypto['name']}: {str(e)}")
            continue

if __name__ == "__main__":
    print("Starting cryptocurrency transaction scraper...")
    main()
    print("\nScript completed!")
