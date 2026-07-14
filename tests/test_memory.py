import tempfile
from pathlib import Path
import pytest

from tools import memory

# Override memory path
TEST_MEMORY = Path(tempfile.gettempdir()) / "test_memory.json"
memory.MEMORY_PATH = TEST_MEMORY

@pytest.fixture(autouse=True)
def cleanup():
    if TEST_MEMORY.exists():
        TEST_MEMORY.unlink()
    yield
    if TEST_MEMORY.exists():
        TEST_MEMORY.unlink()

def test_was_processed():
    assert not memory.was_processed("ad_123")
    memory.mark_processed("ad_123", {"title": "Test Ad"})
    assert memory.was_processed("ad_123")
    
    val = memory.get_previous_value("ad_123")
    assert val["title"] == "Test Ad"

def test_detect_changes():
    key = "competitor_brief"
    h1 = memory.content_hash("content version 1")
    memory.mark_processed(key, {"content_hash": h1})
    
    # Same content
    assert memory.detect_changes(key, h1) is None
    
    # Changed content
    h2 = memory.content_hash("content version 2")
    old_hash = memory.detect_changes(key, h2)
    assert old_hash == h1

def test_log_run():
    assert len(memory.get_run_history()) == 0
    memory.log_run("Initial test run complete.")
    history = memory.get_run_history()
    assert len(history) == 1
    assert history[0]["summary"] == "Initial test run complete."
