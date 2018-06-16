import base64
import cv2
import io
import magic
import numpy as np
import os
import sys
import uuid

from origami import exceptions, constants


def validate_token(token):
    """ Validate the provided token

    Check if the provided token in argument is valid for app

    Args:
        token: Token string which is to be validated

    Returns:
        token: Token if validated else an exception is raised

    Raises:
        MismatchTypeException: Error occurred when correct type of token is not
             supplied.
        InvaidTokenException: Raised when token to be validated is invalid
    """
    try:
        assert isinstance(token, str)
    except AssertionError:
        raise exceptions.MismatchTypeException(
            "TOKEN type mismatch: string expected given %s".format(type(token)))
    try:
        if (token.split(':')[0] in constants.DEMO_DEPLOYMENT_TYPE):
            assert int(token.split(':')[3])
            assert int(token.split(':')[4])
        else:
            raise AssertionError
    except AssertionError:
        raise exceptions.InvalidTokenException(
            "TOKEN invalid: Required format %s".format(constants.TOKEN_FORMAT))
    return token


def parse_target(token):
    """ Parses target of the application from the application token

    This function assumes that the token you are providing has been validated
    earlier using `validate_token` function, so it does not attempt to check
    validity.

    Args:
        token: Token to extract the target from

    Returns:
        target: Target of the application
            either gh or nongh.

    Raises:
        InvalidTokenException: The token provided is invalid, it only checks it
            corresponding to target
    """
    if (token.split(':')[0] == 'gh'):
        target = 'local'
    elif (token.split(':')[0] == 'nongh'):
        target = 'remote'
    else:
        raise exceptions.InvalidTokenException(
            "TOKEN invalid: Required format %s".format(constants.TOKEN_FORMAT))

    return target


def get_image_as_numpy_arr(image_files_arr):
    """ Takes an array of image files and returns numpy array for the same

    This function is a helper function which takes in image files from users
    request and returns the corresponding numpy array for images.

    Args:
        image_files_arr: Array of image files from user request

    Returns:
        image_np_arr: Array of numpy image array corresponding to given
            image files.
    """
    images_np_arr = []

    for index, image_object in enumerate(image_files_arr):
        in_memory = io.BytesIO()
        image_object.save(in_memory)
        data = np.fromstring(in_memory.getvalue(), dtype=np.uint8)
        color_image_flag = 1
        image = cv2.imdecode(data, color_image_flag)

        images_np_arr.append(image)

    return images_np_arr


def check_if_string(data):
    """
    Takes a data as argument and checks if the provided argument is an
    instance of string or not

    Args:
        data: Data to check for.

    Returns:
        result: Returns a boolean if the data provided is instance or not
    """
    if sys.version_info[0] == 2:
        return isinstance(data, basestring)
    else:
        return isinstance(data, str)


def strict_check_array_of_string(data):
    """
    Checks if the argument provided is a list/tuple of string.

    Args:
        data: Data to be validated corresponding to array of string

    Raises:
        MismatchTypeException: Exception that the required type did not match
            catch this to handle non array of strings.
    """
    if not isinstance(data, (list, tuple)):
        raise exceptions.MismatchTypeException(
            "send_text_array can only accept an array or a tuple")

    if not all(check_if_string(element) for element in data):
        raise exceptions.MismatchTypeException(
            "send_text_array expects a list or tuple of string")


def get_base64_image_from_file(file_path):
    """
    Takes image file_path as an argument and returns a base64 encoded string
    corresponding to the image.

    Args:
        file_path: Image path

    Returs:
        src: base64 encoded image.

    Raises:
        InvalidMimeTypeException: Image does not have a vaild mime type to
            process.
        InvalidFilePathException: File trying to access is not found.
    """
    try:
        with open(file_path, "rb") as file:
            mime = magic.Magic(mime=True)
            content_type = mime.from_file(file_path)
            if content_type == constants.MIME_TYPE_JPEG or \
                content_type == constants.MIME_TYPE_JPG:
                src = constants.IMAGE_JPEG_BASE64_SIG
            elif content_type == constants.MIME_TYPE_PNG:
                src = constants.IMAGE_PNG_BASE64_SIG
            else:
                raise exceptions.InavalidMimeTypeException(
                    "Not a valid mime type for image : {}".format(content_type))
            src += str(base64.b64encode(file.read()))
            return src

    except FileNotFoundError:
        raise exceptions.InvalidFilePathException(
            "No file found matching the path {}".format(file_path))


def get_base64_image_from_nparr(image_nparr):
    """
    Takes a numpy image array as input and returns base64 encoded image string

    Args:
        image_nparr: Numpy array for the image.

    Returns:
        image_src: base64 encoded image string

    Raises:
        FileHandlingException: Error while handling file created to get base64
            encoded string from np array using cv2
    """
    try:
        path = os.path.join(constants.TMP_DIR_BASE_PATH, str(uuid.uuid4()))
        cv2.imwrite(path, image_nparr)
        img_src = get_base64_image_from_file(path)
        os.remove(path)
        return img_src

    except OSError:
        raise exceptions.FileHandlingException(
            "Cannot write NP array to the path {} using cv2".format(path))


def validate_cache_path(cache_path):
    """
    Validates cache path, checks if the path provided is a directory and has the
    required permissions for reading and writing data.

    Args:
        cache_path: Path to be validated

    Returns:
        cache_path: Validated cache path as absolute path.

    Raises:
        InvalidCachePathException: The provided cache path is not valid, either
            due to the permissions or is not a directory at all.
    """
    if os.path.isdir(cache_path):
        cache_path = os.path.abspath(cache_path)
        if os.access(cache_path, os.R_OK) and os.access(cache_path, os.W_OK):
            return cache_path
        else:
            raise exceptions.InvalidCachePathException(
                "Permission for cache_path({}) provided are not acceptable.".
                format(cache_path))
    else:
        raise exceptions.InvalidCachePathException(
            "Cache Path provided is not a Directory :: {}".format(cache_path))
