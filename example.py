"""
Python MMR REST-API client. Use with web-based demo at https://trafficeye.ai.
"""
import json
import requests
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, unquote
import os
from typing import List

def is_valid_url(input_str):
    # Decode the URL before checking
    decoded_url = unquote(input_str)
    # Check if the input string is a valid URL
    parsed_url = urlparse(decoded_url)
    return bool(parsed_url.scheme) and bool(parsed_url.netloc)


class MmrApiClient:

    def __init__(self, server_url):
        """
        Initialize by storing url
        :param server_url: address of MMR web server, e.g. https://trafficeye.ai.
        """
        self.server_url = server_url

    def info(self, api_key: str):
        """
        Query web server status information.
        :param email: Your login email as created at 'https://trafficeye.ai/user/licenses'.
        :param password: The password you received to the specified email.
        :return: JSON response structure
        """
        headers = {"apikey": api_key}
        r = requests.get(self.server_url + "info", headers=headers, timeout=60)

        if r.status_code != 200:
            print(f"{r.status_code} {r.reason} - {r.text}")
            raise ValueError(f"Server returned error code {r.status_code}")

        info_result = json.loads(r.content.decode("utf-8"))
        return info_result

    def recognition(self, api_key: str,
                    image_path: str,
                    save_image: Optional[bool] = False,
                    save_plate_text: Optional[bool] = True,
                    tasks: List[str] = ["DETECTION", "OCR", "MMR"],
                    ocr_module_id: Optional[int] = 801):
        """
        Send image file to server for processing license plate based detection. If all optional inputs are set, the web server won't run
        detection, but will only process the selected vehicle.
        :param email: Your API Key available at 'https://trafficeye.ai/user/licenses'.
        :param image_path: Path to the image.
        :param save_image: If True, the server will save the image.
        :param save_plate_text: If False, the server will not save the license plate text in the request history.
        :param tasks: List of tasks to be performed on the image. Possible values are "DETECTION", "OCR", "MMR".
        :param ocrModuleId: ID of the OCR module to be used. Default is 801 - Global OCR.
        :return: JSON response structure
        """
        file_buffer = None
        # Check if the input string is a valid file path
        if os.path.isfile(image_path):
            with open(image_path, "rb") as f:
                file_buffer = f.read()
        elif is_valid_url(image_path):
            # Fetch the image from the URL
            response = requests.get(image_path, timeout=60)

            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                file_buffer = response.content
        else:
            raise ValueError("Input is neither a valid file path nor a URL.")
        if file_buffer is None:
            raise ValueError("Failed to read image.")

        files = {
            "file": (str(image_path), file_buffer)
        }
        headers = {
            'apiKey': api_key,
        }
        request =  {
            "saveImage": save_image, 
            "savePlateText": save_plate_text,
            "tasks": tasks,
            "ocrModuleId": ocr_module_id,
        }
        # Prepare the payload
        payload = {}
        payload['request'] = json.dumps(request)

        r = requests.post(self.server_url + "recognition", data=payload, files=files, headers=headers, timeout=60)

        if r.status_code != 200:
            error_message = r.reason
            if r.text:
                returned_json = json.loads(r.text)
                if "errorMessage" in returned_json:
                    error_message = returned_json["errorMessage"]
            raise ValueError(f"Server returned error code {r.status_code} : {error_message}")

        classification = json.loads(r.content.decode("utf-8"))
        return classification

if __name__ == "__main__":
    # SETUP VARIABLES BEFORE RUNNING
    IMAGE_PATH = "YOUR_IMAGE_PATH"
    NET_ADDRESS = "https://trafficeye.ai/"
    API_KEY = "YOUR_API_KEY"

    if IMAGE_PATH == Path("") or API_KEY == "":
        raise ValueError("You must set your API key and image path prior to running this script.")

    client = MmrApiClient(NET_ADDRESS)
    info = client.info(API_KEY)
    print(info)
    print("Recognition:")
    api_response = client.recognition(API_KEY, IMAGE_PATH)
    print(api_response)
