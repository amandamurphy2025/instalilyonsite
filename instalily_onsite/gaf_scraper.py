import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, NoSuchElementException, WebDriverException


def wait_and_find_element(driver, by, value, timeout=10):
    wait = WebDriverWait(driver, timeout)
    try:
        element = wait.until(EC.presence_of_element_located((by, value)))
        return element
    except (TimeoutException, StaleElementReferenceException):
        return None


def wait_and_find_elements(driver, by, value, timeout=10):
    wait = WebDriverWait(driver, timeout)
    try:
        elements = wait.until(EC.presence_of_all_elements_located((by, value)))
        return elements
    except (TimeoutException, StaleElementReferenceException):
        return []


def safe_get_text(element):
    try:
        return element.text.strip() if element.text else "N/A"
    except (StaleElementReferenceException, AttributeError):
        return "N/A"


def safe_get_attribute(element, attribute):
    try:
        return element.get_attribute(attribute) if element else "N/A"
    except (StaleElementReferenceException, AttributeError):
        return "N/A"


def safe_navigate(driver, url, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"Navigating to {url} (attempt {attempt+1}/{max_retries})")
            driver.get(url)
            
            wait = WebDriverWait(driver, 30)
            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.contractor-listing__results")))
                print(f"Page loaded successfully: {url}")
                return True
            except TimeoutException as e:
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(5)
                continue
                
        except WebDriverException as e:
            if attempt < max_retries - 1:
                print("Retrying after error...")
                time.sleep(5)
            else:
                print(f"Failed to navigate to {url}")
                return False
    
    return False


def scrape_contractor_info(driver, base_url, max_pages=10):
    """
    Scrape contractor information from the GAF website.
    
    Args:
        driver: Selenium WebDriver instance
        base_url: The base URL to start scraping from
        max_pages: Maximum number of pages to scrape
        
    Returns:
        list: List of dictionaries containing contractor information
    """
    contractors_data = []
    
    # Navigate to the base URL
    if not safe_navigate(driver, base_url):
        print(f"Failed to navigate to {base_url}. Exiting.")
        return contractors_data
    
    # Process multiple pages
    current_page = 1
    while current_page <= max_pages:
        print(f"\nProcessing page {current_page}/{max_pages}")
        
        # Wait for contractor listing to load
        contractor_items = wait_and_find_elements(driver, By.CSS_SELECTOR, "ul.contractor-listing__results > li")
        if not contractor_items:
            print("No contractor items found on this page.")
            break
        
        print(f"Found {len(contractor_items)} contractors on page {current_page}")
        
        # Process each contractor on the current page
        for idx, item in enumerate(contractor_items, 1):
            try:
                print(f"Processing contractor {idx}/{len(contractor_items)}")
                
                # Create a dictionary to store contractor information
                contractor_data = {
                    'name': 'N/A',
                    'page_link': 'N/A',
                    'rating_stars': 'N/A',
                    'certifications': 'N/A',
                    'phone_number': 'N/A'
                }
                
                # Extract name and page link
                try:
                    name_element = item.find_element(By.CSS_SELECTOR, "div.certification-card__content > div:nth-child(1) > h2 > a > span")
                    link_element = item.find_element(By.CSS_SELECTOR, "div.certification-card__content > div:nth-child(1) > h2 > a")
                    
                    if name_element:
                        contractor_data['name'] = safe_get_text(name_element)
                    if link_element:
                        contractor_data['page_link'] = safe_get_attribute(link_element, "href")
                except NoSuchElementException:
                    print("Could not find name or link element")
                
                # Extract rating stars
                try:
                    stars_element = item.find_element(By.CSS_SELECTOR, "div.certification-card__content > div:nth-child(1) > div > span.rating-stars__average")
                    if stars_element:
                        contractor_data['rating_stars'] = safe_get_text(stars_element)
                except NoSuchElementException:
                    print("Could not find rating stars element")
                
                # Extract certifications
                try:
                    cert_elements = item.find_elements(By.CSS_SELECTOR, "div.certification-card__certifications > ul > li")
                    if cert_elements:
                        certifications = [safe_get_text(cert) for cert in cert_elements if safe_get_text(cert) != "N/A"]
                        contractor_data['certifications'] = ', '.join(certifications) if certifications else "N/A"
                except:
                    print("Could not find certification elements")
                
                # Extract phone number
                try:
                    # Try to find the phone number in the certification-card__phone element
                    phone_element = item.find_element(By.CSS_SELECTOR, "a.certification-card__phone")
                    if phone_element:
                        # Get the text directly from this element without the SVG icon text
                        phone_text = phone_element.text
                        # Filter out the "Phone Number:" text
                        if "Phone Number:" in phone_text:
                            phone_text = phone_text.replace("Phone Number:", "").strip()
                        contractor_data['phone_number'] = phone_text
                except NoSuchElementException:
                    try:
                        # Alternative selector, trying to find any phone number link
                        phone_element = item.find_element(By.XPATH, ".//a[contains(@href, 'tel:')]")
                        if phone_element:
                            contractor_data['phone_number'] = phone_element.text.replace("Phone Number:", "").strip()
                    except NoSuchElementException:
                        print("Could not find phone number element")
                
                # Add the contractor data to the list
                contractors_data.append(contractor_data)
                print(f"Added contractor: {contractor_data['name']}")
                print(f"Phone number: {contractor_data['phone_number']}")
                
            except Exception as e:
                print(f"Error processing contractor {idx}: {e}")
                continue
        
        # Check if there is a next page
        try:
            # Try to find the next button by looking for both potential positions
            next_button = None
            
            # Try nth-child(9) first
            try:
                next_button = driver.find_element(By.CSS_SELECTOR, "ul.pagination > li:nth-child(9) > button")
            except NoSuchElementException:
                pass
            
            # If not found, try nth-child(8)
            if not next_button:
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "ul.pagination > li:nth-child(8) > button")
                except NoSuchElementException:
                    pass
            
            # If still not found, try looking for a button with a specific aria-label or class
            if not next_button:
                try:
                    next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next'], button.coveo-pager-next")
                except NoSuchElementException:
                    pass
            
            # check if it's enabled before clicking
            if next_button:
                # Check if the button is enabled
                button_disabled = safe_get_attribute(next_button, "disabled")
                
                if button_disabled != "true" and current_page < max_pages:
                    print("Clicking next page button...")
                    driver.execute_script("arguments[0].click();", next_button)
                    print("Navigating to next page...")
                    
                    # Wait for the page to load
                    time.sleep(5)
                    
                    # Wait for the loading indicator to disappear (if there is one)
                    try:
                        WebDriverWait(driver, 10).until_not(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".coveo-processing-animation"))
                        )
                    except:
                        pass
                    
                    # Wait for contractor listing to load again
                    wait = WebDriverWait(driver, 30)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.contractor-listing__results")))
                    
                    # Increment the page counter
                    current_page += 1
                else:
                    print("Next page button is disabled or max pages reached. Stopping pagination.")
                    break
            else:
                print("Could not find next page button. Stopping pagination.")
                break
                
        except Exception as e:
            print(f"Error navigating to next page: {e}")
            break
    
    return contractors_data


