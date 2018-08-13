from collections import deque
from flask import Flask, request as user_req, jsonify
from flask_cors import CORS, cross_origin
import requests
import re
import json
import time
from tornado.wsgi import WSGIContainer
from tornado.web import Application, FallbackHandler, RequestHandler
from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler
import uuid

from . import constants, exceptions, utils
from .pipeline import OrigamiCache


class OrigamiRequester(object):
    def __init__(self):
        pass

    def request_origami_server(self, payload):
        """
        Makes a POST request to the origami server to send the payload, this
        can be used to send data to user via socket. First origami-lib makes
        request to Origami server providing the socket Id of the user which in
        turn inject the data to user browser provided in the data field of the
        payload.

        Args:
            payload: Python dict which is to be sent to the origami server \
                The format of the payload is:

                .. code-block

                    {
                        "socketId": userSocketID,
                        "[dataType]": data
                    }


                where dataType can be one of the following. \
                data, terminalData

        Returns:
            response_text:
                Response text returned from the request made.

        Raises:
            BadRequestException:
                400 when requesting
            NotFoundRequestException:
                404 when requesting
            InternalServerErrorException:
                500 when requesting
            OrigamiRequesterException:
                Some other error code when requesting
        """
        try:
            target_url = self._get_origami_server_target_url()
        except Exception as e:
            raise exceptions.RequesterNoTargetUrlException(
                "No target url retriver function _get_origami_server_target_url\
                found : {}".format(e))

        # Request the origami server
        try:
            payload = json.dumps(payload)
            resp = requests.post(
                target_url,
                headers=constants.REQUESTS_JSON_HEADERS,
                data=payload)
        except Exception as e:
            raise exceptions.OrigamiRequesterException(
                "Connection error when requesting origami server : {}".format(
                    e))

        # Check the response object
        if resp.status_code == 400:
            raise exceptions.BadRequestException(
                "Bad Request: 400 when sending data to origami server")
        elif resp.status_code == 404:
            raise exceptions.NotFoundRequestException(
                "Not Found: 404 when sending data to origami server")
        elif resp.status_code == 500:
            raise exceptions.InternalServerErrorException(
                "Internal Server Error: 500 when requesting origami server")
        elif resp.status_code == 200:
            return resp.text
        else:
            raise exceptions.OrigamiRequesterException(
                "Connection error when requesting origami server")


class OrigamiInputs(object):
    """ Origami input functions
    Class implementing input functions for Origami, this class will be
    inherited by main Origami class.
    """

    def __init__(self):
        pass

    def get_text_array(self):
        """
        Extract text input from the request form.

        Returns:
            text_inputs: Input text array provided by user in the request.

        Raises:
            InvalidRequestParameterGet: Not a valid parameter requested from \
                the users request to origami.
        """
        text_inputs = []
        i = 0
        # TODO: Convert this to getlist to directly get the list of inputs
        while True:
            input_text = user_req.form.get('input-text-{}'.format(i), type=str)
            if input_text:
                text_inputs.append(input_text)
            else:
                break
            i += 1

        if text_inputs:
            return text_inputs
        else:
            raise exceptions.InvalidRequestParameterGet(
                "No valid input text fields in the request")

    def get_image_array(self, mode=constants.INPUT_IMAGE_ARRAY_FILEPATH_MODE):
        """
        Extract image input from the request files.
        The two modes defines how the user wants the images

        file_path: The file_path mode which is the default one makes use of \
            OrigamiCache. It creates a cache object and then store the images \
            into the cache and returns this object.

            User can then use this cache object to load images from the cache.
            The load function will return a list of file_paths which will each
            corresponding to the image.

        Args:
            mode: mode in which you are expecting the result

                * file_path -> cache Image locally and return path
                * numpy_array -> processes the image and returns the numpy \
                    array corresponding to that.

        Returns:
            ImageArr: array of Images either in the numpy array format or \
                the path of the image which is cached locally.

        Raises:
            InputHandlerException: Exception that the input provided by user \
                in the request is not Valid, which is some image is expected \
                and none provided.
        """
        image_inputs = []
        i = 0
        try:
            while True:
                image_inputs.append(user_req.files['input-image-{}'.format(i)])
                i += 1
        except Exception as e:
            if not image_inputs:
                raise exceptions.InvalidRequestParameterGet(
                    "No valid input image fields in the request : {}".format(e))

        if mode == constants.INPUT_IMAGE_ARRAY_FILEPATH_MODE:
            cache = OrigamiCache()
            cache.save_image_file_array_to_cache(image_inputs)
            image_path_arr = cache.load_image_file_paths_from_cache()
            return image_path_arr

        elif mode == constants.INPUT_IMAGE_ARRAY_NPARRAY_MODE:
            return utils.get_image_as_numpy_arr(image_inputs)
        else:
            raise exceptions.InputHandlerException(
                "No valid mode provided when requesting user image input")


