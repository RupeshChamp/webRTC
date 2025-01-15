import os
import cv2
from selenium import webdriver
from selenium.webdriver import ActionChains, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
import time
from Camera_Test_Automation_API import Camera_api as ca
from datetime import datetime

def get_valid_camera_index(camera_name):
    """
    Finds the index of the camera matching the specified camera name.

    Returns:
        int: The index of the camera if found, otherwise -1.
    """
    import cv2 as cv
    import gc

    cap = cv.VideoCapture()
    devices = cap.getDevices()
    for i in range(devices[1]):
        if camera_name == cap.getDeviceInfo(i)[1]:
            cap.release()
            del cap
            gc.collect()
            return i
    cap.release()
    del cap
    gc.collect()
    return -1


def get_usb_camera_resolutions(camera_index):
    ret, value = ca.assign_camera(camera_index)
    if ret:
        supported_resolutions = ca.get_supported_resolution(camera_index)
        print(supported_resolutions)
        unique_resolutions = sorted({(width, height) for _, width, height, _ in supported_resolutions[0]})
        print("Unique resolutions supported by the camera:", unique_resolutions)
        ca.release_camera(camera_index)
        return unique_resolutions, True
    else:
        error_description, _ = ca.get_error_description(value)
        return error_description, False


def map_resolutions_to_webrtc(usb_resolutions, webrtc_resolutions):
    return [res for res in usb_resolutions if res in webrtc_resolutions.keys()]


def log_web_rtc_errors(driver):
    """
    Capture error messages or logs from the WebRTC page.
    """
    if "firefox" in driver.capabilities["browserName"].lower():
        print("Browser logs are not supported for Firefox. Skipping...")
        return
    else:
        logs = driver.get_log("browser")
        for entry in logs:
            print(f"WebRTC Log: {entry['message']}")


def is_stream_active(driver, screenshot_path=None):
    """
    Confirm that the stream is active on the WebRTC page by checking the video element.
    If a screenshot path is provided, captures a screenshot of the video element.

    Args:
        driver: Selenium WebDriver instance.
        screenshot_path (str): Path to save the screenshot. Optional.

    Returns:
        tuple: (bool, str) - True if the stream is active, otherwise False.
               The timestamp (in HH:MM:SS:MS format) when the stream became active, or None if it failed.
    """
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        while True:
            if video_element.is_displayed():
                stream_start_time = datetime.now().strftime("%H:%M:%S:%f")[:-3]  # Format with milliseconds
                print("Stream is active.")
                return True, stream_start_time
    except Exception as e:
        print(f"Stream check failed: {e}")
    return False, None


def capture_full_video_frame(driver, base_path):
    """
    Captures the full video frame from the video element using a canvas and saves it with a precise timestamp.

    Args:
        driver: Selenium WebDriver instance.
        base_path: Base path to save the captured image. The function appends a timestamp to the filename.
    """
    script = """
        const video = document.querySelector('video');
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        return canvas.toDataURL('image/png');
    """
    try:
        # Capture the timestamp immediately before executing the script
        now = datetime.now()
        timestamp = now.strftime("%H_%M_%S") + f"_{now.microsecond // 1000:02d}"  # Format with exactly 3 digits for milliseconds

        # Construct the full save path with the timestamp
        save_path = f"{base_path}_{timestamp}.png"

        # Execute the JavaScript to capture the video frame
        base64_image = driver.execute_script(script)

        # Decode the base64 image and save it to the specified path
        import base64
        with open(save_path, "wb") as file:
            file.write(base64.b64decode(base64_image.split(",")[1]))

        print(f"Full video frame saved to {save_path} at {timestamp}")

        return save_path  # Optionally return the save path
    except Exception as e:
        print(f"Failed to capture full video frame: {e}")
        return None


