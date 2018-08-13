# First Demo

Since now you know what origami is and how it works its time to convert an actual machine learning model to origami wrapped
model demo. For the sake of this document we will focus on Visual Dialog demo. https://github.com/batra-mlp-lab/visdial-rl

* You can find the actual source of origami wrapped visual dialog demo [here](https://github.com/fristonio/visdial-rl/tree/origami-wrapper).
* The actual demo code for the visual dialog demo is located [here](https://github.com/fristonio/visdial-rl/blob/origami-wrapper/temp_main.py)

The main part of the demo in which we are interested is when demos takes in the user input. The demo we have is a command line interface demo
so the input to the demo comes from standard input.

```python
def main():
    DIALOG = []
    visdial_model = VisualDialog()

    while (True):
        CAPTION = "a cat sitting on top of a refrigerator"
        QUESTION = input("Enter the question: ")
        IMG_PATH = "demo/img.jpg"
        if QUESTION == "EXIT":
            break
        dialog = visdial_model.predict(QUESTION, IMG_PATH, CAPTION, DIALOG)
        DIALOG = dialog
        print(dialog)

```

This method first initializes the Visual Dialog demo using `VisualDialog` class, then it infinitely waits for user input from the command line.
For the sake of this demo we have hardcoded the image and the caption, so we only require question from the user. Then corresponding to each question the
code predicts the answer using the model we initialized earlier. The response from the prediction is then printed to stdout.

Let's go ahead and wrap this with origami-lib step by step.

* First we need to import the lib and initialize the application.

```python
from origami_lib.origami import Origami

app = Origami("VisualDialogue", cache_path="cache_visdial")
visdial_model = VisualDialog()
```

* Implement a method with `@app.listen` decorator which will be called each time a request is made to access the demo.

```python
@app.listen()
def visdial():
    # caption = app.get_text_array()[0]
    # image = app.get_image_array()[0]

    CAPTION = "a cat sitting on top of a refrigerator"
    IMG_PATH = "demo/img.jpg"
	dialog = []
```

Again for the sake of this example we have hardcoded the image and caption. We can have used input from the user the uncommenting the commented lines.

* Now for each connection we get on our demo we need to get answer from the same combination of caption and image. So we register a function to be called
each time when a question is asked for the image. This way we can write some preprocessing code for the image in `visdial` function without having to perform
the preprocessing for every question.

```python
def predict(image_path, caption, dialog, message=""):
    new_dial = visdial_model.predict(message, image_path, caption, dialog)
    dialog.append(new_dial[-1])
    print("Current dialog object is : \n", dialog)
    return dialog[-1]["answer"]


@app.listen()
def visdial():
    # caption = app.get_text_array()[0]
    # image = app.get_image_array()[0]

    CAPTION = "a cat sitting on top of a refrigerator"
    IMG_PATH = "demo/img.jpg"
    dialog = []

    # Register predict function
    app.register_persistent_connection(predict, [IMG_PATH, CAPTION, dialog])
```

In the above code predict function is called each time a question is asked, where the question corresponds to message argument.
The variable dialog contains the entire history of the conversation. So we can also return that to user, but for this example we are only
returning the current question prediction.

After defining all the functions and classes we run the app by simply calling `run` on app. And thats it, our demo is ready to be used with
Origami frontend. So with a minimal set of changes to the actual demo code we have our demo ready. 
