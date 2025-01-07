# # Import the required library    visible-part-of-screen.png
# import time
#
# from selenium import webdriver
# import os
#
# # Create a folder for screenshots if it doesn't exist
# os.makedirs("screenshots", exist_ok=True)
#
# # Start a WebDriver instance (make sure ChromeDriver is in your PATH or provide its full path)
# driver = webdriver.Chrome()
#
#
# try:
#     # Visit the target page
#     driver.get("https://webrtc.github.io/samples/src/content/getusermedia/resolution/")
#     time.sleep(5)
#
#     # Take a screenshot of the visible part
#     screenshot_path = "visible-part-of-screen.png"
#     driver.save_screenshot(screenshot_path)
#     print(f"Screenshot saved at {screenshot_path}")
#
# finally:
#     # Quit the driver
#     driver.quit()






# import time
#
# from selenium import webdriver
#
# from selenium.webdriver.common.by import By
# import os
#
#
# os.makedirs("screenshots", exist_ok=True)
#
# driver = webdriver.Chrome()
#
#
# try:
#     # Open the target website
#     driver.get("https://webrtc.github.io/samples/src/content/getusermedia/resolution/")
#     time.sleep(7)
#
#     # Define a function to get scroll dimensions
#     def get_scroll_dimension(axis):
#         return driver.execute_script(f"return document.body.parentNode.scroll{axis}")
#
#     # Get the page scroll dimensions
#     width = get_scroll_dimension("Width")
#     height = get_scroll_dimension("Height")
#
#     # Set the browser window size
#     driver.set_window_size(width, height)
#
#     # Get the full body element
#     # full_body_element = driver.find_element(By.TAG_NAME, "body")
#     full_video_element = driver.find_element(By.TAG_NAME, "video")
#
#
#     # Take a full-page screenshot
#     screenshot_path = "selenium-full-page-screenshot.png"
#     full_video_element.screenshot(screenshot_path)
#     print(f"Full-page screenshot saved at {screenshot_path}")
#
# finally:
#     # Quit the browser
#     driver.quit()


import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import os

# Ensure the screenshots directory exists
os.makedirs("screenshots", exist_ok=True)

# Start the WebDriver instance
driver = webdriver.Chrome()

try:
    # Open the target website
    driver.get("https://webrtc.github.io/samples/src/content/getusermedia/resolution/")
    time.sleep(7)  # Allow the video element to load fully

    # Locate the <video> element by tag name
    video_element = driver.find_element(By.TAG_NAME, "video")

    # Check if the element was found
    if video_element:
        print("Video tag found:", video_element.get_attribute("outerHTML"))

        # Take a screenshot of the video element
        screenshot_path = "screenshots/video-element-screenshot.png"
        video_element.screenshot(screenshot_path)
        print(f"Screenshot of video element saved at {screenshot_path}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Quit the browser
    driver.quit()

