import sys
from os import path
# import parent directory into path so that origami can be imported
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import origami
import numpy as np
import cv2      # for reading image files
from flask import jsonify

# running at 127.0.0.1
# port 8888
app = origami.register('gh:127.0.0.1:1:1:8888:0.0.0.0')

# list of images to be received
image_list = [
    'example1.png',
    'example2.png'
]

# list of text to be received
text_list = [
    'hello',
    'world',
    'Is this a sample question?'
]

@origami.crossdomain
@app.listen()
def test():
    # test number: 
    # 0 for text array, 
    # 1 for image array using filepath, 
    # 2 for image array using np array, 
    # 3 for all
    tnum = origami.request.form['test_number']

    if tnum == '0':
        print('hello')
        # test getTextArray
        all_text = origami.getTextArray()
        print('Received %d text strings'%(len(all_text)))
        print(all_text)
        return jsonify({'data': all_text}), 200        
    
    elif tnum == '1':
        # test getImageArray with file_path mode
        all_image_paths = origami.getImageArray(mode='file_path')
        print('Received %d image paths'%(len(all_image_paths)))
        print(all_image_paths)
        return jsonify({'data': all_image_paths}), 200
    
    elif tnum == '2':
        # test getImageArray with numpy_array mode
        all_images = origami.getImageArray(mode='numpy_array')
        # np arrays have to be converted to python lists before converting to json
        return jsonify({'data': [a.tolist() for a in all_images]}), 200
    
    elif tnum == '3':
        all_text = origami.getTextArray()
        all_image_paths = origami.getImageArray(mode='file_path')
        all_images = origami.getImageArray(mode='numpy_array')
        return jsonify({'text': all_text, 
                        'filepaths': all_image_paths, 
                        'images': [a.tolist() for a in all_images]}), 200

    else:
        return 'Please define test number', 500

    return 'OK'

app.run()
