from flask import *
from flask_cors import CORS, cross_origin
import requests
import subprocess
import hashlib
import random
import base64
import magic
import shutil
import cv2
import sys
import os
import ast
import glob
import io
import numpy as np
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

CVFY_INJECTION_SUBPATH = '/inject'

app = Flask(__name__)
cors = CORS(app)
mime = magic.Magic(mime=True)

#################################
## common validation functions ##
#################################

def validateTOKEN(function_name):
    try:
        assert isinstance(TOKEN, str)
    except Exception as e:
        if (e.__class__.__name__ == 'NameError'):
            raise NameError("cvfy [Error Code: 001] => TOKEN undefined: {0} called before registering the app".format(function_name))
        elif (e.__class__.__name__ == 'AssertionError'):
            raise AssertionError("cvfy [Error Code: 002] => TOKEN not a string: {0} called with an invalid TOKEN value".format(function_name))
    try:
        if (TOKEN.split(':')[0] == 'gh'):
            assert int(TOKEN.split(':')[3])
            assert int(TOKEN.split(':')[4])
        elif (TOKEN.split(':')[0] == 'nongh'):
            assert int(TOKEN.split(':')[3])
            assert int(TOKEN.split(':')[4])
        else:
            raise AssertionError
    except Exception as e:
        if (e.__class__.__name__ == 'AssertionError'):
            raise ValueError("cvfy [Error Code: 003] => Malformed Token")

def validate_socket_id(request):
    try:
        if not request.form['socket-id']:
            raise Exception("cvfy [Error Code: 011] => field socket-id not found in the incoming request")
    except:
        raise Exception("cvfy [Error Code: 011] => field socket-id not found in the incoming request")

##########
## CORS ##
##########

def crossdomain(*args, **kwargs):
    return (cross_origin)

####################
## app decorators ##
####################

def override_route(route):
    def wrapper(*args, **kwargs):
        return (route('/event', methods=['POST', ]))
    return wrapper

def override_run(TOKEN):
    def wrapper(*args, **kwargs):
        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(int(TOKEN.split(':')[4]))
        print ("running on port: {}".format(TOKEN.split(':')[4]))
        IOLoop.instance().start()
    return (wrapper)

##################
## app register ##
##################

def register(APP_TOKEN):
    global TOKEN
    TOKEN = APP_TOKEN
    validateTOKEN(sys._getframe().f_code.co_name)
    global CVFY_TARGET
    if (TOKEN.split(':')[0] == 'gh'):
        CVFY_TARGET = 'local'
    elif (TOKEN.split(':')[0] == 'nongh'):
        CVFY_TARGET = 'remote'
    else:
        raise Exception("cvfy [Error Code: 012] => Malformed Token - Cannot set Target")

    app.listen = override_route(app.route)
    app.run = override_run(TOKEN)
    return (app)


########################
## pipeline functions ##
########################

def transformToLocalPath(image_object_array):
    path_to_use = '/tmp/{}/'.format(getUniqueCacheId())
    subprocess.Popen('mkdir -p {}'.format(path_to_use), shell=True).wait()
    array_of_paths_to_send_back = []
    for index, image_object in enumerate(image_object_array):
        extension = ''
        if (image_object.content_type == 'image/png'):
            extension = '.png'
        elif (image_object.content_type == 'image/jpg' or image_object.content_type == 'image/jpeg'):
            extension = '.jpg'
        array_of_paths_to_send_back.append(path_to_use + str(index) + extension)
        with open(path_to_use + str(index) + extension, 'wb') as file:
            image_object.seek(0)
            file.write(image_object.read())
            image_object.seek(0)
    return (array_of_paths_to_send_back)

def transformToNumpyArrays(image_object_array):
    numpy_arrays_to_send_back = []
    for index, image_object in enumerate(image_object_array):
        in_memory = io.BytesIO()
        image_object.save(in_memory)
        data = np.fromstring(in_memory.getvalue(), dtype=np.uint8)
        color_image_flag = 1
        img = cv2.imdecode(data, color_image_flag)
        numpy_arrays_to_send_back.append(img)
    return (numpy_arrays_to_send_back)

