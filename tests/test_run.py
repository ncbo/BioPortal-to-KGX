"""Tests for BioPortal-to-KGX."""

from unittest import TestCase

from click.testing import CliRunner

from run import run


class TestRun(TestCase):
    """Tests the run.py script."""

    def setUp(self) -> None:
        """Setup for tests."""
        self.runner = CliRunner()

    def test_run_transform(self):
        """Test transforms to just ensure no errors."""
        self.runner.invoke(run, args=["--input", "tests/resources/data/"])

    def test_run_transform_with_validate(self):
        """Test transforms and run KGX validation."""
        self.runner.invoke(
            run, args=["--input", "tests/resources/data/", "--kgx_validate"]
        )
