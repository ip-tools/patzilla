import sys

import patzilla.commands


def test_command_mkconfig(capsys):
    """
    Proof that `patzilla make-config ... --flavor=docker-compose` works as intended.

    It should yield a configuration which contains `mongodb` as host name
    for connecting to MongoDB. That fits the Docker Compose configuration
    provided within the repository.
    """

    sys.argv = ["patzilla", "make-config", "production", "--flavor=docker-compose"]
    patzilla.commands.run()

    result = capsys.readouterr()
    assert "mongodb.patzilla.uri = mongodb://mongodb:27017/patzilla" in result.out