def getUniqueCacheId():
    md5_store = []
    text_array = []
    image_object_array = []
    i = 0
    try:
        while True:
            text_array.append(request.form['input-text-{}'.format(i)])
            i += 1
    except Exception as e:
        pass
    i = 0
    try:
        while True:
            image_object_array.append(request.files['input-image-{}'.format(i)])
            i += 1
    except Exception as e:
        pass
    for text_input in text_array:
        md5_store.append(hashlib.md5(text_input).hexdigest())
    for image_object in image_object_array:
        image_object.seek(0)        
        md5_store.append(hashlib.md5(image_object.read()).hexdigest())
        image_object.seek(0)        

    return hashlib.md5(
        reduce((lambda x, y: x + y), [
            str(reduce(lambda x, y: ord(x) ^ ord(y) 
            if isinstance(x, str) else x ^ ord(y), temp)) 
            for temp in zip(*md5_store)
            ])
    ).hexdigest()

def checkIfCachedResultsExist():
    return os.path.exists('/tmp/{}/results'.format(getUniqueCacheId()))

def loadTextArrayFromCache():
    cache_id = getUniqueCacheId()
    if os.path.exists('/tmp/{}/results/text.cache'.format(cache_id)):
        file = open('/tmp/{}/results/text.cache'.format(cache_id), 'r')
        content = file.read()
        file.close()
        return ast.literal_eval(content.strip())
    else:
        raise ValueError("cvfy [Error Code: 019] => text.cache does not exist")

def saveTextArrayToCache(text_array):
    cache_id = getUniqueCacheId()
    subprocess.Popen('mkdir -p {}'.format('/tmp/{}/results/'.format(cache_id)), shell=True).wait()
    with open('/tmp/{}/results/text.cache'.format(cache_id), 'w') as file:
        text_array = ['"{}"'.format(x) for x in text_array]
        file.write('[' + ', '.join(text_array) + ']')

def loadImageArrayFromCache():
    cache_id = getUniqueCacheId()
    if os.path.exists('/tmp/{}/results/images/'.format(cache_id)):
        return glob.glob('/tmp/{}/results/images/*.*'.format(cache_id))
    else:
        raise ValueError("cvfy [Error Code: 020] => cached image results do not exist")

def saveImageArrayToCache(data, mode):
    cache_id = getUniqueCacheId()
    subprocess.Popen('mkdir -p {}'.format('/tmp/{}/results/images'.format(cache_id)), shell=True).wait()
    if (isinstance(data, list) or isinstance(data, tuple)):
        pass
    else:
        raise ValueError("cvfy [Error Code: 021] => saveImageArrayToCache can only accept an array or a tuple")
    tempdata = []
    if (mode == 'file_path'):
        try:
            for index, file_path in enumerate(data):
                file_extension = file_path.split('/')[-1].split('.')[-1]
                shutil.copy2(file_path, '/tmp/{}/results/images/{}.{}'.format(cache_id, index, file_extension))
        except Exception as e:
            raise Exception("cvfy [Error Code: 021] => unable to cache image file - reason: {}".format(e))
    elif (mode == 'numpy_array'):
        image_base_path = '/tmp/{}/results/images/'.format(cache_id)
        try:
            for index, numpy_image_array in enumerate(data):
                path = image_base_path + str(index) + '.png'
                cv2.imwrite(path, numpy_image_array)
        except Exception as e:
            raise Exception("cvfy [Error Code: 022] => unable to write numpy array as image to cache - reason: {}".format(e))
    else:
        raise ValueError("cvfy [Error Code: 023] => invalid type value")


#####################
## input functions ##
#####################

def getTextArray():
    validateTOKEN(sys._getframe().f_code.co_name)
    textdata = []
    i = 0
    try:
        while True:
            textdata.append(request.form['input-text-{}'.format(i)])
            i += 1
    except Exception as e:
        pass
    return (textdata)

def getImageArray(mode='file_path'):
    validateTOKEN(sys._getframe().f_code.co_name)
    imagedata = []
    i = 0
    try:
        while True:
            imagedata.append(request.files['input-image-{}'.format(i)])
            i += 1
    except Exception as e:
        pass
    if mode == 'file_path':
        return (transformToLocalPath(imagedata))
    elif mode == 'numpy_array':
        return (transformToNumpyArrays(imagedata))

######################
## output functions ##
######################