class OrigamiOutputs(OrigamiRequester):
    """ Origami output functionalities
    This class implements all the output functions for Origami.

    Attributes:
        response: response variable storing response to be sent to client \
            if API access is enabled using the provided decorator.
    """
    response = list(constants.DEFAULT_ORIGAMI_RESPONSE_TEMPLATE)

    def __init__(self):
        pass

    def _clear_response(self):
        """
        Clears the response variable to have the default template
        response string

        Returns:
            response: string which was in self.response before clearing \
                it up.
        """
        response = jsonify(self.response)
        # Make a copy of the constant origami response template in self.response
        self.response = list(constants.DEFAULT_ORIGAMI_RESPONSE_TEMPLATE)
        return response

    def _send_api_response(self, payload):
        """
        Set the response for user request as a json object of payload

        Args:
            payload: payload(python dict) to be sent to the user

        Returns:
            Jsonified json response object.
        """
        self.response.append(payload)
        return self.response

    def origami_api(self, view_func):
        """
        Decorator to decorate the user defined main function to
        send user an API response at the end of the request.

        Args:
            view_func: Function that this function wraps to make \
                things work.

        Returns:
            func: Wrapper fuction that calls the view_func to do its work \
                and then returns the response back to user.
        """

        def _wrapper():
            view_func()
            response = self._clear_response()
            return response

        return _wrapper

    def _origmai_send_data(self, data, dataType, socketId=None):
        """
        Core function which sends output to either the origami server or the
        user as response to request

        Args:
            data: list or tuple of string to be sent.
            dataType: Key for data in payload python dict \
                can be either of `data` or `terminalData`

        Returns:
            resp: Response we sent to user as API response or response from
                the origami server.
        """
        resp = None
        socketId = socketId if socketId else user_req.form.get(
            constants.REQUEST_SOCKET_ID_KEY, type=str)
        # Check if a valid socketId is provided in the request
        # else consider it as an API request.

        if socketId:
            # Check if the socket-id is there is the request form.
            payload = {"socketId": socketId, dataType: data}
            resp = self.request_origami_server(payload)

        else:
            # TODO: Discuss the strucutre of API response payload.
            payload = {"data": data}
            resp = self._send_api_response(payload)

        return resp

    # Data sending functions

    def send_text_array(self, data, dataType=constants.DEFAULT_DATA_TYPE_KEY):
        """
        Send text data array to origami_server with the users socket ID

        Args:
            data: list or tuple of string to be sent.
            dataType: Key for data in payload python dict \
                can be either of data or terminalData

        Returns:
            resp: Response text we got back from the origami server \
                corresponding to the request we made.

        Raises:
            MismatchTypeException: Type of the data provided to function is \
                not what we expected.
        """

        # TODO: make dataType more explicit here use different types for images
        # and graphs too so they can be handled properly via origami.
        utils.strict_check_array_of_string(data)

        resp = self._origmai_send_data(data, dataType)
        return resp

    def send_graph_array(self, data):
        """
        Send text data array to origami_server with the users socket ID

        Args:
            data (list, tuple): list or tuple of list/tuple to be sent.

        Returns:
            resp: Response text we got back from the origami server \
                corresponding to the request we made.

        Raises:
            MismatchTypeException: Type of the data provided to function is \
                not what we expected.
        """

        if not isinstance(data, (list, tuple)):
            raise exceptions.MismatchTypeException(
                "send_graph_array can only accept an array or a tuple.")

        if not all(isinstance(element, (list, tuple)) for element in data):
            raise exceptions.MismatchTypeException(
                "send_graph_array expects a list/tuple of list/tuple")

        resp = self._origmai_send_data(data, constants.DEFAULT_DATA_TYPE_KEY)
        return resp

    def send_text_array_to_terminal(self, data):
        """
        Send the array/tuple provided as argument to the origami server
        as a terminal data.

        Args:
            data (list, tuple): array/tuple of strings to be sent.

        Returns:
            resp: response got from sending the data.
        """
        resp = self.send_text_array(data, constants.TERMINAL_DATA_TYPE_KEY)
        return resp

    def send_image_array(self,
                         data,
                         mode=constants.INPUT_IMAGE_ARRAY_FILEPATH_MODE):
        """
        Send image array as base64 encoded images list.

        Args:
            data (list, tuple): list/tuple of either image path or numpy array
            mode (str): mode in which to process the data

        Returns:
            resp: response got from sending the data.

        Raises:
            MismatchTypeException: data is not of list/tuple type
        """
        if not isinstance(data, (list, tuple)):
            raise exceptions.MismatchTypeException(
                "send_image_array can only accept a list or a tuple.")

        image_arr = []

        # Mode -> file_path
        if mode == constants.INPUT_IMAGE_ARRAY_FILEPATH_MODE:
            for file_path in data:
                img_src = utils.get_base64_image_from_file(file_path)
                image_arr.append(img_src)

        # Mode -> NP Array
        elif mode == constants.INPUT_IMAGE_ARRAY_NPARRAY_MODE:
            for np_image_arr in data:
                img_src = utils.get_base64_image_from_nparr(np_image_arr)
                image_arr.append(img_src)

        else:
            raise exceptions.OutputHandlerException(
                "Not a valid mode({0}) provided when encoding image \
                for sending", mode)

        resp = self._origmai_send_data(image_arr,
                                       constants.DEFAULT_DATA_TYPE_KEY)
        return resp


