import subprocess
from unittest import TestCase

import pytest
from mock import mock
from mock.mock import PropertyMock
from testfixtures import Replacer
from testfixtures.popen import MockPopen

from patzilla.util.render.phantomjs import render_pdf


dotted_path = 'testfixtures.tests.test_popen_docs.Popen'


class TestPhantomJS(TestCase):
    """
    Test a `subprocess.check_call()` invocation to `phantomjs`.

    https://testfixtures.readthedocs.io/en/latest/popen.html
    """

    def setUp(self):
        self.Popen = MockPopen()
        self.r = Replacer()
        self.r.replace(dotted_path, self.Popen)
        self.addCleanup(self.r.restore)

    @mock.patch("patzilla.util.render.phantomjs.NamedTemporaryFile")
    def test_success(self, ntf_factory):

        # Define mock for `NamedTemporaryFile`.
        ntf = mock.MagicMock()
        type(ntf).name = PropertyMock(return_value="/tmp/foo.pdf")
        ntf.read.return_value = b"out"
        ntf_factory.return_value = ntf

        # Define mock for `subprocess.Popen`.
        self.Popen.set_default(returncode=0)

        # Test results.
        with mock.patch("subprocess.Popen", self.Popen):
            output = render_pdf("http://example.com/foo.pdf")
            assert output == b"out"

    @mock.patch("patzilla.util.render.phantomjs.NamedTemporaryFile")
    def test_failure(self, ntf_factory):

        # Define mock for `NamedTemporaryFile`.
        ntf = mock.MagicMock()
        type(ntf).name = PropertyMock(return_value="/tmp/foo.pdf")
        ntf.read.return_value = b"out"
        ntf_factory.return_value = ntf

        # Define mock for `subprocess.Popen`.
        self.Popen.set_default(returncode=1)

        # Test results.
        with mock.patch("subprocess.Popen", self.Popen):
            with pytest.raises(subprocess.CalledProcessError) as ex:
                render_pdf("http://example.com/foo.pdf")
            assert ex.match("Command .+phantomjs.+ returned non-zero exit status 1")
