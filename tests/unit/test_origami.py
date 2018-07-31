from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from origami_lib.origami import FunctionServiceHandler
from origami_lib.exceptions import MismatchTypeException


class FunctionServiceHandlerTest(AsyncHTTPTestCase):
    def get_app(self):
        app = Application([(r'/fass', FunctionServiceHandler)])
        return app

    def test_register_persistent_http_connection(self):
        def temp_func(arg, query=""):
            return arg + '::' + query

        x = FunctionServiceHandler
        self.assertRaises(MismatchTypeException,
                          x.register_persistent_http_connection, temp_func,
                          "pass a list")
        self.assertRaises(MismatchTypeException,
                          x.register_persistent_http_connection,
                          "pass a callable here", ["a"])

        f_id = x.register_persistent_http_connection(temp_func, ["argument"])
        entry = x.functional_service_map[-1]
        self.assertEqual(f_id, entry["id"])
        self.assertEqual(["argument"], entry["arguments"])

        res = self.fetch("/fass")
        self.assertEqual(res.code, 500)

        res = self.fetch("/fass?query=test&id=not_present")
        self.assertEqual(res.code, 500)
        self.assertIn(b"No valid identifier", res.body)

        res = self.fetch("/fass?query=test&id={}".format(f_id))
        self.assertEqual(res.code, 200)
        self.assertEqual(res.body, temp_func("argument", "test").encode())
