from unittest import TestCase

from click.testing import CliRunner

from run import run


class TestRun(TestCase):
    """Tests the run.py script."""

    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_run_transform(self):
        # Test transforms - just ensure no errors
        self.runner.invoke(run, args=["--input", "tests/resources/data/"])

    def test_run_transform_with_validate(self):
        self.runner.invoke(
            run, args=["--input", "tests/resources/data/", "--kgx_validate"]
        )