class OrigamiWebSocketHandler(WebSocketHandler):
    """
    Handles persistent websocket connections for Origami

    Attributes:
        persistent_conn_map:
            This is a list of object containing information about each \
            registered persistent connection. The structure of the object is:

            .. code-block

                {
                    "id": socketId,
                    "func": func,
                    "arguments": args,
                    "timestamp": time.time()
                }

            * `ID`: SocketID for registering user
            * `func`: routine to execute when the request from websocket is made
            * `arguments`: a list of arguments to be provided to func.
            * `timestamp`: Timestamp when the function with is registered in \
                the map. This will be used in the case when we deploy regular
                cleaning of the connection maps.

            Each time a user connection is registered an entry is made in this
            mapping list. An entry from the map is deleted when the client
            closes the websocket for the connection.
    """
    # A persistent connection mapping.
    # Static variable, a single copy for all the connection.
    # TODO: Run a worker to regularly clean this global mapping, might get too
    # bloated
    persistent_conn_map = []

    def register_persistent_connection(self, func, args):
        """
        Entrypoint to register a persistent connection by user.
        First check whether the func is callable and args should be a list
        then add the func with args and socketID to the global map.

        For each request that comes to demo, the `socket-id` of the client needs
        to be registered this will done using this function, it register a
        function for a persistent connection with the argument provided. Apart
        from the arguments in this function `func` will also require to have an
        additional parameter ``message`` which will contain the input from the
        websocket as a string.

        For example

        .. code-block:: python

            def my_func(arg1, arg2, message=""):
                print("Message from websocket is : ", message)
                print("Arguments are :: ", arg1, arg2)

            @app.listen()
            @app.origami_api
            def hello():
                arr = ['Hello', 'World!']
                text_arr = app.send_text_array()

                # Register a function here
                # You can think this of like a python decorator wherein you are
                # essentially
                # enclosing a function inside other. So hello() is the function
                # which will
                # setup the environment for my_func which will be executed
                # within the
                # environment each time user makes a request using websockets.
                # Args is the list of arguments you want to send for the
                #  function in the same
                # order, they are what passed as the state of this connectino t
                # the function.

                app.register_persistent_connection(my_func,
                    ["my argument", "secondArg"])

        Now for the above example whenever a request a received a persistent
        connection will be registered between client and demo. Once the user
        sends some data from the websocket, the function registered will be
        called with the corresponding message.


        Args:
            func (callable): function to execute for the message recieved from \
                the websocket.
            args (list): list of arguments.

        Returns:
            bool: True if the persistent connection is registered. \
                False if the connection is not registered.
        """
        if not isinstance(args, list):
            raise exceptions.MismatchTypeException(
                "register_persistent_connection only accepts \
                arguments as a list")
        # Only works for python2 and python3.2+, check if the function is
        # callable
        if not callable(func):
            raise exceptions.MismatchTypeException(
                "Non callable argument for function")

        socketId = user_req.form.get(constants.REQUEST_SOCKET_ID_KEY, type=str)

        if socketId:
            try:
                # Try to check if a connection with the give socket-id already
                # exist
                dup_conn = next(
                    x for x in self.persistent_conn_map if x["id"] == socketId)
                self.__clear_connection(dup_conn)
            except StopIteration:
                # No connection with the socket ID found.
                self.persistent_conn_map.append({
                    "id": socketId,
                    "func": func,
                    "arguments": args,
                    "timestamp": time.time()
                })
            return True
        else:
            # This is the case when the user is requesting without socket-id
            self._clear_response()
            payload = {"ERROR": "Not available over API"}
            self._send_api_response(payload)
            return False

    def check_origin(self, origin):
        """
        Overridden function from WebSocketHandler for CORS policy.
        This ensures that websocket connection can be made from any
        origin.
        """
        return True

    def __clear_connection(self, conn=None):
        """
        Clear the active connection from the persistent connection map.
        Remove the object self.active_connection from the list
        persistent_connections_map
        """
        conn = conn if conn else self.active_connection
        if conn:
            try:
                dup_conn = next(x for x in self.persistent_conn_map
                                if x["id"] == conn["id"])
                self.persistent_conn_map.remove(dup_conn)
            except StopIteration:
                pass

    def __reset_connection(self):
        """
        Reset global connection variables.
        """
        self.active_connection = None
        self.connection_id = ""

    def _validate_message(self, message):
        """
        Validate the provided message as argument for socket-id it came from.
        Writes the message to the socket on the basis of message validation.

        Args:
            message: message from the websocket to be validated. \
                The format of a valid message is

                .. code-block

                    {
                        "socket-id": "[SocketID]" -> If first time connection \
                            opened
                        "data": "[Data sent from client as a string]"
                    }

        Returns:
            data from the message or None
        """
        try:
            message = json.loads(message)
            if constants.REQUEST_SOCKET_ID_KEY in message:
                socketId = message[constants.REQUEST_SOCKET_ID_KEY]
                if not self.active_connection:
                    self.active_connection = next(
                        x for x in self.persistent_conn_map
                        if x["id"] == socketId)
                    self.connection_id = self.active_connection["id"]

                elif self.active_connection and self.connection_id != socketId:
                    self.write_error("Not a valid socket-id provided")
                    self.close()
                    return None

            elif not self.active_connection:
                self.write_message(
                    "No active connection found, register socket-id")
                self.close()
                return None

            if "data" in message and utils.check_if_string(message["data"]):
                return message["data"]

        except StopIteration:
            self.write_message("Could not find socket-id match")
        except Exception:
            self.write_message("Input provided is malformed")

        return None

    def open(self):
        """
        A new websocket connection is opened.
        Overridden function from WebSocketHandler

        This method resets the global connection variables.
        """
        self.__reset_connection()

    def on_message(self, message):
        """
        Got a messege from the websocket connection.
        Overridden method from WebSocketHandler.

        This method recieves the message from the websocket connection and
        validates the message. If the message is validated it extracts the
        data from the message and pass it as an argument to the function
        registered corresponding to the users socket-id. The returned value
        from the function is sent back to user as a response.

        Args:
            message: message from the websocket connection. \
                This message is what we got from the websocket, first we need \
                to validate it and then extract the required matter from it \
                which will then be used by the registered function.
        """
        data = self._validate_message(message)
        if data:
            out_msg = self.active_connection["func"](
                *self.active_connection["arguments"], message=data)
            try:
                # Send the out_msg returned from the function.
                if isinstance(out_msg, dict):
                    json_resp = json.dumps(out_msg)
                    self.write_message(json_resp)
                elif utils.check_if_string(out_msg):
                    self.write_message(out_msg)
                    # self._origmai_send_data(
                    #     "ws_data", out_msg, socketId=self.connection_id)
                else:
                    print(
                        "A persistent connection can only return a python dict \
                        or string")
            except Exception:
                pass

    def on_close(self):
        """
        WebSocket connection is closed, clear the active connection that we were
        using and reset the connection variables.
        """
        self.__clear_connection()
        self.__reset_connection()


