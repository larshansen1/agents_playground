from unittest.mock import patch

from app.worker import run_worker


def test_run_worker_creates_state_machine():
    """Test that run_worker creates and runs the state machine."""
    with patch("app.worker_state.WorkerStateMachine") as mock_state_machine:
        mock_instance = mock_state_machine.return_value

        run_worker()

        mock_state_machine.assert_called_once()
        mock_instance.run.assert_called_once()


def test_run_worker_uses_instance_name_as_worker_id():
    """Test that run_worker uses the instance name as the worker ID."""
    with (
        patch("app.worker_state.WorkerStateMachine") as mock_state_machine,
        patch("app.worker.get_instance_name", return_value="test-worker-1"),
    ):
        run_worker()

        mock_state_machine.assert_called_once_with(worker_id="test-worker-1")
