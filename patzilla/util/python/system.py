# -*- coding: utf-8 -*-
# (c) 2018 Andreas Motl <andreas.motl@ip-tools.org>
import logging
import subprocess
from six import BytesIO

logger = logging.getLogger(__name__)


def run_command(command, input=None):
    command_string = ' '.join(command)

    proc = subprocess.Popen(
        command,
        # shell = (os.name == 'nt'),
        # shell = True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    stdout = stderr = ''
    try:
        stdout, stderr = proc.communicate(input)
        if proc.returncode is not None and proc.returncode != 0:
            message = 'Command "{}" failed, returncode={}, stderr={}'.format(command_string, proc.returncode, stderr)
            logger.error(message)
            raise RuntimeError(message)

    except Exception as ex:
        if isinstance(ex, RuntimeError):
            raise
        else:
            message = 'Command "{}" failed, returncode={}, exception={}, stderr={}'.format(
                command_string, proc.returncode, ex, stderr)
            logger.error(message)
            raise RuntimeError(message)

    return BytesIO(stdout)

    """
    # Use Delegator.py for process execution

    # Currently, there seem to be problems using both binary STDIN and STDOUT:
    # https://github.com/kennethreitz/delegator.py/issues/51
    # Let's try again soon.

    #proc = delegator.run(command)
    #proc = delegator.run(command, block=True, binary=True)
    proc = delegator.run(command, block=False, binary=True)

    # https://github.com/kennethreitz/delegator.py/issues/50
    #proc.blocking = False
    proc.send(tiff.read())
    #proc.subprocess.send(tiff.read() + b"\n")
    proc.block()
    #print 'out:', proc.out
    print 'self.blocking:', proc.blocking
    print 'self._uses_subprocess:', proc._uses_subprocess
    print 'self.subprocess:', proc.subprocess

    print 'stdout-1:', proc.std_out
    stdout = proc.std_out.read()
    print 'stdout-2:', stdout
    #if 'ImageMagick' in stdout[:200]:
    #    raise ValueError('Image conversion failed, found "ImageMagick" in STDOUT')

    return BytesIO(stdout)
    """