class FunctionServiceHandler(RequestHandler):
    """
    Handles persistent calls to function.

    The const MAX_CONN_LIMIT here defines the maximum no of
    simultaneous http connection we support, the default is 32

    We are not using python list here since pop operations for them is
    slow as compared to deque. It also acts as a similar iterable to list
    so most of the methods we use with list are available for this too.

    Attributes:
        MAX_CONN_LIMIT: maximum connections that we can hold.

        functional_service_map: A list of connections maapings with functions \
            and identifiers.
    """
    MAX_CONN_LIMIT = 32
    functional_service_map = deque(maxlen=MAX_CONN_LIMIT)

    @classmethod
    def register_persistent_http_connection(cls, func, args):
        """
        Similar to register_persistent_connection method for a websocket
        handler, with the only difference that it registers http connection
        which can then be used to respond to user requests on a particular
        resource /fass in this case.

        How this function work is, each time a user request the root resource
        a function will be registered for the user with the provided args.
        Now whenever user wants to access the registered function he only needs
        to make an HTTP request to /fass resource with the identifier
        returned by this function.

        So suppose I have a function in which I take an image from the user
        and preprocess it, then first the user request the root resource with
        the image. After preprocessing a call to this function is made with the
        preprocessed data as an argument. This method in turn registers the
        function provided for future user interaction.

        Now user makes a request to /fass resource with the ID returned from
        the method. The request is matched with the function registered with
        the corresponding ID and called with the preprocessed image as the
        argument we provided earlier. This registered function then returns
        a response to the user.

        .. code-block:: python

            from origami_lib.origami import Origami

            # VQA model
            app = Origami("vqa")

            class VQA:
                def __init__(self):
                    pass

            def preprocess_image(img):
                pass

            def my_func(preprocessed_image, query):
                print("Query is : {}".format(query))
                ans = VQA(preprocessed_image, query)
                return "Ans for query {} is {}".format(query, ans)


            @app.listen()
            @app.origami_api
            def vqa_handler():
                img_arr = app.get_image_array()
                preprocessed_image = preprocess_image(img_arr[0])
                func_id = app.register_persistent_http_connection(
                    question_handler,
                    [preprocessed_image])
                app.send_text_array([func_id])

            app.run()


        Args:
            func (callable): A callable function which will be called when the \
                user requests the fass resource.
            args (list): A list of arguments to be passed to the handler

        Returns:
            func_id (str): Identifier corresponding to the registered \
                connection, every further request corresponding to this \
                registration should be provided with this id as a query \
                parameter.
        """
        if not isinstance(args, list):
            raise exceptions.MismatchTypeException(
                "register_persistent_connection only accepts \
                arguments as a list")
        # Only works for python2 and python3.2+, check if the function is
        # callable
        if not callable(func):
            raise exceptions.MismatchTypeException(
                "Non callable argument for function")

        func_id = uuid.uuid4().hex
        cls.functional_service_map.append({
            "id": func_id,
            "func": func,
            "arguments": args,
            "timestamp": time.time()
        })
        return func_id

    def get(self):
        query = self.get_query_argument("query", None, True)
        func_id = self.get_query_argument("id", None, True)
        if query and func_id:
            try:
                connection = next(x for x in self.functional_service_map
                                  if x["id"] == func_id)
                out_msg = connection["func"](
                    *connection["arguments"], query=query)
                try:
                    # Send the out_msg returned from the function.
                    if isinstance(out_msg, dict):
                        out_msg = json.dumps(out_msg)
                    elif not utils.check_if_string(out_msg):
                        print("Invaid return type, required either a dict or\
                            string")
                    self.write(out_msg)
                except Exception:
                    pass
            except StopIteration:
                self.set_status(500)
                self.finish("No valid identifier provided : {}".format(func_id))
                return

        else:
            self.set_status(500)
            self.finish("Need a query parameter along with an identifier")


