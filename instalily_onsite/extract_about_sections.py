import csv
import time
import pandas as pd
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


def safe_get_text(element):
    try:
        return element.text.strip() if element.text else "N/A"
    except (StaleElementReferenceException, AttributeError):
        return "N/A"


def safe_navigate(driver, url, max_retries=3):
    for attempt in range(max_retries):
        try:
            print(f"Navigating to {url} (attempt {attempt+1}/{max_retries})")
            driver.get(url)
            
            # Wait for document ready state to be complete
            wait = WebDriverWait(driver, 30)
            wait.until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
            
            # Wait for the page to load
            time.sleep(3)
            
            return True
                
        except WebDriverException as e:
            print(f"Navigation error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                print("Retrying after error...")
                time.sleep(5)
            else:
                print(f"Failed to navigate to {url} after {max_retries} attempts")
                return False
    
    return False


def extract_about_section(driver, url):
    """
    Extract the About section from a contractor's page.
    
    Args:
        driver: Selenium WebDriver instance
        url: URL of the contractor's page
        
    Returns:
        str: About section text or 'N/A' if not found
    """
    about_text = "N/A"
    
    if not safe_navigate(driver, url):
        print(f"Failed to navigate to {url}. Skipping.")
        return about_text
    
    try:
        # Try to find the About section using the xpath provided
        about_element = driver.find_element(By.XPATH, "/html/body/main/section[4]/div/div/div/p")
        if about_element:
            about_text = safe_get_text(about_element)
    except NoSuchElementException:
        # If the specific xpath doesn't work, try some alternatives
        try:
            # Look for any section that might contain "About" text
            sections = driver.find_elements(By.TAG_NAME, "section")
            for section in sections:
                try:
                    # Check for headings that might indicate an about section
                    headings = section.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, h5, h6")
                    for heading in headings:
                        if "about" in safe_get_text(heading).lower():
                            # Found look for paragraph text
                            paragraphs = section.find_elements(By.TAG_NAME, "p")
                            if paragraphs:
                                about_text = "\n".join([safe_get_text(p) for p in paragraphs])
                                print(f"Found about section with heading: {safe_get_text(heading)}")
                                return about_text
                except:
                    continue
                    
            # If we still haven't found it, just look for any paragraph that might contain "about us"
            paragraphs = driver.find_elements(By.TAG_NAME, "p")
            for p in paragraphs:
                p_text = safe_get_text(p)
                if len(p_text) > 100 and ("about" in p_text.lower() or "our company" in p_text.lower()):
                    about_text = p_text
                    print("Found potential about paragraph")
                    return about_text
                    
        except Exception as e:
            print(f"Error finding alternative about section: {e}")
    
    except Exception as e:
        print(f"Error extracting about section: {e}")
    
    return about_text


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


def process_contractors_file(input_file, output_file):
    """
    Process a CSV file containing contractor information and extract about sections.
    
    Args:
        input_file: Path to the input CSV file
        output_file: Path to the output CSV file
    """
    # Read the input CSV file
    try:
        df = pd.read_csv(input_file)
        print(f"Successfully read {len(df)} contractors from {input_file}")
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    # Add a new column for about section
    df['about_section'] = 'N/A'
    
    # Set up driver
    driver = None
    try:
        print("Setting up web driver...")
        driver = setup_driver()
        
        # Handle cookie consent once at the beginning (might need to be repeated)
        first_url = df['page_link'].iloc[0] if not df.empty else None
        if first_url:
            safe_navigate(driver, first_url)
            handle_cookie_consent(driver)
        
        # Process each contractor
        for idx, row in df.iterrows():
            try:
                contractor_name = row['name']
                page_link = row['page_link']
                
                print(f"\nProcessing contractor {idx+1}/{len(df)}: {contractor_name}")
                print(f"Page link: {page_link}")
                
                # Skip if page_link is N/A or empty
                if page_link == 'N/A' or not page_link:
                    print("No page link available. Skipping.")
                    continue
                
                # Extract about section
                about_section = extract_about_section(driver, page_link)
                print(f"About section: {about_section[:100]}..." if len(about_section) > 100 else f"About section: {about_section}")
                
                # Update dataframe
                df.at[idx, 'about_section'] = about_section
                
                # Save progress after every 5 contractors
                if (idx + 1) % 5 == 0 or idx == len(df) - 1:
                    print(f"Saving progress to {output_file}...")
                    df.to_csv(output_file, index=False)
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Error processing contractor {idx+1}: {e}")
                continue
        
        # Save final results
        print(f"Saving final results to {output_file}...")
        df.to_csv(output_file, index=False)
        print(f"Successfully processed {len(df)} contractors")
        
    except Exception as e:
        print(f"Error during processing: {e}")
    
    finally:
        if driver:
            print("Closing web driver...")
            driver.quit()


if __name__ == "__main__":
    # Input and output file paths
    input_file = "gaf_roofing_contractors.csv"
    output_file = "gaf_roofing_contractors_with_about.csv"
    
    # Process contractors file
    process_contractors_file(input_file, output_file)