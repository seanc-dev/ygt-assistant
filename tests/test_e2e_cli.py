"""End-to-end CLI tests that run the full pipeline: CLI → LLM → EventKit."""

import pytest
import subprocess
import sys
import os
from datetime import datetime, timedelta
import time


@pytest.mark.e2e
class TestEndToEndCLI:
    """Test the full CLI pipeline with real user input simulation."""

    def run_cli_command(self, inputs, timeout=30):
        """Run the CLI with a list of inputs and capture output."""
        # Prepare input string (each input on a new line)
        input_text = "\n".join(inputs) + "\n"

        # Run the CLI process
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "CALENDAR_NAME": "Testing Calendar"},
        )

        try:
            stdout, stderr = process.communicate(input=input_text, timeout=timeout)
            return process.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise TimeoutError(f"CLI process timed out after {timeout} seconds")

    def test_cli_welcome_and_exit(self):
        """Test basic CLI startup and exit."""
        print("\n=== Testing: CLI welcome and exit ===")

        inputs = ["exit"]
        returncode, stdout, stderr = self.run_cli_command(inputs)

        print(f"Return code: {returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

        assert returncode == 0, f"CLI should exit cleanly, got return code {returncode}"
        assert "Welcome to the Terminal Calendar Assistant" in stdout
        assert "Goodbye!" in stdout

    def test_cli_list_events_today(self):
        """Test listing today's events through full pipeline."""
        print("\n=== Testing: List today's events (full pipeline) ===")

        inputs = ["show me today's events", "exit"]
        returncode, stdout, stderr = self.run_cli_command(inputs)

        print(f"Return code: {returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

        assert returncode == 0, f"CLI should exit cleanly, got return code {returncode}"
        assert (
            "📅 Events:" in stdout
            or "⏰ Reminders:" in stdout
            or "No events found" in stdout
        )

    def test_cli_create_event(self):
        """Test creating an event through full pipeline."""
        print("\n=== Testing: Create event (full pipeline) ===")

        # Use a future date to avoid conflicts
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        inputs = [
            f"schedule team meeting on {future_date} at 2pm for 60 minutes",
            "exit",
        ]

        returncode, stdout, stderr = self.run_cli_command(inputs)

        print(f"Return code: {returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

        assert returncode == 0, f"CLI should exit cleanly, got return code {returncode}"
        # Should either succeed or show an error message, but not crash
        assert "✅" in stdout or "❌" in stdout or "Error" in stdout

    def test_cli_create_event_with_location(self):
        """Test creating an event with location through full pipeline."""
        print("\n=== Testing: Create event with location (full pipeline) ===")

        future_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
        inputs = [
            f"schedule meeting at conference room A on {future_date} at 3pm for 30 minutes",
            "exit",
        ]

        returncode, stdout, stderr = self.run_cli_command(inputs)

        print(f"Return code: {returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

        assert returncode == 0, f"CLI should exit cleanly, got return code {returncode}"
        assert "✅" in stdout or "❌" in stdout or "Error" in stdout

    def test_cli_delete_event(self):
        """Test deleting an event through full pipeline."""
        print("\n=== Testing: Delete event (full pipeline) ===")

        future_date = (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d")
        inputs = [f"delete team meeting on {future_date}", "exit"]

        returncode, stdout, stderr = self.run_cli_command(inputs)

        print(f"Return code: {returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

        assert returncode == 0, f"CLI should exit cleanly, got return code {returncode}"
        assert (
            "✅" in stdout
            or "❌" in stdout
            or "Error" in stdout
            or "not found" in stdout.lower()
        )

    def test_cli_move_event(self):
        """Test moving an event through full pipeline."""
        print("\n=== Testing: Move event (full pipeline) ===")

        future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        new_date = (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%d")
        inputs = [f"move team meeting on {future_date} to {new_date} at 4pm", "exit"]

        returncode, stdout, stderr = self.run_cli_command(inputs)

        print(f"Return code: {returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

        assert returncode == 0, f"CLI should exit cleanly, got return code {returncode}"
        assert (
            "✅" in stdout
            or "❌" in stdout
            or "Error" in stdout
            or "not found" in stdout.lower()
        )

    def test_cli_add_notification(self):
        """Test adding a notification through full pipeline."""
        print("\n=== Testing: Add notification (full pipeline) ===")

        future_date = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d")
        inputs = [
            f"add notification to team meeting on {future_date} 15 minutes before",
            "exit",
        ]

        returncode, stdout, stderr = self.run_cli_command(inputs)

        print(f"Return code: {returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

        assert returncode == 0, f"CLI should exit cleanly, got return code {returncode}"
        assert (
            "✅" in stdout
            or "❌" in stdout
            or "Error" in stdout
            or "not found" in stdout.lower()
        )

    def test_cli_list_specific_date(self):
        """Test listing events for a specific date through full pipeline."""
        print("\n=== Testing: List specific date (full pipeline) ===")

        future_date = (datetime.now() + timedelta(days=13)).strftime("%Y-%m-%d")
        inputs = [f"events for {future_date}", "exit"]

        returncode, stdout, stderr = self.run_cli_command(inputs)

        print(f"Return code: {returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

        assert returncode == 0, f"CLI should exit cleanly, got return code {returncode}"
        assert (
            "📅 Events:" in stdout
            or "⏰ Reminders:" in stdout
            or "No events found" in stdout
        )

    def test_cli_list_date_range(self):
        """Test listing events for a date range through full pipeline."""
        print("\n=== Testing: List date range (full pipeline) ===")

        start_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=16)).strftime("%Y-%m-%d")
        inputs = [f"list events from {start_date} to {end_date}", "exit"]

        returncode, stdout, stderr = self.run_cli_command(inputs)

        print(f"Return code: {returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

        assert returncode == 0, f"CLI should exit cleanly, got return code {returncode}"
        assert (
            "📅 Events:" in stdout
            or "⏰ Reminders:" in stdout
            or "No events found" in stdout
        )

    def test_cli_natural_language_parsing(self):
        """Test natural language parsing through full pipeline."""
        print("\n=== Testing: Natural language parsing (full pipeline) ===")

        test_cases = [
            ("show me tomorrow's events", ["show me tomorrow's events", "exit"]),
            ("what's on Friday", ["what's on Friday", "exit"]),
            (
                "schedule lunch tomorrow at noon",
                ["schedule lunch tomorrow at noon", "60", "exit"],
            ),
            ("delete the meeting on Monday", ["delete the meeting on Monday", "exit"]),
        ]

        for command, inputs in test_cases:
            print(f"Testing command: '{command}'")

            returncode, stdout, stderr = self.run_cli_command(inputs)

            print(f"Return code: {returncode}")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")

            assert (
                returncode == 0
            ), f"CLI should exit cleanly for '{command}', got return code {returncode}"
            # Should not crash, even if it doesn't understand the command
            assert "Welcome to the Terminal Calendar Assistant" in stdout

    def test_cli_error_handling(self):
        """Test error handling through full pipeline."""
        print("\n=== Testing: Error handling (full pipeline) ===")

        # Test with invalid commands
        invalid_commands = [
            ("invalid command", ["invalid command", "exit"]),
            (
                "schedule meeting on invalid-date",
                ["schedule meeting on invalid-date", "60", "exit"],
            ),
            (
                "delete event that doesn't exist",
                ["delete event that doesn't exist", "exit"],
            ),
            ("move event to invalid time", ["move event to invalid time", "exit"]),
        ]

        for command, inputs in invalid_commands:
            print(f"Testing invalid command: '{command}'")

            returncode, stdout, stderr = self.run_cli_command(inputs)

            print(f"Return code: {returncode}")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")

            assert (
                returncode == 0
            ), f"CLI should handle invalid command '{command}' gracefully, got return code {returncode}"
            # Should not crash, should show some kind of response
            assert "Welcome to the Terminal Calendar Assistant" in stdout

    def test_cli_multiple_commands(self):
        """Test running multiple commands in sequence."""
        print("\n=== Testing: Multiple commands in sequence (full pipeline) ===")

        future_date = (datetime.now() + timedelta(days=17)).strftime("%Y-%m-%d")
        inputs = [
            "show me today's events",
            f"schedule test meeting on {future_date} at 10am for 30 minutes",
            f"events for {future_date}",
            f"delete test meeting on {future_date}",
            "exit",
        ]

        returncode, stdout, stderr = self.run_cli_command(inputs, timeout=60)

        print(f"Return code: {returncode}")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

        assert (
            returncode == 0
        ), f"CLI should handle multiple commands, got return code {returncode}"
        assert "Welcome to the Terminal Calendar Assistant" in stdout
        assert "Goodbye!" in stdout

    def test_cli_exit_commands(self):
        """Test all exit commands work properly."""
        print("\n=== Testing: All exit commands (full pipeline) ===")

        exit_commands = ["exit", "quit", "q"]

        for cmd in exit_commands:
            print(f"Testing exit command: '{cmd}'")
            inputs = [cmd]

            returncode, stdout, stderr = self.run_cli_command(inputs)

            print(f"Return code: {returncode}")
            print(f"STDOUT: {stdout}")
            print(f"STDERR: {stderr}")

            assert (
                returncode == 0
            ), f"CLI should exit with '{cmd}', got return code {returncode}"
            assert "Welcome to the Terminal Calendar Assistant" in stdout
            assert "Goodbye!" in stdout


if __name__ == "__main__":
    print("Running end-to-end CLI tests...")
    pytest.main([__file__, "-v"])