class Origami(OrigamiInputs, OrigamiOutputs, OrigamiWebSocketHandler,
              FunctionServiceHandler):
    """ Origami class to declare the main app

    This class initializes the app and provides methods to interact with
    the web interface.

    This is the main interface for interacting with Origami, it provides all
    the necessery methods to be used by the user for demo deployment and user
    interaction.

    To create an Origami app

    .. code-block:: python

        from origami_lib.origami import Origami

        app = Origami("vqa")

        @app.listen("/event")
        @app.origami_api
        def hello():
            arr = ['Hello', 'World!']
            text_arr = app.send_text_array()
            return

        # App configuration have been established, spin the demo
        # This is a blocking call, so anything after this won't be executed.
        app.run()


    Attributes:
        name: Application name for the demo.
        origami_server_base: URL for origami server running.
        server: Flask server for origami
        cors: CORS for flask server running
    """

    def __init__(self,
                 name,
                 server_base=constants.ORIGAMI_SERVER_BASE_URL,
                 cache_path=constants.GLOBAL_CACHE_PATH):
        """
        Inits class with provided arguments
        """

        self.app_name = name
        self.origami_server_base = server_base
        # self.token = validate_token(token)
        # self.target = parse_target(token)

        self.server = Flask(__name__)
        self.cors = CORS(self.server)

    def _get_origami_server_target_url(self):
        """
        Returns orgiami server target url for flask server to use for injecting
        output.

        Returns:
            target_url: Origami server target url

        Raises:
            MismatchTypeException: Error occurred when correct type of token is
                not supplied.
        """
        try:
            assert isinstance(self.origami_server_base, str)
        except AssertionError:
            raise exceptions.MismatchTypeException(
                "Server base url type mismatch: string expected given %s"
                .format(type(self.origami_server_base)))

        target_protocol = constants.HTTPS_ENDPOINT
        if re.search(constants.LOCAL_TARGET_REGEXP, self.origami_server_base):
            target_protocol = constants.HTTP_ENDPOINT

        target_url = "{0}{1}{2}".format(target_protocol,
                                        self.origami_server_base,
                                        constants.ORIGAMI_SERVER_INJECTION_PATH)
        return target_url

    def listen(self, route=constants.ORIGAMI_DEFAULT_EVENT_ROUTE):
        """ Listen decorator wrapper for origami

        This function acts as a wrapper around the Flasks app.route() decorator
        By default we are restricting this to only POST methods.

        Args:
            route: route to be uesd by origami web interface for interaction. \
                By default the route is /event.
        """
        return self.server.route(
            route, methods=[
                "GET",
                "POST",
            ])

    def run(self):
        """
        Starts the flask server over Tornados WSGI Container interface
        Also provide websocket interface at /websocket for persistent
        connections

        To run this server just create an instance of Origami Class and call
        this function

        .. code-block:: python

            from origami_lib.origami import Origami

            app = Origami("My Model")
            app.run()


        Raises:
            OrigamiServerException: Exception when the port we are trying to \
                bind to is already in use.
        """
        try:
            port = constants.DEFAULT_PORT
            http_server = WSGIContainer(self.server)

            # Register a web application with websocket at /websocket
            server = Application([(r'/websocket', OrigamiWebSocketHandler),
                                  (r'/fass', FunctionServiceHandler),
                                  (r'.*', FallbackHandler,
                                   dict(fallback=http_server))])

            server.listen(port)
            print("Origami server running on port: {}".format(port))
            IOLoop.instance().start()
        except OSError:
            raise exceptions.OrigamiServerException(
                "ORIGAMI SERVER ERROR: Port {0} already in use.".format(port))

    def crossdomain(self, *args, **kwargs):
        """
        Implements cross-domain access for origami wrapped function.
        This is useful when the demo is deployed on some external server
        whose domain does not match with the origami.
        """
        return cross_origin