def setup_driver():
    """
    Set up and return a configured Chrome driver.
    
    Returns:
        webdriver.Chrome: Configured Chrome driver
    """
    try:
        print("Setting up Chrome options...")
        chrome_options = Options()
        
        # Configure options
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Add page load strategy
        chrome_options.page_load_strategy = 'normal'
        
        print("Initializing Chrome driver...")
        driver = webdriver.Chrome(options=chrome_options)
        print("Chrome driver initialized successfully")
        
        # Set longer page load timeout
        print("Setting page load timeout...")
        driver.set_page_load_timeout(60)
        
        # Set script timeout
        driver.set_script_timeout(30)
        
        return driver
    except Exception as e:
        print(f"Failed to create driver: {str(e)}")
        print("Please ensure Chrome is installed and chromedriver is in your PATH")
        raise


def save_to_csv(contractors_data, filename):
    """
    Save the contractors data to a CSV file.
    
    Args:
        contractors_data: List of dictionaries containing contractor information
        filename: Name of the CSV file to save to
    """
    if not contractors_data:
        print("No data to save.")
        return
    
    try:
        # Get the fieldnames from the first dictionary
        fieldnames = contractors_data[0].keys()
        
        # Write to CSV file
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(contractors_data)
        
        print(f"Successfully saved {len(contractors_data)} contractors to {filename}")
    
    except Exception as e:
        print(f"Error saving to CSV: {e}")


def handle_cookie_consent(driver):
    """Handle cookie consent popup if it appears"""
    try:
        cookie_accept_button = wait_and_find_element(
            driver, 
            By.CSS_SELECTOR, 
            "button.cookie-banner__button, button#onetrust-accept-btn-handler", 
            timeout=5
        )
        if cookie_accept_button:
            print("Accepting cookies...")
            cookie_accept_button.click()
            time.sleep(1)
    except Exception as e:
        print(f"Note: Cookie handling failed or wasn't needed: {e}")


def handle_location_popup(driver):
    """Handle location popup if it appears"""
    try:
        # Wait for location popup
        location_input = wait_and_find_element(
            driver, 
            By.CSS_SELECTOR, 
            "input#location-input", 
            timeout=5
        )
        if location_input:
            print("Location popup detected. Entering location...")
            # Enter zip code
            location_input.clear()
            location_input.send_keys("10001")
            
            # Click search button
            search_button = driver.find_element(By.CSS_SELECTOR, "button.location-search__button")
            if search_button:
                search_button.click()
                # Wait for results to load
                time.sleep(3)
    except Exception as e:
        print(f"Note: Location handling failed or wasn't needed: {e}")


if __name__ == "__main__":
    # Base URL for GAF roofing contractors
    base_url = "https://www.gaf.com/en-us/roofing-contractors/residential?distance=25"
    
    # Set up driver
    driver = None
    try:
        print("Setting up web driver...")
        driver = setup_driver()
        
        # Scrape contractor information
        print("Starting contractor information scraping...")
        
        # Navigate to base URL
        if safe_navigate(driver, base_url):
            # Handle cookie consent popup if it appears
            handle_cookie_consent(driver)
            
            # Handle location popup if it appears
            handle_location_popup(driver)
            
            # Scrape contractor information - adjust max_pages to control how many pages to scrape
            contractors_data = scrape_contractor_info(driver, base_url, max_pages=20)
            
            # Save to CSV
            save_to_csv(contractors_data, "gaf_roofing_contractors.csv")
            
            print(f"Scraping completed. Total contractors found: {len(contractors_data)}")
        
    except Exception as e:
        print(f"Error during scraping: {e}")
    
    finally:
        if driver:
            print("Closing web driver...")
            driver.quit()