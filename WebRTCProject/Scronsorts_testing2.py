import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

# Ensure the screenshots directory exists
os.makedirs("screenshots", exist_ok=True)

# Function to capture the video tag screenshot
def capture_video_tag_screenshot(url, screenshot_path):
    # Start the WebDriver
    driver = webdriver.Chrome()

    try:
        # Open the URL
        driver.get(url)

        # Wait for the video element to load
        video_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "video"))
        )

        # Get the outer HTML of the video element (i.e., <video> tag)
        video_html = video_element.get_attribute("outerHTML")
        print("Video tag HTML:", video_html)  # Display the <video> tag in the console

        # Get the position and dimensions of the video element
        video_rect = video_element.rect
        x = video_rect['x']
        y = video_rect['y']
        width = video_rect['width']
        height = video_rect['height']

        # Ensure valid dimensions are available
        if width > 0 and height > 0:
            print(f"Video dimensions: {width}x{height} at position ({x}, {y})")

            # Set the browser window size to match the video element size
            driver.set_window_size(width + x, height + y)  # Adjust window size

            # Take a screenshot of the video element
            video_element.screenshot(screenshot_path)
            print(f"Screenshot of video element saved at: {screenshot_path}")
        else:
            print("Video dimensions are not available (width or height is zero).")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Quit the WebDriver
        driver.quit()


# URL of the webpage
url = "https://webrtc.github.io/samples/src/content/getusermedia/resolution/"

# Path to save the screenshot
screenshot_path = os.path.join("screenshots", "video-tag-screenshot.png")

# Call the function
capture_video_tag_screenshot(url, screenshot_path)
