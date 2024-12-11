from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException

import time
import pandas as pd

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Specify the path to the ChromeDriver
webdriver_path = '/Users/alfiewearn/Library/CloudStorage/OneDrive-McGillUniversity/OHBM_ComCom/YouTube_Transfer/upload_api/scrape_ondemand_urls/chromedriver-mac-x64/chromedriver'

# Initialize the ChromeDriver
service = Service(webdriver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

# Navigate to the login page
login_url = "https://www.humanbrainmapping.org/i4a/ams/publiclogin.cfm?nextpage=/custom/bluesky.cfm"
driver.get(login_url)

# Log in to the system
username_input = driver.find_element(By.NAME, "username")
password_input = driver.find_element(By.NAME, "password")
username_input.send_keys("<username>")
password_input.send_keys("<password>")
password_input.send_keys(Keys.RETURN)

# Wait for login to complete
time.sleep(2)

# List of course URLs to visit after login
course_urls = [
#    "https://www.pathlms.com/ohbm/courses/45907",
    "https://www.pathlms.com/ohbm/courses/45970",
    "https://www.pathlms.com/ohbm/courses/31759",
    "https://www.pathlms.com/ohbm/courses/31757",
    "https://www.pathlms.com/ohbm/courses/15243",
    "https://www.pathlms.com/ohbm/courses/12238",
    # Add more URLs as needed
]

data = []

def toggle_download_switch():
    try:
        # Close the cookie consent dialog if it exists
        try:
            cookie_consent = driver.find_element(By.CLASS_NAME, "cc-window")
            close_cookie_consent = cookie_consent.find_element(By.CLASS_NAME, "cc-btn")
            close_cookie_consent.click()
            time.sleep(2)
        except (NoSuchElementException, ElementNotInteractableException):
            print("No cookie window")
            pass  # Ignore if the cookie consent dialog doesn't exist

        # Retry mechanism for clicking the 'Edit' button
        retries = 3
        for attempt in range(retries):
            try:
                edit_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a.edit[data-role='edit-show']"))
                )
                driver.execute_script("arguments[0].click();", edit_button)
                time.sleep(2)  # Wait for the pop-up to appear

                # Check that the Advanced tab is visible as a sign the edit window is open
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "a[data-toggle='tab'][href='#presentation-advanced-content']"))
                )
                print("Edit window successfully opened.")
                break  # Exit the retry loop if successful
            except (ElementClickInterceptedException, ElementNotInteractableException, NoSuchElementException) as e:
                print(f"Attempt {attempt + 1} to open the Edit window failed: {e}")
                if attempt == retries - 1:
                    raise Exception("Failed to open the Edit window after several attempts. Reloading page.")
                driver.refresh()
                time.sleep(2)  # Wait after page refresh
            except Exception as e:
                print(f"An error occurred while opening the Edit window: {e}")
                traceback.print_exc()  # Print the full stack trace to help with debugging

        # Click on the 'Advanced' tab using JavaScript
        advanced_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-toggle='tab'][href='#presentation-advanced-content']"))
        )
        driver.execute_script("arguments[0].click();", advanced_tab)
        time.sleep(1)

        # Scroll to the download switch to ensure it is visible
        toggle_input = driver.find_element(By.ID, "presentation_downloadable")
        driver.execute_script("arguments[0].scrollIntoView(true);", toggle_input)
        time.sleep(1)

        # Check the state of the toggle switch by inspecting if the checkbox is selected
        is_checked = toggle_input.is_selected()
        print(f"Download toggle switch current state: {is_checked}")

        if not is_checked:
            print("Attempting to toggle the download switch...")
            driver.execute_script("arguments[0].click();", toggle_input)
            time.sleep(1)

            # Re-check if the toggle was successful
            is_checked_after = toggle_input.is_selected()
            print(f"Download toggle switch new state: {is_checked_after}")
            if not is_checked_after:
                raise Exception("Failed to toggle the download switch.")
        
        # Scroll to the Update button and use JavaScript to click it
        update_button = driver.find_element(By.ID, "submit-presentation")
        driver.execute_script("arguments[0].scrollIntoView(true);", update_button)
        driver.execute_script("arguments[0].click();", update_button)
        time.sleep(1)  # Wait for the pop-up to close and the page to reload

        print("Download switch enabled and presentation updated.")
    except NoSuchElementException as e:
        print(f"Element not found: {e}")
    except Exception as e:
        print(f"An error occurred while toggling the download switch: {e}")

