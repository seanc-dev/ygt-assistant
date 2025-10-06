"""Test main.py CLI functionality."""

from unittest.mock import patch
import runpy


def test_main_loop_exit():
    """Test that main loop exits on 'exit' command."""
    with patch("builtins.input", side_effect=["exit"]):
        with patch("builtins.print") as mock_print:
            runpy.run_module("main", run_name="__main__")
            # Check that goodbye message was printed
            mock_print.assert_called_with("Goodbye!")


def test_main_loop_quit():
    """Test that main loop exits on 'quit' command."""
    with patch("builtins.input", side_effect=["quit"]):
        with patch("builtins.print") as mock_print:
            runpy.run_module("main", run_name="__main__")
            # Check that goodbye message was printed
            mock_print.assert_called_with("Goodbye!")


def test_main_loop_q():
    """Test that main loop exits on 'q' command."""
    with patch("builtins.input", side_effect=["q"]):
        with patch("builtins.print") as mock_print:
            runpy.run_module("main", run_name="__main__")
            # Check that goodbye message was printed
            mock_print.assert_called_with("Goodbye!")