def stream_camera_in_resolution(driver, resolution, webrtc_resolutions, duration, cam_name, browser_name):
    """
    Streams the camera at the given resolution and calculates the latency from button click to stream start.
    Captures a single image to confirm the resolution while streaming for the given duration.

    Args:
        driver: Selenium WebDriver instance.
        resolution (tuple): Resolution to stream (width, height).
        webrtc_resolutions (dict): Mapping of resolutions to labels.
        duration (int): Duration to stream in seconds.
        cam_name (str): Name of the camera being tested.
        browser_name (str): Name of the browser being used.
    """
    button_label = webrtc_resolutions[resolution]
    buttons = driver.find_elements(By.TAG_NAME, "button")

    # Find and click the button matching the resolution
    for button in buttons:
        if button.text == button_label:
            # Use JavaScript to capture the exact click time
            script = """
                const button = arguments[0];
                const clickTime = new Date(); // Get the actual current time
                const localTime = clickTime.toLocaleTimeString('en-US', { 
                    hour12: false, 
                    hour: '2-digit', 
                    minute: '2-digit', 
                    second: '2-digit' 
                }); // Get local time in HH:MM:SS format
                const milliseconds = clickTime.getMilliseconds(); // Get milliseconds separately
                button.click();
                return localTime + ':' + ('000' + milliseconds).slice(-3); // Combine time and milliseconds
            """
            button_click_time = driver.execute_script(script, button)
            print(f"Button clicked at {button_click_time} (local time).")

            # Validate stream and capture latency
            stream_active, stream_start_time = is_stream_active(driver)
            print("stream_start_time: ", stream_start_time)
            if stream_active:
                # Calculate the latency in seconds and milliseconds
                time_format = "%H:%M:%S:%f"
                button_click_dt = datetime.strptime(button_click_time, time_format)
                stream_start_dt = datetime.strptime(stream_start_time, time_format)
                time_difference = stream_start_dt - button_click_dt
                time_difference_ms = time_difference.total_seconds() * 1000

                print(f"Time difference: {time_difference}, which is {time_difference_ms:.3f} ms.")

                # Create a directory for the browser and resolution screenshots
                browser_folder = os.path.join("Captured_Images", browser_name)
                if not os.path.exists(browser_folder):
                    os.makedirs(browser_folder)

                end_time = time.time() + duration  # Define the end time for streaming
                image_captured = False

                while time.time() < end_time:
                    base_path = os.path.join(browser_folder, f"{browser_name}_{cam_name}_Stream_{resolution[0]}x{resolution[1]}")

                    try:
                        if not image_captured:
                            screenshot_path = capture_full_video_frame(driver, base_path)  # The function appends the timestamp
                            if screenshot_path and os.path.getsize(screenshot_path) > 0:
                                print(f"Valid image captured: {screenshot_path}")
                                image_captured = True
                            else:
                                print(f"Failed to capture image: {screenshot_path} (file is 0 bytes)")
                                if screenshot_path:
                                    os.remove(screenshot_path)  # Delete invalid file
                    except Exception as e:
                        print(f"Error during image capture: {e}")

                print(f"Finished streaming at resolution: {button_label}")
            else:
                print(f"Failed to stream at resolution: {button_label}")
            break


def select_camera_from_dropdown(driver, camera_name):
    """
    Selects a camera from the dropdown on the WebRTC test page and ensures the dropdown closes.

    Args:
        driver: Selenium WebDriver instance.
        camera_name (str): The name of the camera to select.
    """
    try:
        # Find the camera dropdown
        dropdown = driver.find_element(By.ID, "videoSource")  # Adjust if the ID is different on the page

        # Expand the dropdown
        dropdown.click()

        # Wait for the dropdown options to load
        time.sleep(1)  # Adjust sleep time as necessary, or use WebDriverWait for a dynamic wait

        # Get all options
        options = dropdown.find_elements(By.TAG_NAME, "option")

        # Loop through the options to find the matching camera
        for option in options:
            print("Options: ", option.text)
            if camera_name in option.text:
                option.click()
                print(f"Camera '{camera_name}' selected successfully.")

                # Close the dropdown by clicking outside or pressing the Esc key
                driver.execute_script("arguments[0].blur();", dropdown)  # Remove focus from dropdown
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()  # Press Esc key to close it
                return

        # If no matching camera is found
        print(f"Camera '{camera_name}' not found in the dropdown.")
    except Exception as e:
        print(f"Error selecting camera from dropdown: {e}")


