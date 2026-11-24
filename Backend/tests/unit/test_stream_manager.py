"""Unit tests for DebateRunStreamManager."""

import pytest
import asyncio
from src.adapters.orchestration.stream_manager import DebateRunStreamManager


@pytest.mark.asyncio
async def test_stream_manager_basic():
    import uuid
    manager = DebateRunStreamManager()
    run_id = f"test-run-{uuid.uuid4()}"

    # Add events
    ev1 = await manager.add_event(run_id, "node_start", node_name="supervisor")
    assert ev1["seq"] == 1
    assert ev1["event_type"] == "node_start"
    assert ev1["node_name"] == "supervisor"
    assert ev1["run_id"] == run_id

    ev2 = await manager.add_event(run_id, "node_end", node_name="supervisor")
    assert ev2["seq"] == 2

    # Get latest seq
    latest = await manager.get_latest_seq(run_id)
    assert latest == 2

    # Get events after seq 1
    after = await manager.get_events_after(run_id, 1)
    assert len(after) == 1
    assert after[0]["seq"] == 2

    # Set and get state
    await manager.set_state(run_id, {"status": "completed", "verdict": "BUY"})
    state = await manager.get_state(run_id)
    assert state["verdict"] == "BUY"
