import ast
import cv2
import hashlib
import numpy as np
import os
import shutil
import uuid

from . import constants, exceptions, utils


class OrigamiCache(object):
    """ Implements pipeline functions for Origami
    Handles various pipeline functions such as fetching and saving data from
    and to cache.

    This essentially is not cache since all the storage is done on the disk,
    and since IO are resource expensive this does not essentially increases
    speed in any sense. The main use of this here is for persistence, this
    can be also for large amount of data wherein it is not possible to store
    all of it in the memory.

    .. code-block:: python

        from origami import OrigamiCache

        cache = OrigamiCache()
        arr = ["Hello, ", "World!"]
        cache.save_text_array_to_cache(arr)
        arr = ''.join(arr)
        new_arr = cache.load_text_array_from_cache()
        print(new_arr)

    Attrs:
        global_cache_path: Path for all the file interaction for pipeline \
            functions.
        cache_id: ID for the current cache object.
        cache_dir: Cache dir corresponding to global_cache_path and cache_id.
    """

    def __init__(self, cache_path=constants.GLOBAL_CACHE_PATH):
        self.global_cache_path = utils.validate_cache_path(cache_path)
        self.cache_id = ""
        self.cache_dir = ""
        self._create_cache()

    def _create_cache(self):
        """
        Create a cache space in global_cache_path and return the ID/directory to
        that.

        Returns:
            cache_id: Cache ID to reference the cache in future.

        Raises:
            FileHandlingException: Exception during creating directory for the \
                cache.
        """
        self.cache_id = uuid.uuid4().hex
        self.cache_dir = os.path.join(self.global_cache_path, self.cache_id)
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
        except OSError:
            self.cache_dir = ""
            raise exceptions.FileHandlingException(
                "Error when creating directory for cache :: {}.".format(
                    self.cache_dir))

        return self.cache_id

    def delete_current_cache(self):
        """
        Delete the cache identifiers, cache_id and cache_dir
        """
        try:
            if self.cache_dir:
                shutil.rmtree(self.cache_dir)
                self.cache_dir = ""
            self.cache_id = ""
        except Exception:
            pass

    def new_cache(self):
        """
        Create a cache space in global_cache_path and return the ID/directory to
        that.

        Returns:
            cache_id: Cache ID to reference the cache in future.
        """
        self.delete_current_cache()
        cache_id = self._create_cache()
        return cache_id

    def __write_python_list_to_file(self, file_path, text_array):
        """
        Takes a file path and a list of strings and writes the whole data
        structure to the file. This file is internal to the class and hence
        assumes that any argument provided to it must be sanitized and checked
        for earlier.

        This function does nothing more than just writing the data structure to
        the file.

        Args:
            file_path(str): Path to store the data to
            text_array(list): A list of strings to be stored in the file.
        """
        with open(file_path, "w") as file:
            # Write it to the cache file as an array of string.
            text_array = ['"{}"'.format(x) for x in text_array]
            file.write('[' + ', '.join(text_array) + ']')

    def __read_from_file_as_python_list(self, file_path):
        """
        Takes a file_path(A cache file) and parses it for a python list using
        ast module.

        Args:
            file_path: Path of the file to parse.

        Raises:
            MalformedCacheException: The cache file we are trying to parse is \
                malformed.
            InvalidCachePathException: The path provided to read does not exist.
        """
        if os.path.exists(file_path):
            with open(file_path, "r") as cache_file:
                content = cache_file.read()
                try:
                    eval_ds = ast.literal_eval(content.strip())
                    return eval_ds
                except ValueError:
                    raise exceptions.MalformedCacheException(
                        "Text cache does not contain a valid string to be\
                        evaluated")
        else:
            raise exceptions.InvalidCachePathException(
                "No valid cache file found :: {}".format(file_path))

    def save_text_array_to_cache(self, text_array):
        """
        Takes an array of string and saves it to cache file on the disk.
        This checks first for the validity of the text_array provided and then
        calls a function to write to the file.

        Args:
            text_array: array of strings to be saved in the text file cache.
        """
        utils.strict_check_array_of_string(text_array)
        text_cache_path = os.path.join(self.cache_dir,
                                       constants.TEXT_CACHE_FILE)

        self.__write_python_list_to_file(text_cache_path, text_array)

    def load_text_array_from_cache(self):
        """
        Load the text array from the cache file and return it.

        Returns:
            text_arr (list): Evaluated data structure from the text cache file \
                , in this case it corresponds to the text array.

        Raises:
            MalformedCacheException: Exception during parsing the data \
                structure from text cache file.

            InvalidCachePathException: The path for cache we obtained is not \
                present or there is nothing to load fro the cache path.
        """
        text_cache_path = os.path.join(self.cache_dir,
                                       constants.TEXT_CACHE_FILE)

        text_arr = self.__read_from_file_as_python_list(text_cache_path)
        return text_arr

    def __create_blobs_from_image_objects(self, image_objects_arr):
        """
        Takes in an array of image_object like the one retrieved from the
        request files and saves it to disk in the cache directory as a blob.
        Each blob has a name which corresponds to the MD5 hash of the image
        file. This ensures that no duplicate files are stored twice and uses
        the same blobs for reference.

        After saving the blobs to image blobs cache directory, it writes all the
        blobs hash to a file image.cache which can then be used to lookup for
        the available blobs. This file have a structure wherein it contains the
        blobs in the form of python list. So to read this use the function
        __read_from_file_as_python_list(). It will return
        a python list of blobs hash.

        Args:
            image_objects_arr: An array of image object(should be checked \
                before here for type) which will be cached by creating blobs \
                from the file.

        Returns:
            image_blobs_hash: A python list containing the blobs hash which \
                are saved into the image cache directory.

        Raises:
            BlobCreationException: Each image_object is converted to blob to \
                be saved individually this exception is thrown when there is \
                an error during this process for any image object.
        """
        image_blobs_hash = []
        image_cache_dir = os.path.join(self.cache_dir,
                                       constants.IMAGE_BLOBS_DIR)
        if not os.path.exists(image_cache_dir):
            os.makedirs(image_cache_dir)
        try:
            for image_object in image_objects_arr:
                image_object.seek(0)
                blob_hash = hashlib.md5(image_object.read()).hexdigest()

                image_blobs_hash.append(blob_hash)
                image_blob_path = os.path.join(image_cache_dir, blob_hash)
                with open(image_blob_path, "w+b") as file:
                    image_object.seek(0)
                    file.write(image_object.read())
                    image_object.seek(0)

        except Exception as e:
            raise exceptions.BlobCreationException(
                "Exception occurred while creating blobs from image object \
                array : {}".format(e))

        image_cache_file = os.path.join(self.cache_dir,
                                        constants.IMAGE_CACHE_FILE)
        self.__write_python_list_to_file(image_cache_file, image_blobs_hash)

        return image_blobs_hash

    def save_image_file_array_to_cache(self, image_objects):
        """
        Save an array of image to the global origami cache. The provided image
        inputs should be a list/tuple of images.

        Args:
            image_objects: list/tuple of images to be saved.

        Raises:
            MismatchTypeException: Image objects in the argument should be a \
                python list or a tuple. THis is raised when this type is \
                mismatched.
        """
        if not isinstance(image_objects, (list, tuple)):
            raise exceptions.MismatchTypeException(
                "send_text_array can only accept an array or a tuple")

        return self.__create_blobs_from_image_objects(image_objects)

    def load_image_file_paths_from_cache(self):
        """
        Gives the list of image blobs paths from the cache.

        Returns:
            image_file_paths: Image file paths stored in the cache as a list.
        """
        image_cache_file_path = os.path.join(self.cache_dir,
                                             constants.IMAGE_CACHE_FILE)
        blob_hash_list = self.__read_from_file_as_python_list(
            image_cache_file_path)

        image_file_paths = []
        for blob_hash in blob_hash_list:
            image_file_paths.append(
                os.path.join(self.cache_dir, constants.IMAGE_BLOBS_DIR,
                             blob_hash))

        return image_file_paths

    def load_image_nparr_from_cache(self):
        """
        Gives the list of image as numpy array from the cache.

        Returns:
            image_nparr_list: Image stored in the caches as numpy array.
        """
        image_file_paths = self.load_image_file_paths_from_cache()
        image_nparr_list = []
        for image_path in image_file_paths:
            image = cv2.imread(image_path)
            image_nparr_list.append(np.array(image))

        return image_nparr_list
