import unittest
from pyramid import testing

class TestMyView(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_it(self):
        # At least, check if spinning this up doesn't throw an exception
        from patzilla.navigator.views import navigator_standalone
        request = testing.DummyRequest()
        info = navigator_standalone(request)
        self.assertIsInstance(info, dict)