def main(camera_names, duration, browser_choices):
    """
    Main function to stream from multiple cameras and capture valid images at the given duration.

    Args:
        camera_names (list): List of camera names to stream from.
        duration (int): Duration to stream in seconds for each camera and resolution.
        browser_choices (list): List of browsers to test (e.g., ["Chrome", "Edge"]).
    """
    try:
        for camera_name in camera_names:
            print(f"\nProcessing camera: {camera_name}")

            # Get the valid camera index for the given camera name
            camera_index = get_valid_camera_index(camera_name)
            if camera_index == -1:
                print(f"No camera found for: {camera_name}")
                continue

            print(f"Camera Index for {camera_name}: {camera_index}")

            # Get resolutions supported by the USB camera
            usb_resolutions, ret_value = get_usb_camera_resolutions(camera_index)
            if ret_value:
                if not usb_resolutions:
                    print(f"No resolutions found for the camera: {camera_name}")
                    continue
            else:
                print(f"Error fetching resolutions for {camera_name}: {usb_resolutions}")
                continue

            # Define WebRTC resolutions
            webrtc_resolutions = {
                (320, 180): "180p (320x180)",
                (320, 240): "QVGA (320x240)",
                (640, 360): "360p (640x360)",
                (640, 480): "VGA (640x480)",
                (1280, 720): "HD/720p (1280x720)",
                (1920, 1080): "Full HD/1080p (1920x1080)",
                (3840, 2160): "Television 4K/2160p (3840x2160)",
                (4096, 2160): "Cinema 4K (4096x2160)",
                (7680, 4320): "8k"
            }

            # Map USB resolutions to WebRTC resolutions
            matched_resolutions = map_resolutions_to_webrtc(usb_resolutions, webrtc_resolutions)
            if not matched_resolutions:
                print(f"No matching resolutions found between USB camera and WebRTC for: {camera_name}")
                continue

            webrtc_url = "https://webrtc.github.io/samples/src/content/getusermedia/resolution/"

            # Supported browsers with corresponding options and drivers
            browsers = {
                "Chrome": (Options(), webdriver.Chrome),
                "Edge": (EdgeOptions(), webdriver.Edge),
                "Firefox": (FirefoxOptions(), webdriver.Firefox),
            }

            for browser_choice in browser_choices:
                if browser_choice not in browsers:
                    print(f"Unsupported browser: {browser_choice}. Skipping...")
                    continue

                options, browser_driver = browsers[browser_choice]
                print(f"Testing on {browser_choice}...")

                if browser_choice == "Chrome":
                    options.add_argument("--use-fake-ui-for-media-stream")
                    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
                    options.add_experimental_option("prefs", {
                        "profile.default_content_setting_values.media_stream_camera": 1,
                        "profile.default_content_setting_values.media_stream_mic": 1,
                    })

                elif browser_choice == "Edge":
                    options.add_argument("--use-fake-ui-for-media-stream")
                    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
                    options.add_experimental_option("prefs", {
                        "profile.default_content_setting_values.media_stream_camera": 1,
                        "profile.default_content_setting_values.media_stream_mic": 1,
                    })

                elif browser_choice == "Firefox":
                    options.set_preference("dom.disable_open_during_load", False)
                    options.set_preference("media.navigator.permission.disabled", True)
                    options.set_preference("media.navigator.streams.fake", False)
                    options.set_preference("privacy.resistFingerprinting", False)
                    options.set_preference("media.getusermedia.screensharing.enabled", True)

                driver = browser_driver(options=options)

                try:
                    driver.get(webrtc_url)
                    # Select the camera from the dropdown
                    select_camera_from_dropdown(driver, camera_name)

                    for resolution in matched_resolutions:
                        print(f"Attempting to stream in resolution: {resolution}")
                        stream_camera_in_resolution(driver, resolution, webrtc_resolutions, duration, camera_name, browser_choice)
                finally:
                    driver.quit()

    except cv2.error as cv_err:
        # Handle OpenCV error when the camera is in use
        if "VIDIOC_STREAMON" in str(cv_err) or "Resource busy" in str(cv_err):
            print("Camera is already in use by another application. Please close other applications and try again.")
        else:
            print(f"OpenCV Error: {cv_err}")

    except Exception as e:
        # Handle any other exceptions
        if "MediaDevice" in str(e) or "Could not start video source" in str(e):
            print("Camera is already in use by another application or browser tab.")
        else:
            print(f"Unexpected Error: {e}")


if __name__ == "__main__":
    camera_name = ["See3CAM_CU27"]
    duration = 10
    browser_choices = ["Chrome"]
    main(camera_name, duration, browser_choices)

