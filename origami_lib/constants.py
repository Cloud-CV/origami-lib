ORIGAMI_SERVER_INJECTION_PATH = "/inject"
ORIGAMI_SERVER_BASE_URL = "localhost:8000"
DEFAULT_PORT = 9001

LOCAL_TARGET_REGEXP = '^localhost|127\.0\.0\..|0\.0\.0\.0'

HTTP_ENDPOINT = "http://"
HTTPS_ENDPOINT = "https://"

DEMO_DEPLOYMENT_TYPE = ["gh", "nongh"]
LOCAL_TARGET = 'local'
REMOTE_TARGET = 'remote'

TOKEN_FORMAT = "nongh:0.0.0.0:1814173:5001:9001:0.0.0.0"

ORIGAMI_DEFAULT_EVENT_ROUTE = "/event"

INPUT_IMAGE_ARRAY_FILEPATH_MODE = "file_path"
INPUT_IMAGE_ARRAY_NPARRAY_MODE = "numpy_array"

REQUESTS_JSON_HEADERS = {'Content-Type': 'application/json'}

DEFAULT_ORIGAMI_RESPONSE_TEMPLATE = [{
    "Copyright": """
@CloudCV Origami Demo
"""
}]

DEFAULT_DATA_TYPE_KEY = "data"
TERMINAL_DATA_TYPE_KEY = "terminalData"

REQUEST_SOCKET_ID_KEY = "socket-id"

IMAGE_JPEG_BASE64_SIG = "data:image/jpeg;base64,"
IMAGE_PNG_BASE64_SIG = "data:image/png;base64,"

MIME_TYPE_JPEG = "image/jpeg"
MIME_TYPE_JPG = "image/jpg"
MIME_TYPE_PNG = "image/png"

TMP_DIR_BASE_PATH = "/tmp"

GLOBAL_CACHE_PATH = "/tmp"

TEXT_CACHE_FILE = "text.cache"
IMAGE_CACHE_FILE = "image.cache"
IMAGE_BLOBS_DIR = "img_blobs"
