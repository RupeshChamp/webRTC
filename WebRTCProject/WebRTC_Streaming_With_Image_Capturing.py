import os
import cv2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
import time
from Camera_Test_Automation_API import Camera_api as ca


def get_valid_camera_index(camera_name):
    """
    Finds the index of the camera matching the specified camera name.

    Returns:
        int: The index of the camera if found, otherwise -1.
    """
    import gc

    cap = cv2.VideoCapture()
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
    print(ca.assign_camera(camera_index))
    supported_resolutions = ca.get_supported_resolution(camera_index)
    print(supported_resolutions)
    unique_resolutions = sorted({(width, height) for _, width, height, _ in supported_resolutions[0]})
    print("Unique resolutions supported by the camera:", unique_resolutions)
    ca.release_camera(camera_index)
    return unique_resolutions


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
        bool: True if the stream is active, otherwise False.
    """
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        if video_element.is_displayed():
            print("Stream is active.")
            return True
    except Exception as e:
        print(f"Stream check failed: {e}")
    return False


def capture_full_video_frame(driver, save_path):
    """
    Captures the full video frame from the video element using a canvas.

    Args:
        driver: Selenium WebDriver instance.
        save_path: Path to save the captured image.
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
        base64_image = driver.execute_script(script)

        # Decode the base64 image and save it to the specified path
        import base64
        with open(save_path, "wb") as file:
            file.write(base64.b64decode(base64_image.split(",")[1]))
        print(f"Full video frame saved to {save_path}")
    except Exception as e:
        print(f"Failed to capture full video frame: {e}")


def stream_camera_in_resolution(driver, resolution, webrtc_resolutions, duration, cam_name, browser_name):
    button_label = webrtc_resolutions[resolution]
    buttons = driver.find_elements(By.TAG_NAME, "button")

    # Find and click the button matching the resolution
    for button in buttons:
        if button.text == button_label:
            button.click()
            time.sleep(1)

            if not os.path.exists("screenshots"):
                os.makedirs("screenshots")
            screenshot_path = f"screenshots/{browser_name}_{cam_name}_stream_{resolution[0]}x{resolution[1]}.jpg"

            if is_stream_active(driver, screenshot_path=screenshot_path):
                capture_full_video_frame(driver, screenshot_path)
                print(f"Streaming successfully at resolution: {button_label}")
            else:
                print(f"Failed to stream at resolution: {button_label}")
            break

    # Log any errors from WebRTC
    log_web_rtc_errors(driver)

    # Stream for the given duration
    time.sleep(duration)


def main(camera_name, duration):
    camera_index = get_valid_camera_index(camera_name)
    if camera_index == -1:
        print("No camera found.")
        return

    print("Camera Index: ", camera_index)

    usb_resolutions = get_usb_camera_resolutions(camera_index)
    if not usb_resolutions:
        print("No resolutions found for the USB camera.")
        return

    print("USB Resolutions: ", usb_resolutions)

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

    matched_resolutions = map_resolutions_to_webrtc(usb_resolutions, webrtc_resolutions)
    if not matched_resolutions:
        print("No matching resolutions found between USB camera and WebRTC.")
        return

    webrtc_url = "https://webrtc.github.io/samples/src/content/getusermedia/resolution/"

    # Testing on multiple browsers
    browsers = [
        ("Chrome", Options(), webdriver.Chrome),
        ("Edge", EdgeOptions(), webdriver.Edge),
        ("Firefox", FirefoxOptions(), webdriver.Firefox),
    ]

    for browser_name, options, browser_driver in browsers:
        print(f"Testing on {browser_name}...")

        if browser_name == "Chrome":
            options.add_argument("--use-fake-ui-for-media-stream")
            options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
            options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.media_stream_camera": 1,
                "profile.default_content_setting_values.media_stream_mic": 1,
            })

        elif browser_name == "Edge":
            options.add_argument("--use-fake-ui-for-media-stream")
            options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
            options.add_experimental_option("prefs", {
                "profile.default_content_setting_values.media_stream_camera": 1,
                "profile.default_content_setting_values.media_stream_mic": 1,
            })

        elif browser_name == "Firefox":
            options = FirefoxOptions()
            options.set_preference("dom.disable_open_during_load", False)
            options.set_preference("media.navigator.permission.disabled", True)
            options.set_preference("media.navigator.streams.fake", False)
            options.set_preference("privacy.resistFingerprinting", False)
            options.set_preference("media.getusermedia.screensharing.enabled", True)

        driver = browser_driver(options=options)

        try:
            driver.get(webrtc_url)
            for resolution in matched_resolutions:
                print(f"Attempting to stream in resolution: {resolution}")
                stream_camera_in_resolution(driver, resolution, webrtc_resolutions, duration, camera_name, browser_name)
        finally:
            driver.quit()


if __name__ == "__main__":
    camera_name = "See3CAM_CU81"
    duration = 5
    main(camera_name, duration)
