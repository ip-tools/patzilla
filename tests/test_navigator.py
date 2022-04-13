import unittest
from pyramid import testing


class TestNavigatorStandalone(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_with_dummy_request(self):
        # At least, check if spinning this up doesn't throw an exception.
        from patzilla.navigator.views import navigator_standalone
        request = testing.DummyRequest()
        info = navigator_standalone(request)
        self.assertIsInstance(info, dict)
