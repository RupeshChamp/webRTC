import datetime
import os
from typing import Any
import time
import hid
import cv2
import numpy as np
from threading import Thread, Event


class Camera_api:
    streaming_status = {}
    streaming_threads = {}
    stop_events = {}
    exit_val = None
    child_folder = None
    main_folder = None
    cam_list = []
    cam_index = []
    global RED_TEXT, RESET_COLOR
    frame = None
    frame1 = None
    streaming_initialised = False
    resolution_found = None
    VID = None
    PID = None
    device_path = None
    slash_reference = None
    supported_uvc_properties = None
    uvc_propID = None
    possible_uvc_list = None
    support_mode = None
    prop_id = None
    available_properties = None
    current_mode = None
    current_value = None
    supported_mode = None
    default_value = None
    roll_prop = None
    stepping_delta = None
    minimum = None
    maximum = None
    capture_properties = None
    con_prop = None
    gain_prop = None
    supported_properties = None
    iris_prop = None
    focus_prop = None
    tilt_prop = None
    backlight_prop = None
    pan_prop = None
    zoom_prop = None
    exp_prop = None
    gamma_prop = None
    wb_prop = None
    hue_prop = None
    sharp_prop = None
    sat_prop = None
    bri_prop = None
    serial_number = None
    firmware = None
    device = None
    devices = None
    cap = None
    cap2 = None
    cap1 = None

    RED_TEXT = "\033[91m"
    RESET_COLOR = "\033[0m"

    @classmethod
    def get_error_description(cls, error_code):
        success_code = 0
        status_code = False
        ERROR_UNKNOWN_ERROR_CODE = 400
        error_codes = {
            0: 'Success code',
            101: 'Camera devices not found',
            102: 'Camera not assigned / Unable to assign the camera',
            103: 'Unable to release the camera',
            104: 'Unable to get device path',
            105: 'Unable to get PID',
            106: 'Unable to get VID',
            107: 'Unable to get firmware version',
            108: 'Unable to get Unique ID',
            109: 'Unable to get supported resolutions',
            110: 'Unable to set resolution',
            111: 'Unable to get supported UVC Parameters',
            112: 'Unable to get UVC parameter value',
            113: 'Unable to set UVC parameter value',
            114: 'Unable to stream',
            115: 'Unable to save image',
            116: 'Unable to get HID',
            117: 'Unable to set HID',
            118: 'Unable to set HID values in default',
            119: 'Unable to get camera details',
            120: 'Camera is occupied',
            121: 'Streaming must be initialized',
            122: 'Unable to set uvc parameter value to default',
            123: 'Missing Image save path',
            124: 'Missing Arguments',
            201: 'Invalid camera node',
            202: 'Invalid Width',
            203: 'Invalid Height',
            204: 'Invalid Format',
            205: 'Invalid FPS',
            206: 'Invalid UVC parameter name',
            207: 'Invalid UVC parameter value',
            208: 'Invalid UVC parameter mode',
            209: 'Invalid start value',
            210: 'Invalid end value',
            211: 'Invalid step value',
            212: 'Invalid hold value',
            213: 'Invalid Image save value',
            214: 'Invalid Image save format',
            215: 'Invalid camera ID',
            216: 'Invalid duration',
            217: 'Invalid show FPS',
            218: 'Invalid Save to path',
            219: 'Invalid image save name',
            220: 'Invalid Hid_bytes',
            301: 'Unable to create the folder',
            400: "Unknown Error code"
        }

        try:
            return error_codes[error_code], success_code
        except Exception:
            return status_code, ERROR_UNKNOWN_ERROR_CODE

    @classmethod
    def get_connected_devices(cls) -> list:

        """
            Usage:
                Retrieve a list of connected camera devices.
            Returns:
                tuple: Detected devices and status code.
                       - If devices are found, returns a dictionary mapping device indices to their names and 0 as success code.
                       - If no devices are found, returns False and error code 101.
        """

        detected_devices = {}
        ERROR_NO_DEVICES_FOUND = 101  # Camera devices not found
        status_code = False
        success_code = 0
        try:
            cls.cap1 = cv2.VideoCapture()
            for i in range(cls.cap1.getDevices()[1]):
                device_name = str(cls.cap1.getDeviceInfo(i)[1])
                detected_devices[i] = device_name
            if detected_devices != {}:
                return detected_devices, success_code
            else:
                return status_code, ERROR_NO_DEVICES_FOUND
        except Exception:
            return status_code, ERROR_NO_DEVICES_FOUND

    @classmethod
    def assign_camera(cls, camera_node: int) -> int:
        global RED_TEXT, RESET_COLOR

        """           
            Usage:
                Assigns the specified camera node using OpenCV.

            Parameters:
                - camera_node (int): Camera node obtained from get_devices().

            Returns:
                tuple: Assigned camera object and an status code.
                       - If the camera is successfully assigned, returns the camera object and 0 as success code.
                       - If the specified camera is not assigned, returns False and error code 102.
                       - If an invalid camera node is provided, returns False and error code 103.
        """

        ERROR_INVALID_CAMERA_NODE = 201  # Invalid camera node provided
        ERROR_CAMERA_IS_OCCUPIED = 120  # Camera is occupied / Unable to assign the camera

        status_code = False
        success_code = 0
        if not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE
        elif cls.cap is not None:
            return status_code, ERROR_CAMERA_IS_OCCUPIED

        cls.cap = None
        cls.stop = False

        try:
            cls.cap = cv2.VideoCapture(camera_node)
            no_of_devices = cls.cap.getDevices()[1]
            if camera_node < no_of_devices:
                if cls.cap.isOpened():
                    cls.cam_list.append(cls.cap)
                    cls.cam_index.append(camera_node)
                    return cls.cap, success_code
                else:
                    return status_code, ERROR_CAMERA_IS_OCCUPIED
            else:
                return status_code, ERROR_INVALID_CAMERA_NODE
        except Exception:
            return status_code, ERROR_INVALID_CAMERA_NODE

    @classmethod
    def release_camera(cls, camera_node: int) -> int:
        """
            Usage:
                Releases the camera for the given node.

            Parameters:
                camera_node (int): Camera node obtained from get_connected_devices().

            Returns:
                tuple: True if the camera is successfully released, False otherwise, and an error code.
                       - If the camera is successfully released, returns True and 0 as success code.
                       - If an invalid camera node is provided, returns False and error code 103.
                       - If unable to release the camera, returns False and error code 104.
                       - If the specified camera is not assigned, returns False and error code 102.
        """

        ERROR_CAMERA_NOT_ASSIGNED = 102  # Camera not assigned / Unable to assign the camera
        ERROR_INVALID_CAMERA_NODE = 201  # Invalid camera node provided
        ERROR_UNABLE_TO_RELEASE_CAMERA = 103  # Unable to release the camera
        status_code = False
        success_code = 0
        cls.exit_val = False
        if not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE
        try:
            if cls.cam_list[cls.cam_index.index(int(camera_node))].isOpened():
                try:
                    cls.cam_list[cls.cam_index.index(int(camera_node))].release()
                    cls.cam_list.clear()
                    cls.cam_index.clear()
                    cls.cap = None
                    cls.exit_val = True
                    status_code = True
                    return status_code, success_code
                except:
                    return status_code, ERROR_UNABLE_TO_RELEASE_CAMERA
            else:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED  # camera is not opened

        except Exception as e:
            if NameError:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED
            else:
                return status_code, ERROR_INVALID_CAMERA_NODE

    @classmethod
    def get_device_path(cls, camera_node: int) -> str:

        """
            Usage:
                Gets the Device Path of the camera for the given node.

            Parameters:
                camera_node (int): Camera node obtained from get_connected_devices().

            Returns:
                tuple: device_path of the camera and 0 as success code if successful, otherwise False and an error code.
                       - If the device_path is successfully obtained, returns the device_path and 0 as success code.
                       - If an invalid camera node is provided, returns False and error code 103.
                       - If unable to get the device_path, returns False and error code 105.
        """

        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_UNABLE_TO_GET_DEVICE_PATH = 104  # Unable to get the Device path
        status_code = False
        success_code = 0
        cls.device_path = None

        if not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE

        try:
            cls.cap = cv2.VideoCapture()
            no_of_devices = cls.cap.getDevices()[1]

            if camera_node < no_of_devices:
                cls.device_path = cls.cap.getDeviceInfo(camera_node)[4]
            else:
                return status_code, ERROR_INVALID_CAMERA_NODE

            if cls.device_path != '':
                return cls.device_path, success_code
            else:
                return status_code, ERROR_UNABLE_TO_GET_DEVICE_PATH

        except Exception:
            return status_code, ERROR_INVALID_CAMERA_NODE

    @classmethod
    def get_PID(cls, camera_node: int) -> str:
        """
            Usage:
                Gets the PID of the camera for the given node.

            Parameters:
                camera_node (int): Camera node obtained from get_connected_devices().

            Returns:
                tuple: PID of the camera and 0 as success code if successful, otherwise False and an error code.
                       - If the PID is successfully obtained, returns the PID and 0 as success code.
                       - If an invalid camera node is provided, returns False and error code 103.
                       - If unable to get the PID, returns False and error code 105.
        """

        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_UNABLE_TO_GET_PID = 105  # Unable to get the PID
        status_code = False
        cls.PID = None

        if not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE

        try:
            cls.cap = cv2.VideoCapture()
            no_of_devices = cls.cap.getDevices()[1]

            if camera_node < no_of_devices:
                cls.PID = cls.cap.getDeviceInfo(camera_node)[3]
            else:
                return status_code, ERROR_INVALID_CAMERA_NODE

            if cls.PID != '':
                return cls.PID, 0
            else:
                return status_code, ERROR_UNABLE_TO_GET_PID
        except Exception:
            return status_code, ERROR_INVALID_CAMERA_NODE

    @classmethod
    def get_VID(cls, camera_node: int) -> tuple[Any, int] | tuple[None, int]:

        """
            Usage:
                Gets the VID of the camera for the given node.
            Parameters:
                camera_node (int): Camera node obtained from get_connected_devices().
            Returns:
                tuple: VID of the camera and 0 as success code if successful, otherwise False and an error code.
                       - If the VID is successfully obtained, returns the VID and 0 as success code.
                       - If an invalid camera node is provided, returns False and error code 103.
                       - If unable to get the VID, returns False and error code 105.
        """

        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_UNABLE_TO_GET_VID = 106  # Unable to get the VID
        status_code = False
        success_code = 0
        if not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE

        cls.VID = None

        try:
            cls.cap = cv2.VideoCapture()
            no_of_devices = cls.cap.getDevices()[1]
            if camera_node < no_of_devices:
                cls.VID = cls.cap.getDeviceInfo(camera_node)[2]
            else:
                return status_code, ERROR_INVALID_CAMERA_NODE

            if cls.VID != '':
                return cls.VID, success_code
            else:
                return status_code, ERROR_UNABLE_TO_GET_VID
        except Exception:
            return status_code, ERROR_INVALID_CAMERA_NODE

    @classmethod
    def get_firmware_version(cls, camera_node: int):

        """
            Usage:
                Gets the firmware version of the e-con camera for the given node using HID commands.

            Parameters:
                camera_node (int): Camera node obtained from get_connected_devices().

            Returns:
                tuple: Firmware version of the camera and 0 as success code if successful, otherwise False and an error code.
                       - If the firmware version is successfully obtained, returns the firmware version and 0 as success code.
                       - If an invalid camera node is provided, returns False and error code 103.
                       - If unable to get the firmware version, returns False and error code 107.
        """

        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_UNABLE_TO_GET_FIRMWARE = 107  # Unable to get the Firmware for the given camera
        status_code = False
        success_code = 0
        cls.firmware = None

        if not isinstance(camera_node, int):
            return False, ERROR_INVALID_CAMERA_NODE

        try:
            # Open the device using a path
            cls.devices = hid.enumerate(
                int('0x' + cls.cam_list[cls.cam_index.index(camera_node)].getDeviceInfo(camera_node)[2], 16),
                int('0x' + cls.cam_list[cls.cam_index.index(camera_node)].getDeviceInfo(camera_node)[3], 16))
            print(cls.devices)
            if not cls.devices:
                return cls.firmware, ERROR_UNABLE_TO_GET_FIRMWARE

            cls.device = hid.device()
            cls.device.open_path(cls.devices[0]["path"])
            # Refer the HID command.
            command = [0x00, 0x40]
            # Send the command to the camera
            cls.device.write(command)
            # Read the response (adjust the length as per your expected response)
            response = cls.device.read(65, 1000)
            SDK_VER = (response[3] << 8) + response[4]
            SVN_VER = (response[5] << 8) + response[6]
            pMajorVersion = response[1]
            pMinorVersion1 = response[2]
            cls.firmware = str(pMajorVersion) + "." + str(pMinorVersion1) + "." + str(SDK_VER) + "." + str(SVN_VER)
        except Exception as e:
            if NameError:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED
            else:
                return status_code, ERROR_INVALID_CAMERA_NODE
        return cls.firmware, success_code

    @classmethod
    def get_unique_ID(cls, camera_node: int):

        """
            Usage:
                Gets the unique ID of the e-con camera for the given node using HID commands.

            Parameters:
                camera_node (int): Camera node obtained from get_connected_devices().

            Returns:
                tuple: Unique ID of the camera and 0 as success code if successful, otherwise False and an error code.
                       - If the unique ID is successfully obtained, returns the unique ID and 0 as success code.
                       - If an invalid camera node is provided, returns False and error code 103.
                       - If unable to get the unique ID, returns False and error code 108.
        """

        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_UNABLE_TO_GET_UNIQUE_ID = 108
        status_code = False
        success_code = 0
        cls.serial_number = None

        if not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE

        try:
            # Open the device using path
            cls.devices = hid.enumerate(
                int('0x' + cls.cam_list[cls.cam_index.index(camera_node)].getDeviceInfo(camera_node)[2], 16),
                int('0x' + cls.cam_list[cls.cam_index.index(camera_node)].getDeviceInfo(camera_node)[3], 16))

            if not cls.devices:
                return cls.serial_number, ERROR_UNABLE_TO_GET_UNIQUE_ID
                # return None
            cls.device = hid.device()
            cls.device.open_path(cls.devices[0]["path"])
            command = [0x00, 0x41, 0x01, 0x00, 0x00, 0x00]
            cls.device.write(command)
            response = cls.device.read(65, 1000)
            cls.serial_number = format(response[1], '02X') + format(response[2], '02X') + format(response[3],
                                                                                                 '02X') + format(
                response[4], '02X')
        except Exception as e:
            if NameError:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED
            else:
                return status_code, ERROR_INVALID_CAMERA_NODE

        return cls.serial_number, success_code

    @classmethod
    def get_supported_resolution(cls, camera_node: int):
        """
            Usage:
                Used to get the supported resolutions of the camera for the given node.

            Parameters:
                - camera_node (int): Camera node obtained using the get_connected_devices method.

            Returns:
                tuple: Supported resolutions along with formats, width, height, and FPS if successful, otherwise False and an error code.
                       - If the supported resolutions are successfully obtained, returns a list containing supported resolutions along with formats, width, height, and FPS, along with 0 as success code.
                       - If the camera is not assigned, returns False and error code 102.
                       - If an invalid camera node is provided, returns False and error code 201.
                       - If unable to get the supported resolutions, returns False and error code 109.
        """

        ERROR_UNABLE_TO_GET_RESOLUTION = 109
        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_INVALID_CAMERA_NODE = 201

        status_code = False
        success_code = 0
        if isinstance(camera_node, bool) or not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE
        supported_resolution = []

        try:
            for res in range(cls.cam_list[cls.cam_index.index(int(camera_node))].getFormats()[1]):
                supported_resolution.append(cls.cap.getFormatType(res)[1:])
            return supported_resolution, success_code
        except Exception:
            if NameError:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED
            else:
                return status_code, ERROR_UNABLE_TO_GET_RESOLUTION

    @classmethod
    def set_resolution(cls, camera_node: int, width: int, height: int, Format: str, FPS: int):

        """
            Usage:
                Used to set the resolution of the camera for the given node.

            Parameters:
                - camera_node (int): Camera node obtained using the get_connected_devices method.
                - width (int): Width of the resolution.
                - height (int): Height of the resolution.
                - Format (str): Format of the resolution.
                - FPS (int): FPS of the resolution.

            Returns:
                tuple: True if the resolution is successfully set, otherwise False and an error code.
                       - If the resolution is successfully set, returns True and 0 as success code.
                       - If the camera is not assigned, returns False and error code 102.
                       - If an invalid camera node is provided, returns False and error code 201.
                       - If an invalid width provided, returns False and error code 202.
                       - If an invalid height provided, returns False and error code 203.
                       - If an invalid format provided, returns False and error code 204.
                       - If an invalid FPS provided, returns False and error code 205.
                       - If unable to set the resolution, returns False and error code 110.
        """

        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_INVALID_WIDTH = 202
        ERROR_INVALID_HEIGHT = 203
        ERROR_INVALID_FORMAT = 204
        ERROR_INVALID_FPS = 205
        ERROR_UNABLE_TO_SET_RESOLUTIONS = 110
        ERROR_MISSING_ARGUMENTS = 124
        status_code = False
        success_code = 0

        if isinstance(camera_node, bool) or not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE
        if isinstance(width, bool) or not isinstance(width, int):
            return status_code, ERROR_INVALID_WIDTH
        if isinstance(height, bool) or not isinstance(height, int):
            return status_code, ERROR_INVALID_HEIGHT
        if not isinstance(Format, str):
            return status_code, ERROR_INVALID_FORMAT
        if isinstance(FPS, bool) or not isinstance(FPS, int):
            return status_code, ERROR_INVALID_FPS

        try:
            resolution = (True, Format, width, height, FPS)
            cls.resolution_found = False
            try:
                # Find camera node and attempt to set resolution
                cls.cam_index_int = int(camera_node)
                cls.cam_index_pos = cls.cam_index.index(cls.cam_index_int)
                ret, frame = cls.cam_list[cls.cam_index_pos].read()
                frame.any()

                for res in range(cls.cam_list[cls.cam_index.index(int(camera_node))].getFormats()[1]):
                    try:
                        if resolution == cls.cam_list[cls.cam_index.index(int(camera_node))].getFormatType(res):
                            cls.cam_list[cls.cam_index.index(int(camera_node))].setFormatType(res)
                            status_code = True
                            cls.resolution_found = True
                            return status_code, success_code
                    except ValueError:
                        return status_code, ERROR_UNABLE_TO_SET_RESOLUTIONS
                if not cls.resolution_found:
                    return status_code, ERROR_UNABLE_TO_SET_RESOLUTIONS
            except Exception:
                if NameError:
                    return status_code, ERROR_CAMERA_NOT_ASSIGNED
                else:
                    return status_code, ERROR_UNABLE_TO_SET_RESOLUTIONS
        except Exception:
            if TypeError:
                return status_code, ERROR_MISSING_ARGUMENTS
            else:
                return status_code, ERROR_INVALID_CAMERA_NODE

    @classmethod
    def get_supported_uvc_parameter(cls, camera_node: int):

        """
           Used to getting the UVC supported features of the camera for the  give node.
            Parameters:
            - camera_node (int): camera node which was get using the get devices.
            Returns:
            Dict: Supported UVC features along with minimum, maximum, step, current value, default value, applied mode, supported mode.
                applied mode either 1 or 2 --> 1 - Auto 2 - Manual
                Supported mode either 2 or 3  --> 2 - auto not supported, 3 - both manual and auto supported
        """

        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_UNABLE_TO_GET_SUPPORTED_UVC_PARAMETER = 111
        status_code = False
        success_code = 0

        if isinstance(camera_node, bool) or not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE

        cls.possible_uvc_list = ['brightness', 'contrast', 'saturation', 'sharpness', 'hue', 'white_balance_blue_u',
                                 'gamma', 'exposure',
                                 'gain', 'zoom', 'pan', 'tilt',
                                 'backlight', 'focus', 'roll', 'iris']

        cls.supported_uvc_properties = {}
        cls.minimum = -1
        cls.maximum = -1
        cls.stepping_delta = -1
        cls.supported_mode = -1
        cls.current_value = -1
        cls.current_mode = -1
        cls.default_value = -1
        cls.bri_prop = []
        cls.con_prop = []
        cls.sat_prop = []
        cls.sharp_prop = []
        cls.hue_prop = []
        cls.wb_prop = []
        cls.gamma_prop = []
        cls.exp_prop = []
        cls.gain_prop = []
        cls.zoom_prop = []
        cls.pan_prop = []
        cls.tilt_prop = []
        cls.backlight_prop = []
        cls.focus_prop = []
        cls.roll_prop = []
        cls.iris_prop = []
        cls.capture_properties = ['msec', 'frames', 'ratio', 'width', 'height', 'fps', 'fourcc', 'count', 'format',
                                  'mode', 'brightness',
                                  'contrast', 'saturation', 'hue', 'gain', 'exposure', 'convert_rgb',
                                  'white_balance_blue_u', 'rectification',
                                  'monochrome', 'sharpness', 'auto_exposure', 'gamma', 'temperature', 'trigger',
                                  'trigger_delay',
                                  'white_balance_red_v', 'zoom', 'focus', 'guid', 'iso_speed', '', 'backlight', 'pan',
                                  'tilt', 'roll', 'iris',
                                  'settings', 'buffersize', 'autofocus']
        cls.uvc_propID = [cls.bri_prop, cls.con_prop, cls.sat_prop, cls.sharp_prop, cls.hue_prop, cls.wb_prop,
                          cls.gamma_prop, cls.exp_prop, cls.gain_prop, cls.zoom_prop, cls.pan_prop, cls.tilt_prop,
                          cls.backlight_prop, cls.focus_prop, cls.roll_prop, cls.iris_prop]

        cls.supported_properties = []
        cls.support_mode = []
        cls.feature_list = []
        # checking the availability of the UVC parameter for the connected parameter
        try:
            no_of_devices = cls.cap.getDevices()[1]
            if not camera_node < no_of_devices:
                return status_code, ERROR_INVALID_CAMERA_NODE

            for i in range(38):
                get_availability_properties = (cls.cam_list[cls.cam_index.index(int(camera_node))].get(i))  # 94
                value_not_supported_properties = -1.0
                if get_availability_properties != value_not_supported_properties:
                    cls.supported_properties.append(cls.capture_properties[i])
                cls.available_properties = (
                    cls.cap.get(i, cls.minimum, cls.maximum, cls.stepping_delta, cls.supported_mode,
                                cls.current_value, cls.current_mode, cls.default_value))  # 132
                if cls.available_properties[0]:

                    cls.prop_id = list(cls.available_properties)

                    cls.prop_id.append(cls.capture_properties[i])
                    if cls.prop_id[4] == 3:
                        cls.support_mode.append(cls.prop_id[-1])

                    for uvc_name in range(len(cls.possible_uvc_list)):

                        if cls.prop_id[-1] == cls.possible_uvc_list[uvc_name]:
                            cls.uvc_propID[uvc_name].append(cls.prop_id[1])
                            cls.uvc_propID[uvc_name].append(cls.prop_id[2])
                            cls.uvc_propID[uvc_name].append(cls.prop_id[3])
                            cls.uvc_propID[uvc_name].append(cls.prop_id[5])
                            cls.uvc_propID[uvc_name].append(cls.prop_id[7])
                            cls.uvc_propID[uvc_name].append(cls.prop_id[6])
                            cls.uvc_propID[uvc_name].append(cls.prop_id[4])
                            cls.supported_uvc_properties[str(cls.prop_id[-1])] = cls.uvc_propID[uvc_name]
            return cls.supported_uvc_properties, success_code
        except Exception:
            if NameError:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED
            else:
                return status_code, ERROR_UNABLE_TO_GET_SUPPORTED_UVC_PARAMETER

    @classmethod
    def set_uvc(cls, camera_node: int, parameter_name: str, value: int, Mode: int):

        """
        Usage:
            Used to set the given parameter value in the camera.

        Parameters:
            - camera_node (int): Camera node obtained using the get_connected_devices method.
            - parameter_name (str): Supported UVC parameter name.
            - value (int): Value to set for the UVC parameter.
            - Mode (int): Mode for setting the parameter.
        Returns:

        """

        # while not cls.streaming_initialised:
        #     continue
        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_INVALID_UVC_PARAMETER_NAME = 206
        ERROR_INVALID_UVC_PARAMETER_VALUE = 207
        ERROR_INVALID_UVC_PARAMETER_MODE = 208
        ERROR_UNABLE_TO_SET_UVC_PARAMETER_VALUE = 113
        status_code = False
        success_code = 0
        if isinstance(camera_node, bool) or not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE
        if isinstance(parameter_name, bool) or not isinstance(parameter_name, str):
            return status_code, ERROR_INVALID_UVC_PARAMETER_NAME
        if isinstance(value, bool) or not isinstance(value, int):
            return status_code, ERROR_INVALID_UVC_PARAMETER_VALUE
        if isinstance(Mode, bool) or not isinstance(Mode, int):
            return status_code, ERROR_INVALID_UVC_PARAMETER_MODE

        UVC_PARAMETER_NAMES = ['BRIGHTNESS', 'CONTRAST', 'SHARPNESS', 'SATURATION', 'HUE', 'WHITE_BALANCE_BLUE_U', 'GAMMA', 'EXPOSURE',
                               'GAIN', 'ZOOM', 'PAN', 'TILT',
                               'FOCUS', 'BACKLIGHT', 'ROLL', 'IRIS']
        CAP_UVCPROPERTIES_NAME = [cv2.CAP_PROP_BRIGHTNESS, cv2.CAP_PROP_CONTRAST, cv2.CAP_PROP_SHARPNESS,
                                  cv2.CAP_PROP_SATURATION, cv2.CAP_PROP_HUE, cv2.CAP_PROP_WHITE_BALANCE_BLUE_U,
                                  cv2.CAP_PROP_GAMMA, cv2.CAP_PROP_EXPOSURE, cv2.CAP_PROP_GAIN, cv2.CAP_PROP_ZOOM,
                                  cv2.CAP_PROP_PAN, cv2.CAP_PROP_TILT, cv2.CAP_PROP_BACKLIGHT, cv2.CAP_PROP_FOCUS,
                                  cv2.CAP_PROP_ROLL, cv2.CAP_PROP_IRIS]
        try:
            try:
                if parameter_name.upper() in UVC_PARAMETER_NAMES:
                    UVC_PARAMETER_NAMES.index(parameter_name.upper())

                cls.cam_list[cls.cam_index.index(int(camera_node))].set(
                    CAP_UVCPROPERTIES_NAME[UVC_PARAMETER_NAMES.index(parameter_name.upper())], value, Mode)
                new_val = int(cls.cam_list[cls.cam_index.index(int(camera_node))].get(
                    CAP_UVCPROPERTIES_NAME[UVC_PARAMETER_NAMES.index(parameter_name.upper())]))
                return new_val, success_code
            except ValueError:
                return status_code, ERROR_INVALID_UVC_PARAMETER_NAME
        except Exception as e:
            if NameError:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED
            else:
                return status_code, ERROR_UNABLE_TO_SET_UVC_PARAMETER_VALUE

    @classmethod
    def get_uvc(cls, camera_node: int, parameter_name: str):
        """
            Usage:
                Used to get the supported UVC features of the camera for the given node.

            Parameters:
                - camera_node (int): Camera node obtained using the get_connected_devices method.

            Returns:l
                tuple: Supported UVC features along with minimum, maximum, step, current value, default, applied mode, and supported mode if successful, otherwise False and an error code.
                       - If the supported UVC features are successfully obtained, returns a dictionary containing supported UVC features along with their details, along with 0 as success code.
                       - If the camera is not assigned, returns False and error code 102.
                       - If an invalid camera node is provided, returns False and error code 201.
                       - If unable to get the supported UVC features, returns False and error code 111.
        """

        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_INVALID_UVC_PARAMETER_NAME = 206
        ERROR_UNABLE_TO_GET_UVC_PARAMETER_VALUE = 112
        status_code = False
        success_code = 0
        if isinstance(camera_node, bool) or not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE
        if not isinstance(parameter_name, str):
            return status_code, ERROR_INVALID_UVC_PARAMETER_NAME

        UVC_PARAMETER_NAMES = ['BRIGHTNESS', 'CONTRAST', 'SHARPNESS', 'SATURATION', 'HUE', 'WHITE_BALANCE_BLUE_U', 'GAMMA', 'EXPOSURE',
                               'GAIN', 'ZOOM', 'PAN', 'TILT',
                               'FOCUS', 'BACKLIGHT', 'ROLL', 'IRIS']
        CAP_UVCPROPERTIES_NAME = [cv2.CAP_PROP_BRIGHTNESS, cv2.CAP_PROP_CONTRAST, cv2.CAP_PROP_SHARPNESS,
                                  cv2.CAP_PROP_SATURATION, cv2.CAP_PROP_HUE, cv2.CAP_PROP_WHITE_BALANCE_BLUE_U,
                                  cv2.CAP_PROP_GAMMA, cv2.CAP_PROP_EXPOSURE, cv2.CAP_PROP_GAIN, cv2.CAP_PROP_ZOOM,
                                  cv2.CAP_PROP_PAN, cv2.CAP_PROP_TILT, cv2.CAP_PROP_BACKLIGHT, cv2.CAP_PROP_FOCUS,
                                  cv2.CAP_PROP_ROLL, cv2.CAP_PROP_IRIS]
        try:
            try:
                if parameter_name.upper() in UVC_PARAMETER_NAMES:
                    UVC_PARAMETER_NAMES.index(parameter_name.upper())
                value = int(cls.cam_list[cls.cam_index.index(int(camera_node))].get(
                    CAP_UVCPROPERTIES_NAME[UVC_PARAMETER_NAMES.index(parameter_name.upper())]))
                return value, success_code
            except ValueError:
                return status_code, ERROR_INVALID_UVC_PARAMETER_NAME
        except Exception as e:
            if NameError:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED
            else:
                return status_code, ERROR_UNABLE_TO_GET_UVC_PARAMETER_VALUE

    @classmethod
    def uvc_var(cls, camera_node: int, parameter_name: str, start: int, end: int, step: int, mode: int, hold: int, image_save: bool = False, save_path: str = "", save_format='jpg'):

        """
        Usage:
            Varies the given UVC parameter within the specified range with the provided step size and optionally saves images.

        Parameters:
            - camera_node (int): Camera node obtained using the get_connected_devices method.
            - parameter_name (str): Supported UVC parameter name.
            - start (int): Starting value for the UVC parameter.
            - end (int): Ending value for the UVC parameter.
            - step (int): Step size for varying the UVC parameter.
            - mode (int): Mode for setting the UVC parameter.
            - hold (int): Time to hold each parameter value (in seconds).
            - image_save (bool): Indicates whether to save images while varying the parameter (default is False).
            - save_path (str): Path to save the images (required if image_save is True).
            - save_format (str): Format to save the images (default is 'jpg').

        Returns:
            tuple: A tuple containing the following:
                - If the parameter value is successfully set, returns True and 0 as success code.
                - If an error occurs, returns False and an error code.
        """

        cls.exit_val = False
        cls.slash_reference = "\\"

        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_INVALID_UVC_PARAMETER_NAME = 206
        ERROR_INVALID_UVC_PARAMETER_MODE = 208
        ERROR_INVALID_START_VALUE = 209
        ERROR_INVALID_END_VALUE = 210
        ERROR_INVALID_STEP_VALUE = 211
        ERROR_INVALID_HOLD_VALUE = 212
        ERROR_IMAGE_SAVE_VALUE = 213
        ERROR_IMAGE_SAVE_FORMAT = 214
        ERROR_INVALID_SAVE_PATH = 218
        ERROR_INITIALIZING_STREAM = 121
        ERROR_UNABLE_TO_SET_UVC_PARAMETER_VALUE = 113
        ERROR_UNABLE_TO_CREATE_FOLDER = 301
        status_code = False
        success_code = 0

        supported_image_save_format = ['bmp', 'jpg', 'raw', 'png']

        if isinstance(camera_node, bool) or not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE
        if isinstance(parameter_name, bool) or not isinstance(parameter_name, str):
            return status_code, ERROR_INVALID_UVC_PARAMETER_NAME
        if isinstance(start, bool) or not isinstance(start, int):
            return status_code, ERROR_INVALID_START_VALUE
        if isinstance(end, bool) or not isinstance(end, int):
            return status_code, ERROR_INVALID_END_VALUE
        if isinstance(step, bool) or not isinstance(step, int):
            return status_code, ERROR_INVALID_STEP_VALUE
        if isinstance(mode, bool) or not isinstance(mode, int):
            return status_code, ERROR_INVALID_UVC_PARAMETER_MODE
        if isinstance(hold, bool) or not isinstance(hold, int):
            return status_code, ERROR_INVALID_HOLD_VALUE
        if not isinstance(image_save, bool):
            return status_code, ERROR_IMAGE_SAVE_VALUE
        if isinstance(save_format, bool) or not isinstance(save_format, str):
            return status_code, ERROR_IMAGE_SAVE_FORMAT
        if isinstance(save_path, bool) or not isinstance(save_path, str):
            return status_code, ERROR_INVALID_SAVE_PATH
        # if not save_path:
        #     return False, ERROR_MISSING_IMAGE_SAVE_PATH

        time.sleep(2)

        if not cls.streaming_initialised:
            cls.release_camera(camera_node)
            cls.streaming_initialised = False
            return status_code, ERROR_INITIALIZING_STREAM
        else:
            if image_save:
                current_time = datetime.datetime.now()
                current_time_split = current_time.strftime("%Y%m%d_%H%M%S")
                folder_name = f"Camera_api_out_{str(current_time_split)}"
                cls.main_folder = os.path.join(save_path, folder_name)
                try:
                    os.makedirs(cls.main_folder, 0o777, exist_ok=True)
                except PermissionError:
                    return status_code, ERROR_UNABLE_TO_CREATE_FOLDER

            UVC_PARAMETER_NAMES = ['BRIGHTNESS', 'CONTRAST', 'SHARPNESS', 'SATURATION', 'HUE', 'WHITE_BALANCE_BLUE_U', 'GAMMA', 'EXPOSURE',
                                   'GAIN', 'ZOOM', 'PAN', 'TILT',
                                   'FOCUS', 'BACKLIGHT', 'ROLL', 'IRIS']
            CAP_UVCPROPERTIES_NAME = [cv2.CAP_PROP_BRIGHTNESS, cv2.CAP_PROP_CONTRAST, cv2.CAP_PROP_SHARPNESS,
                                      cv2.CAP_PROP_SATURATION, cv2.CAP_PROP_HUE, cv2.CAP_PROP_WHITE_BALANCE_BLUE_U,
                                      cv2.CAP_PROP_GAMMA, cv2.CAP_PROP_EXPOSURE, cv2.CAP_PROP_GAIN, cv2.CAP_PROP_ZOOM,
                                      cv2.CAP_PROP_PAN, cv2.CAP_PROP_TILT, cv2.CAP_PROP_BACKLIGHT, cv2.CAP_PROP_FOCUS,
                                      cv2.CAP_PROP_ROLL, cv2.CAP_PROP_IRIS]
            if start >= end:
                step_sign_img = -1
                step = -step
            else:
                step_sign_img = 1
                step = step

            if parameter_name.upper() in UVC_PARAMETER_NAMES:
                UVC_PARAMETER_NAMES.index(parameter_name.upper())

            try:
                if image_save:
                    # if cls.main_folder.exists():
                    cls.child_folder = os.path.join(cls.main_folder, parameter_name)
                    os.makedirs(cls.child_folder, 0o777, exist_ok=True)
            except PermissionError:
                return status_code, ERROR_UNABLE_TO_CREATE_FOLDER

            for i in range(start, end + step_sign_img, step):
                try:
                    cls.cam_list[cls.cam_index.index(int(camera_node))].set(
                        CAP_UVCPROPERTIES_NAME[UVC_PARAMETER_NAMES.index(parameter_name.upper())], i, mode)
                except ValueError:
                    return status_code, ERROR_INVALID_UVC_PARAMETER_NAME  # unable to set the parameter
                time.sleep(hold)
                try:
                    if cls.frame1.any():
                        if image_save:
                            if save_format.lower() in supported_image_save_format:
                                current_time_image = str(datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
                                file_name = (str(parameter_name) + "_" + str(i) + "_" + current_time_image + "." +
                                             str(save_format))
                                save_image_path = os.path.join(cls.child_folder, file_name)
                                if save_format != 'raw':
                                    cv2.imwrite(save_image_path, cls.frame1)
                                    cls.frame1 = None
                                else:
                                    fp = open(save_image_path, 'wb+')
                                    fp.write(cls.frame1)
                                    fp.close()
                                    cls.frame1 = None
                            else:
                                return status_code, ERROR_IMAGE_SAVE_FORMAT  # unknown save format
                    if cls.exit_val:
                        break
                except Exception:
                    if NameError:
                        return status_code, ERROR_CAMERA_NOT_ASSIGNED  # camera not assigned
                    else:
                        return status_code, ERROR_UNABLE_TO_SET_UVC_PARAMETER_VALUE
            if cls.is_streaming_stopped(camera_node):
                return False, ERROR_INITIALIZING_STREAM
            else:
                return True, success_code

    @classmethod
    def set_uvc_default(cls, camera_node: int) -> tuple:
        """
            Usage:
                Sets the camera's UVC values to default.

            Parameters:
                - camera_node (int): Camera node obtained from get_connected_devices().

            Returns:
                tuple: Result of the operation. If successful, returns (True, 0). Otherwise, returns (False, error_code).
                       - If the UVC values are successfully set to default, returns (True, 0) as success code.
                       - If the camera is not assigned, returns (False, error_code 102).
                       - If an invalid camera node is provided, returns (False, error_code 201).
                       - If unable to set the UVC values to default, returns (False, error_code 122).
        """

        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_UNABLE_TO_SET_UVC_PARAMETER_VALUE_TO_DEFAULT = 122
        status_code = False
        success_code = 0

        if isinstance(camera_node, bool) or not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE

        try:
            supported_params = cls.get_supported_uvc_parameter(camera_node)[0]
            for param, values in supported_params.items():
                default_value = values[4]
                default_mode = values[5]
                cls.set_uvc(camera_node, param, default_value, default_mode)
                status_code = True
            return status_code, success_code
        except Exception:
            if NameError:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED
            else:
                return status_code, ERROR_UNABLE_TO_SET_UVC_PARAMETER_VALUE_TO_DEFAULT

    @classmethod
    def get_hid(cls, camera_node: int, hid_bytes: list) -> tuple:
        """
        Used to change the HID parameter of the e-con camera for the given node using HID commands.

        Parameters:
        - camera_node (int): Camera node obtained from get_connected_devices().
        - hid_bytes (list or tuple): List or tuple containing HID byte values.

        Returns:
        tuple: HID control value or error code.
               - If the HID parameter is successfully retrieved, returns the HID control value and 0 as the success code.
               - If there's an error while retrieving the HID parameter, returns False and the respective error code.
        """

        cls.get_response = None
        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_INVALID_HID_BYTES = 220
        ERROR_UNABLE_TO_GET_HID_VALUE = 116
        status_code = False
        success_code = True
        if not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE

        if not isinstance(hid_bytes, (list, tuple)):
            return status_code, ERROR_INVALID_HID_BYTES

        for byte_value in hid_bytes:
            if not isinstance(byte_value, int) or not 0 <= byte_value <= 255:
                return status_code, ERROR_INVALID_HID_BYTES

        try:
            # Open the device using path
            device_info = cls.cam_list[cls.cam_index.index(camera_node)].getDeviceInfo(camera_node)
            device_vendor_id = int('0x' + device_info[2], 16)
            device_product_id = int('0x' + device_info[3], 16)
        except Exception as e:
            return status_code, ERROR_CAMERA_NOT_ASSIGNED
        try:
            # Open the device using path
            cls.devices = hid.enumerate(device_vendor_id, device_product_id)

            if not cls.devices:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED  # device not found
            cls.device = hid.device()
            cls.device.open_path(cls.devices[0]["path"])
            get_command = [0x00]  # Initialize the get command with the header

            # Append HID bytes to the get command
            get_command.extend(hid_bytes)

            cls.device.write(get_command)
            cls.get_response = cls.device.read(65, 1000)
            if cls.get_response != []:
                if cls.get_response[6] == 1:
                    return cls.get_response, success_code
                else:
                    return status_code, cls.get_response, ERROR_UNABLE_TO_GET_HID_VALUE
            else:
                return status_code, ERROR_UNABLE_TO_GET_HID_VALUE
        except Exception:
            if NameError:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED
            elif ValueError:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED
            else:
                return status_code, ERROR_UNABLE_TO_GET_HID_VALUE  # unable to get the HID value

    @classmethod
    def set_hid(cls, camera_node: int, hid_bytes: list) -> tuple:

        """
            Used to change the HID parameter of the e-con camera for the given node using HID commands.

            Parameters:
            - camera_node (int): Camera node obtained from get_connected_devices().
            - hid_bytes (list or tuple): List or tuple containing HID byte values.

            Returns:
            tuple: HID control value or error code.
                   - If the HID parameter is successfully set, returns the HID control value and 0 as the success code.
                   - If there's an error while setting the HID parameter, returns False and the respective error code.
        """

        ERROR_CAMERA_NOT_ASSIGNED = 102
        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_INVALID_HID_BYTES = 220
        ERROR_UNABLE_TO_SET_HID = 117
        status_code = False
        success_code = True

        if not isinstance(camera_node, int):
            return status_code, ERROR_INVALID_CAMERA_NODE
        if not isinstance(hid_bytes, (list, tuple)):
            return status_code, ERROR_INVALID_HID_BYTES

        for byte_value in hid_bytes:
            if not isinstance(byte_value, int) or not 0 <= byte_value <= 255:
                return status_code, ERROR_INVALID_HID_BYTES
        try:
            # Open the device using path
            device_info = cls.cam_list[cls.cam_index.index(camera_node)].getDeviceInfo(camera_node)
            device_vendor_id = int('0x' + device_info[2], 16)
            device_product_id = int('0x' + device_info[3], 16)
        except Exception as e:
            return status_code, ERROR_CAMERA_NOT_ASSIGNED
        try:
            # Open the device using path
            cls.devices = hid.enumerate(device_vendor_id, device_product_id)

            if not cls.devices:
                return status_code, ERROR_CAMERA_NOT_ASSIGNED  # camera not found

            cls.device = hid.device()
            cls.device.open_path(cls.devices[0]["path"])

            set_command = [0x00]  # Initialize the set command with the header

            # hid_bytes_hex = [byte_value if isinstance(byte_value, int) else int(byte_value, 16) for byte_value in hid_bytes]

            # Append HID bytes to the set command
            set_command.extend(hid_bytes)
            # Write the set command to the device
            cls.device.write(set_command)
            cls.set_response = cls.device.read(65, 1000)

            if cls.set_response:
                if cls.set_response[6] == 1:
                    return cls.set_response, success_code
                else:
                    return status_code, cls.set_response, ERROR_UNABLE_TO_SET_HID

            else:
                return status_code, ERROR_UNABLE_TO_SET_HID

        except Exception as e:
            return status_code, ERROR_CAMERA_NOT_ASSIGNED  # unable to set the HID

    @classmethod
    def convert_y16_to_rgb(cls, frame):
        """
            Method Name: convert_y16_to_rgb
            Description: This method converts Y16 or Y8 format to RGB for rendering and saving image.
            :param frame: Frame to be converted from Y16 or Y8 format to RGB.
            :type frame: numpy.ndarray
            :return: The converted frame in RGB format.
            :rtype: numpy.ndarray
        """
        return cv2.convertScaleAbs(frame, alpha=0.2490234375)

    @classmethod
    def convert_y12_to_y8(cls, frame):
        """
            Method Name: convert_y12_to_y8
            Description: This method converts a Y12 frame to a Y8 frame.
            :param frame: The Y12 frame to be converted.
            :type frame: numpy.ndarray
            :return: The converted Y8 frame.
            :rtype: numpy.ndarray
        """
        try:
            y8_frame_height = frame.shape[0]
            y8_frame_width = frame.shape[1]
            y8_frame = np.zeros(shape=(y8_frame_height, y8_frame_width), dtype=np.uint8)
            raw_bytes = frame.tobytes()  # converting two dimensional mat data to byte array
            row = frame.shape[0]
            column = frame.shape[1]
            filtered_bytes = np.frombuffer(raw_bytes, dtype=np.uint8)
            filtered_bytes = np.reshape(filtered_bytes, (-1, 3))
            filtered_bytes = np.delete(filtered_bytes, 2, 1)
            filtered_bytes = np.reshape(filtered_bytes, -1)
            m = 0
            for i in range(0, row):
                y8_frame[i,] = filtered_bytes[m:m + column]
                m += column
            return y8_frame  # Converting back to two-dimensional matrix
        except:
            print("unable to convert")

    @classmethod
    def show_preview(cls, node, duration, show_FPS, stop_event):
        global stop_time
        cls.exit_val = False
        time.sleep(1)
        ERROR_NO_DEVICES_FOUND = 101
        try:
            time_second = 1
            frame_count = 0
            fps_start_time = time.time()
            fps_show_time = time.time() + time_second
            fps = 0
            if duration != 0:
                stop_time = time.time() + duration
            for i in range(20):
                ret, cls.frame = cls.cam_list[cls.cam_index.index(int(node))].read()
            while True:
                ret, cls.frame = cls.cam_list[cls.cam_index.index(int(node))].read()
                cls.frame.any()
                # Stop event check here
                if stop_event.is_set():
                    break  # Gracefully exit the loop if stop event is set
                frame_count += 1

                if time.time() > fps_show_time:
                    fps = frame_count
                    frame_count = 0
                    fps_show_time = time.time() + time_second

                if "".join(
                        [chr((int(cls.cam_list[cls.cam_index.index(int(node))].get(cv2.CAP_PROP_FOURCC)) >> 8 * i)
                             & 0xFF) for i in range(4)]) == 'UYVY':
                    cls.frame1 = cv2.cvtColor(cls.frame, cv2.COLOR_YUV2BGR_UYVY)
                elif "".join(
                        [chr((int(cls.cam_list[cls.cam_index.index(int(node))].get(cv2.CAP_PROP_FOURCC)) >> 8 * i)
                             & 0xFF) for i in range(4)]) == 'YUY2':
                    cls.frame1 = cv2.cvtColor(cls.frame, cv2.COLOR_YUV2BGR_YUY2)
                elif "".join(
                        [chr((int(cls.cam_list[cls.cam_index.index(int(node))].get(cv2.CAP_PROP_FOURCC)) >> 8 * i)
                             & 0xFF) for i in range(4)]) == 'Y12':
                    cls.frame1 = cls.convert_y12_to_y8(cls.frame)
                elif "".join(
                        [chr((int(cls.cam_list[cls.cam_index.index(int(node))].get(cv2.CAP_PROP_FOURCC)) >> 8 * i)
                             & 0xFF) for i in range(4)]).strip() == 'Y16':
                    cls.frame1 = cls.convert_y16_to_rgb(cls.frame)
                else:
                    cls.frame1 = cls.frame

                if show_FPS:
                    cv2.putText(cls.frame1, f"FPS: {fps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                try:
                    cv2.imshow("Preview - " + str(node), cls.frame1)
                    cls.streaming_initialised = True
                except AttributeError:
                    return False, ERROR_NO_DEVICES_FOUND

                except cv2.error:
                    return False, ERROR_NO_DEVICES_FOUND
                except:
                    continue

                if duration != 0:
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        cls.streaming_initialised = False
                        cls.streaming_status[node] = False
                        break
                    if stop_time <= int(time.time()):
                        cls.streaming_status[node] = False
                        cls.streaming_initialised = False
                        break
                else:
                    if cv2.waitKey(1) & 0xFF == ord('q') or cv2.waitKey(1) & 0xFF == ord('Q'):
                        cls.streaming_status[node] = False
                        cls.streaming_initialised = False
                        cls.exit_val = True
                        break
        except AttributeError:
            cv2.destroyAllWindows()
            cls.streaming_status[node] = False  # Streaming stopped due to error
            return False, ERROR_NO_DEVICES_FOUND  # please assign the camera
        except ValueError:
            cv2.destroyAllWindows()
            cls.streaming_status[node] = False  # Streaming stopped due to error
            return False, ERROR_NO_DEVICES_FOUND  # please assign the camera
        except BaseException:
            cv2.destroyAllWindows()
            cls.streaming_status[node] = False  # Streaming stopped due to error
            return False, ERROR_NO_DEVICES_FOUND
        finally:
            cv2.destroyAllWindows()
            # cls.cam_list[cls.cam_index.index(int(node))].release()
            cls.streaming_status[node] = False
            cls.streaming_status[node] = False
            cls.cam_list.clear()
            cls.cam_index.clear()
            cls.cap = None

    @classmethod
    def show_stream(cls, camera_node=-1, duration=0, show_FPS=False):
        ERROR_INVALID_CAMERA_NODE = 201
        ERROR_INVALID_DURATION = 216
        ERROR_INVALID_FPS_SHOW = 217

        if isinstance(camera_node, bool) or not isinstance(camera_node, int):
            return False, ERROR_INVALID_CAMERA_NODE
        if isinstance(duration, bool) or not isinstance(duration, int):
            return False, ERROR_INVALID_DURATION
        if not isinstance(show_FPS, bool):
            return False, ERROR_INVALID_FPS_SHOW

        # Check if a previous stream exists for this camera node and stop it if so
        if camera_node in cls.streaming_threads:
            cls.stop_events[camera_node].set()  # Signal the thread to stop
            cls.streaming_threads[camera_node].join()  # Wait for the thread to finish
            cls.stop_events[camera_node].clear()  # Reset the event for future use

        # Create a new stop event for this camera node
        cls.stop_events[camera_node] = Event()
        cls.streaming_status[camera_node] = True

        # Start a new thread for streaming
        cls.streaming_threads[camera_node] = Thread(
            target=cls.show_preview,
            args=(camera_node, duration, show_FPS, cls.stop_events[camera_node]),  # Pass stop_event here
        )
        cls.streaming_threads[camera_node].start()

        return True

    @classmethod
    def is_streaming_stopped(cls, camera_node):
        """
        Checks if the streaming for the given camera_node has stopped.

        Parameters:
            - camera_node (int): Camera node for which streaming status needs to be checked.

        Returns:
            bool: True if streaming has stopped, False otherwise.
        """
        return not cls.streaming_status.get(camera_node, False)

    @classmethod
    # def save_image(cls, save_path: str, file_name: str, save_format: str) -> bool:
    #
    #     """
    #     Usage:
    #         Save an image captured from the camera stream.
    #
    #     Parameters:
    #          save_path (str): Path to save the captured image.
    #          save_format (str): Save format for the image to be saved.
    #          file_name (str): name of the file to the saved.
    #
    #     Returns:
    #          bool: True if the image is successfully saved, False otherwise.
    #     """
    #
    #     ERROR_IMAGE_SAVE_FORMAT = 214
    #     ERROR_INVALID_SAVE_PATH = 218
    #     ERROR_INVALID_IMAGE_SAVE_NAME = 219
    #     ERROR_UNABLE_TO_SAVE_IMAGE = 115
    #     ERROR_MISSING_IMAGE_SAVE_PATH = 123
    #
    #     status_code = False
    #     success_code = 0
    #     supported_image_save_format = ['bmp', 'jpg', 'raw', 'png']
    #
    #     if isinstance(save_format, bool) or not isinstance(save_format, str):
    #         return status_code, ERROR_IMAGE_SAVE_FORMAT
    #     if isinstance(save_path, bool) or not isinstance(save_path, str):
    #         return status_code, ERROR_INVALID_SAVE_PATH
    #     if not isinstance(save_path, str) or not save_path:
    #         return False, ERROR_MISSING_IMAGE_SAVE_PATH
    #     if isinstance(file_name, bool) or not isinstance(file_name, str):
    #         return status_code, ERROR_INVALID_IMAGE_SAVE_NAME
    #     try:
    #         while not cls.streaming_initialised:
    #             continue
    #         current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    #         if save_format in supported_image_save_format:
    #             file_name = f"{file_name}_{current_time}.{save_format}"
    #             save_image_path = os.path.join(save_path, file_name)
    #
    #             if cv2.imwrite(save_image_path, cls.frame1):
    #                 status_code = True
    #                 return status_code, success_code
    #         else:
    #             return status_code, ERROR_IMAGE_SAVE_FORMAT  # unknown save format
    #     except Exception as e:
    #         print(e)
    #         return status_code, ERROR_UNABLE_TO_SAVE_IMAGE

    def save_image(cls, save_path: str, file_name: str, save_format: str) -> bool:
        """
        Usage:
            Save an image captured from the camera stream.

        Parameters:
             save_path (str): Path to save the captured image.
             save_format (str): Save format for the image to be saved.
             file_name (str): Name of the file to be saved.

        Returns:
             bool: True if the image is successfully saved, False otherwise.
        """

        ERROR_IMAGE_SAVE_FORMAT = 214
        ERROR_INVALID_SAVE_PATH = 218
        ERROR_INVALID_IMAGE_SAVE_NAME = 219
        ERROR_UNABLE_TO_SAVE_IMAGE = 115
        ERROR_MISSING_IMAGE_SAVE_PATH = 123

        status_code = False
        success_code = 0
        supported_image_save_format = ['bmp', 'jpg', 'raw', 'png']

        if isinstance(save_format, bool) or not isinstance(save_format, str):
            return status_code, ERROR_IMAGE_SAVE_FORMAT
        if isinstance(save_path, bool) or not isinstance(save_path, str):
            return status_code, ERROR_INVALID_SAVE_PATH
        if not isinstance(save_path, str) or not save_path:
            return False, ERROR_MISSING_IMAGE_SAVE_PATH
        if isinstance(file_name, bool) or not isinstance(file_name, str):
            return status_code, ERROR_INVALID_IMAGE_SAVE_NAME

        try:
            while not cls.streaming_initialised:
                continue
            current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{file_name}_{current_time}.{save_format}"
            save_image_path = os.path.join(save_path, file_name)

            if save_format in supported_image_save_format:
                if save_format == 'raw':
                    # Save raw image data
                    with open(save_image_path, 'wb') as f:
                        f.write(cls.frame1.tobytes())
                    status_code = True
                else:
                    # Save using OpenCV for other formats
                    if cv2.imwrite(save_image_path, cls.frame1):
                        status_code = True
                    else:
                        return status_code, ERROR_UNABLE_TO_SAVE_IMAGE
                return status_code, success_code
            else:
                return status_code, ERROR_IMAGE_SAVE_FORMAT  # unknown save format
        except Exception:
            return status_code, ERROR_UNABLE_TO_SAVE_IMAGE