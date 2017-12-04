import requests 
import json
import numpy as np
import cv2

# server running locally at port 8888
url = 'http://127.0.0.1:8888/event'

# text data to be sent
data = {
    'input-text-0': 'hello',
    'input-text-1': 'world',
    'input-text-2': 'Is this a sample question?',
    'input-text-4': 'This will not be read'
}
# list of images to be sent
image_list = [
    'example1.png',
    'example2.png'
]

# send text strings and check that they are received properly
def test_getTextInput():
    data_copy = data.copy()
    data_copy['test_number'] = 0
    r = requests.post(url=url, data=data_copy)
    text_array = json.loads(r.content)['data']
    assert(len(text_array) == 3)
    assert(text_array == ['hello', 'world', 'Is this a sample question?'])

# send wrong strings
def test_getWrongTextInput():
    data_copy = data.copy()
    data_copy['test_number'] = 0
    data_copy['input-text-0'] = 'goodbye'
    r = requests.post(url=url, data=data_copy)
    text_array = json.loads(r.content)['data']
    assert(text_array != ['hello', 'world', 'Is this a sample question?'])

# send more text strings than expected
def test_getExtraTextInput():
    data_copy = data.copy()
    data_copy['test_number'] = 0
    data_copy['input-text-3'] = 'goodbye'
    r = requests.post(url=url, data=data_copy)
    text_array = json.loads(r.content)['data']
    assert(text_array != ['hello', 'world', 'Is this a sample question?'])

# send images and get result as file_path
def test_getImageInput_filepath():
    # compile image data as byte strings
    files = {}
    for i in range(len(image_list)):
        with open(image_list[i], 'rb') as f:
            files['input-image-%d'%(i)] = f.read()
    r = requests.post(url=url, files=files, data={'test_number': 1})
    filepaths = json.loads(r.content)['data']
    assert(len(filepaths) == len(image_list))
    for i in range(len(filepaths)):
        assert(np.array_equal(cv2.imread(filepaths[i]), cv2.imread(image_list[i])))

# send images and get result as numpy array
def test_getImageInput_nparray():
    # compile image data as byte strings
    files = {}
    for i in range(len(image_list)):
        with open(image_list[i], 'rb') as f:
            files['input-image-%d'%(i)] = f.read()
    r = requests.post(url=url, files=files, data={'test_number': 2})
    # get image pixel data
    images = json.loads(r.content)['data']
    assert(len(images) == len(image_list))
    for i in range(len(images)):
        assert(np.array_equal(np.array(images[i], dtype=np.int16), cv2.imread(image_list[i])))

# send wrong images
def test_getWrongImageInput():
    # compile image data as byte strings
    files = {}
    for i in range(len(image_list)):
        # images in wrong order
        with open(image_list[len(image_list) - 1 - i], 'rb') as f:
            files['input-image-%d'%(i)] = f.read()
    r = requests.post(url=url, files=files, data={'test_number': 2})
    # get image pixel data
    images = json.loads(r.content)['data']
    assert(len(images) == len(image_list))
    for i in range(len(images)):
        assert(not np.array_equal(np.array(images[i], dtype=np.int16), cv2.imread(image_list[i])))

# send both the text data and image data at once
def test_all():
    data_copy = data.copy()
    data_copy['test_number'] = 3
    files = {}
    for i in range(len(image_list)):
        with open(image_list[i], 'rb') as f:
            files['input-image-%d'%(i)] = f.read()
    r = requests.post(url=url, files=files, data=data_copy)
    recv_data = json.loads(r.content)
    text_array = recv_data['text']
    image_paths = recv_data['filepaths']
    images = recv_data['images']
    assert(text_array == ['hello', 'world', 'Is this a sample question?'])
    assert(len(images) == len(image_list))
    for i in range(len(images)):
        assert(np.array_equal(np.array(images[i], dtype=np.int16), cv2.imread(image_list[i])))
    assert(len(image_paths) == len(image_list))
    for i in range(len(image_paths)):
        assert(np.array_equal(cv2.imread(image_paths[i]), cv2.imread(image_list[i])))