def extract_videos_from_page(page_url, video_title, course_title, session_title="NA"):
    # Reload the page each time to ensure a fresh state
    driver.get(page_url)
    time.sleep(2)

    # Toggle the download switch before attempting to download
    toggle_download_switch()

    # Extract video URL
    try:
        video_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@data-role='download-video-link']"))
        )
        video_url = video_element.get_attribute("href")
    except:
        video_url = None
    
    # Extract Contributor text
    try:
        names_elements = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[@data-role='remove-contributor']"))
        )
        # Check if multiple elements are found
        if isinstance(names_elements, list):
            names = ', '.join([elem.get_attribute("data-name") for elem in names_elements])
        else:
            names = names_elements.get_attribute("data-name")
    #        names = names_element.get_attribute("data-name")
    except Exception as e:
        names = None
        print(f"Could not extract contributor names: {e}")
    print(f"Names: {names}")
    
    # Store the data
    data.append({
        'course_title': course_title,
        'session_title': session_title,
        'video_title': video_title,
        'contributors': names,
        'video_url': video_url
    })

def process_session_page(session_url, course_title, session_title):
    driver.get(session_url)
    time.sleep(2)
    
    video_page_links = driver.find_elements(By.CLASS_NAME, "course_item_el")  # Locate all video links within the session
    
    video_links_fixed = []
    for link in video_page_links:
        video_links_fixed.append({
            'title': link.get_attribute("title"),
            'href': link.get_attribute("href")
        })
    
    for i, video in enumerate(video_links_fixed):
        video_page_url = video['href']
        video_page_name = video['title']
        print(f"Video page name: {video_page_name}")
        extract_videos_from_page(video_page_url, video_page_name, course_title, session_title)

def process_course_page(course_url):
    driver.get(course_url)
    time.sleep(2)
    
    # Extract the content from the <title> tag
    try:
        course_title = driver.title.strip()
    except:
        course_title = "Unknown Page Title"
    print(f"Course page title: {course_title}")
    
    # Identify all sections and presentations
    items = driver.find_elements(By.CLASS_NAME, "course_item_el")

    item_links_fixed = []
    for item in items:
        item_links_fixed.append({
            'title': item.get_attribute("title"),
            'href': item.get_attribute("href"),
            'class': item.get_attribute("class")
        })
        
    for i, item in enumerate(item_links_fixed):
        item_title = item['title']
        item_class = item['class']
        item_href = item['href']

        # Force reload to avoid stale elements
        driver.get(course_url)
        time.sleep(2)
        
        # Check if it's a session (Section)
        if "section" in item_class:
            session_title = item_title.strip()
            print(f"Processing session: {session_title}")
            process_session_page(item_href, course_title, session_title)
        elif "presentation" in item_class:  # Directly a video link
            video_page_url = item_href
            video_page_name = item_title.strip()
            print(f"Processing Video: {video_page_name}")
            extract_videos_from_page(video_page_url, video_page_name, course_title)

# Loop through each course URL
for course_url in course_urls:
    process_course_page(course_url)

# Save the data
df = pd.DataFrame(data)
df.to_csv('video_info.csv', index=False)
df.to_excel('video_info.xlsx', index=False)

print("Data extraction complete. Saved to video_info.csv and video_info.xlsx.")
driver.quit()
