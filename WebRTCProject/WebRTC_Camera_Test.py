import cv2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
from Camera_Test_Automation_API import Camera_api as ca


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
    logs = driver.get_log("browser")
    for entry in logs:
        print(f"WebRTC Log: {entry['message']}")


def is_stream_active(driver):
    """
    Confirm that the stream is active on the WebRTC page by checking the video element.
    Returns True if the stream is active, otherwise False.
    """
    try:
        video_element = driver.find_element(By.TAG_NAME, "video")
        if video_element.is_displayed():
            print("Stream is active.")
            return True
    except Exception as e:
        print(f"Stream check failed: {e}")
    return False


def stream_camera_in_resolution(driver, resolution, webrtc_resolutions, duration):
    button_label = webrtc_resolutions[resolution]
    buttons = driver.find_elements(By.TAG_NAME, "button")

    # Find and click the button matching the resolution
    for button in buttons:
        if button.text == button_label:
            button.click()
            time.sleep(1)  # Wait for the stream to start
            if is_stream_active(driver):
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

    chrome_options = Options()
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument(f"--use-file-for-fake-video-capture=/dev/video{camera_index}")
    chrome_options.set_capability("goog:loggingPrefs", {"browser": "ALL"})  # Enable browser logging

    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()

    try:
        webrtc_url = "https://webrtc.github.io/samples/src/content/getusermedia/resolution/"
        driver.get(webrtc_url)

        time.sleep(5)

        for resolution in matched_resolutions:
            print(f"Attempting to stream in resolution: {resolution}")
            stream_camera_in_resolution(driver, resolution, webrtc_resolutions, duration)
    finally:
        driver.quit()


if __name__ == "__main__":
    camera_name = "See3CAM_CU81"
    duration = 10
    main(camera_name, duration)