def sendTextArray(data):
    validateTOKEN(sys._getframe().f_code.co_name)
    validate_socket_id(request)
    if (isinstance(data, list) or isinstance(data, tuple)):
        pass
    else:
        raise ValueError("cvfy [Error Code: 005] => sendTextArray can only accept an array or a tuple")
    for element in data:
        if (not isinstance(element, basestring if (sys.version_info[0] == 2) else str)):
            raise ValueError("cvfy [Error Code: 006] => iterable is not composed of strings")
    data = {
        'socketId': request.form['socket-id'],
        'data': data
    }
    data = json.dumps(data)
    try:
        headers = {'Content-Type': 'application/json'}
        if (CVFY_TARGET == 'local'):
            url = 'http://' + TOKEN.split(':')[1] + ':' + TOKEN.split(':')[3] + CVFY_INJECTION_SUBPATH
        elif (CVFY_TARGET == 'remote'):
            url = 'http://' + TOKEN.split(':')[5] + ':' + TOKEN.split(':')[3] + CVFY_INJECTION_SUBPATH
        r = requests.post(url, headers=headers, data=data)
        if (r.status_code == 400):
            raise Exception("cvfy [Error Code: 007] => 400: Bad Request - app server says malformed request")
        elif (r.status_code == 500):
            raise Exception("cvfy [Error Code: 008] => 500: Internal Server Error - app server cannot handle your request")
        elif (r.status_code == 404):
            raise Exception("cvfy [Error Code: 009] => 404: Not Found - app server cannot be found; {0} is unreachable".format(url))
        elif (r.status_code == 200):
            return (r.text)
    except Exception as e:
        if (e.__class__.__name__ == 'ConnectionError'):
            raise Exception("cvfy [Error Code: 010] => Connection Error")

def sendGraphArray(data):
    validateTOKEN(sys._getframe().f_code.co_name)
    validate_socket_id(request)
    if (isinstance(data, list) or isinstance(data, tuple)):
        pass
    else:
        raise ValueError("cvfy [Error Code: 0017] => sendBarGraphArray can only accept an array or a tuple")
    for element in data:
        if (not isinstance(element, list)):
            raise ValueError("cvfy [Error Code: 0018] => iterable is not composed of arrays")
    data = {
        'socketId': request.form['socket-id'],
        'data': data
    }
    data = json.dumps(data)
    try:
        headers = {'Content-Type': 'application/json'}
        if (CVFY_TARGET == 'local'):
            url = 'http://' + TOKEN.split(':')[1] + ':' + TOKEN.split(':')[3] + CVFY_INJECTION_SUBPATH
        elif (CVFY_TARGET == 'remote'):
            url = 'http://' + TOKEN.split(':')[5] + ':' + TOKEN.split(':')[3] + CVFY_INJECTION_SUBPATH
        r = requests.post(url, headers=headers, data=data)
        if (r.status_code == 400):
            raise Exception("cvfy [Error Code: 007] => 400: Bad Request - app server says malformed request")
        elif (r.status_code == 500):
            raise Exception("cvfy [Error Code: 008] => 500: Internal Server Error - app server cannot handle your request")
        elif (r.status_code == 404):
            raise Exception("cvfy [Error Code: 009] => 404: Not Found - app server cannot be found; {0} is unreachable".format(url))
        elif (r.status_code == 200):
            return (r.text)
    except Exception as e:
        if (e.__class__.__name__ == 'ConnectionError'):
            raise Exception("cvfy [Error Code: 010] => Connection Error")

