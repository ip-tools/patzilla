import re

import pytest

from patzilla.util.python import exception_traceback
from patzilla.util.python.decorators import memoize
from patzilla.util.python.system import run_command


def test_run_command_success_basic():
    assert run_command(["echo", "foo"]).read().strip() == b"foo"


def test_run_command_success_input():
    assert run_command(["cat"], input=b"foo").read().strip() == b"foo"


def test_run_command_failure_not_found():
    with pytest.raises(OSError) as ex:
        run_command(["unknown"])
    assert ex.match("No such file or directory")


def test_run_command_failure_program_error():
    with pytest.raises(RuntimeError) as ex:
        run_command(["false"])
    assert ex.match('Command "false" failed, returncode=1, stderr=')


def test_run_command_failure_input_error():
    with pytest.raises(RuntimeError) as ex:
        run_command(["true"], input={b"abc": b"def"})
    assert ex.match('Command "true" failed, returncode=None, exception=memoryview: a bytes-like object is required, not \'dict\', stderr=')


def test_memoize():
    @memoize
    def something():
        return "foo"
    result = something()
    assert result == "foo"
    assert something.cache == {'(){}': 'foo'}


def test_exception_traceback(capsys):
    try:
        foobar
    except NameError:
        output = exception_traceback()

    assert "Traceback (most recent call last)" in output
    assert "NameError: name \'foobar\' is not defined" in output
