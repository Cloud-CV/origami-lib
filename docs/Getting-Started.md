# Getting Started

> Origami is an AI-as-a-service solution that allows researchers to easily convert their deep
learning models into an online service that is widely accessible to everyone without the need
to setup the infrastructure, resolve the dependencies, and build a web service around the deep
learning model.

Origami is a complete infrastructure including a web application which provides an interface
to interact with your demo and a library to build and bootstrap that application.

### Install origami-lib

To use your demo with origami first you will need to bootstrap your demo with origami-lib.
origami-lib(origami) is a python package which provides the necessery abstraction to interact
with the Origami user interface.

* Install origami lib using pip

`pip install origami`

### Bootstraping your demo

Next step is to bootstrap your demo with Origami. origami-lib has a few essential elements which
a demo uses to interact with the user interface. We will build a simple application from scratch using
origami-lib drawing a parallel between normal demo and origami bootstrapped demo.

First suppose you have a demo code which consists of just a function as below,
for the sake of this example consider the model takes user input and returns a 
string based on the length of input.

```python
def example_demo(user_input):
	length = len(user_input)
	index = length % 5
	string_arr = ["Hello!", "World", "think", "build", "ship"]
	return string_arr[index]

while True:
	user_input = input("Enter something magical : ")
	output = example_demo(user_input)
	print(output)
```

Now if you were to show this demo to someone the person should first set up your demo and then use it.
Origami helps you increase the reach of your demo by abstracting away all the setup and providing
a nice UI to interact with the demo.

So let's start bootstrapping this with origami.

Before doing anything with your demo you need to first instantiate Origami application.

```python
from origami import Origami

app = Origami("my_demo")
```

If you have even a little experince with python you might have come across _decorators_. You
can think of decorators as a black box which takes your function do something magical and then
return you a different function with some additional features. Origami provides nice decorators
which you can easily use with your functions.

One such decorator is `Origami.listen()` which runs your function each time a user interact with
your demo on the Origami User Interface. You can think of its function similar to taking user input
from command line and then calling `example_demo` function in our example.

Only catch here is you don't get the user input as an argument to the function but you have to manually
ask for it inside the function. This is done using Origami Input functions which includes

* _get_text_array_ -> User text inputs as python list
* _get_image_array_ -> User image inputs as python list

So user can give multiple inputs with different type too, like two question and an Image for VQA like demo.

But in our case we only need text input so we will use `get_text_array()`.

```python
@app.listen()
def example_demo():
	user_input = app.get_text_array()[0]
```

After all code for the demo is writtern we run the app using `Origami.run()`. So let's see how our code looks
with origami.

```python
from origami import Origami

app = Origami("my_demo")

@app.listen()
def example_demo():
	user_input = app.get_text_array()[0]
	length = len(user_input)
	index = length % 5
	string_arr = ["Hello!", "World", "think", "build", "ship"]
	return string_arr[index]

app.run()
```

Preety cool right!

To know about more things you can do with origami-lib go to [Next Steps](/docs/Next-Steps.md). 