def sendTextArrayToTerminal(data):
    validateTOKEN(sys._getframe().f_code.co_name)
    validate_socket_id(request)
    if (isinstance(data, list) or isinstance(data, tuple)):
        pass
    else:
        raise ValueError("cvfy [Error Code: 017] => sendTextArrayToTerminal can only accept an array or a tuple")
    for element in data:
        if (not isinstance(element, basestring if (sys.version_info[0] == 2) else str)):
            raise ValueError("cvfy [Error Code: 006] => iterable is not composed of strings")
    data = {
        'socketId': request.form['socket-id'],
        'terminalData': data
    }
    data = json.dumps(data)
    try:
        headers = {'Content-Type': 'application/json'}
        if (CVFY_TARGET == 'local'):
            url = 'http://' + TOKEN.split(':')[1] + ':' + TOKEN.split(':')[3] + CVFY_INJECTION_SUBPATH
        elif (CVFY_TARGET == 'remote'):
            url = 'http://' + TOKEN.split(':')[5] + ':' + TOKEN.split(':')[3] + CVFY_INJECTION_SUBPATH
        r = requests.post(url, headers=headers, data=data)
        if (r.status_code == 400):
            raise Exception("cvfy [Error Code: 007] => 400: Bad Request - app server says malformed request")
        elif (r.status_code == 500):
            raise Exception("cvfy [Error Code: 008] => 500: Internal Server Error - app server cannot handle your request")
        elif (r.status_code == 404):
            raise Exception("cvfy [Error Code: 009] => 404: Not Found - app server cannot be found; {0} is unreachable".format(url))
        elif (r.status_code == 200):
            return (r.text)
    except Exception as e:
        if (e.__class__.__name__ == 'ConnectionError'):
            raise Exception("cvfy [Error Code: 010] => Connection Error")


def sendImageArray(data, mode):
    validateTOKEN(sys._getframe().f_code.co_name)
    validate_socket_id(request)
    if (isinstance(data, list) or isinstance(data, tuple)):
        pass
    else:
        raise ValueError("cvfy [Error Code: 013] => sendImageArray can only accept an array or a tuple")
    tempdata = []
    if (mode == 'file_path'):
        try:
            for file_path in data:
                with open(file_path, 'rb') as file:
                    src = ''
                    content_type = mime.from_file(file_path)
                    if content_type == 'image/jpeg' or content_type == 'image/jpg':
                        src += 'data:image/jpeg;base64,'
                    elif content_type == 'image/png':
                        src += 'data:image/png;base64,'
                    src += base64.b64encode(file.read())
                    tempdata.append(src)
        except Exception as e:
            raise Exception("cvfy [Error Code: 015] => unable to read image file - reason: {}".format(e))
    elif (mode == 'numpy_array'):
        image_base_path = '/tmp/' + str(random.randint(1, 1000000)) + '/'
        subprocess.Popen('mkdir -p {}'.format(image_base_path), shell=True).wait()
        try:
            for index, numpy_image_array in enumerate(data):
                path = image_base_path + str(index) + '.png'
                cv2.imwrite(path, numpy_image_array)
                with open(path, 'rb') as file:
                    src = ''
                    content_type = mime.from_file(path)
                    if content_type == 'image/jpeg' or content_type == 'image/jpg':
                        src += 'data:image/jpeg;base64,'
                    elif content_type == 'image/png':
                        src += 'data:image/png;base64,'
                    src += base64.b64encode(file.read())
                    tempdata.append(src)
            subprocess.Popen('rm -rf {}'.format(image_base_path), shell=True).wait()
        except Exception as e:
            raise Exception("cvfy [Error Code: 016] => unable to write numpy array as image")
    else:
        raise ValueError("cvfy [Error Code: 014] => invalid type value")
    data = {
        'socketId': request.form['socket-id'],
        'data': tempdata
    }
    data = json.dumps(data, ensure_ascii=False)
    try:
        headers = {'Content-Type': 'application/json'}
        if (CVFY_TARGET == 'local'):
            url = 'http://' + TOKEN.split(':')[1] + ':' + TOKEN.split(':')[3] + CVFY_INJECTION_SUBPATH
        elif (CVFY_TARGET == 'remote'):
            url = 'http://' + TOKEN.split(':')[5] + ':' + TOKEN.split(':')[3] + CVFY_INJECTION_SUBPATH
        r = requests.post(url, headers=headers, data=data)
        if (r.status_code == 400):
            raise Exception("cvfy [Error Code: 007] => 400: Bad Request - app server says malformed request")
        elif (r.status_code == 500):
            raise Exception("cvfy [Error Code: 008] => 500: Internal Server Error - app server cannot handle your request")
        elif (r.status_code == 404):
            raise Exception("cvfy [Error Code: 009] => 404: Not Found - app server cannot be found; {0} is unreachable".format(url))
        elif (r.status_code == 200):
            return (r.text)
    except Exception as e:
        if (e.__class__.__name__ == 'ConnectionError'):
            raise Exception("cvfy [Error Code: 010] => Connection Error")
