"""Offline tests for the voice agent (no API keys needed)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import voice_agent
from voice_agent import classify_intent, twiml_say, book_slot, app


def test_classify_booking():
    assert classify_intent("I want to book an appointment") == "booking"


def test_classify_hours():
    assert classify_intent("What are your hours?") == "hours"


def test_classify_human():
    assert classify_intent("Let me talk to a human") == "human"


def test_classify_fallback():
    assert classify_intent("Tell me about the weather") == "fallback"


def test_twiml_is_valid_xml_shape():
    xml = twiml_say("Hello")
    assert xml.startswith("<?xml")
    assert "<Say>Hello</Say>" in xml
    assert "<Response>" in xml


def test_book_slot_removes_availability(tmp_path=None):
    # Use a temp slots file so tests don't clobber the sample data.
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fake = Path(d) / "slots.json"
        fake.write_text(json.dumps({"available": ["2026-09-24 10:00"], "booked": []}))
        old = voice_agent.SLOTS_PATH
        voice_agent.SLOTS_PATH = fake
        try:
            assert book_slot("Test", "2026-09-24 10:00") == "2026-09-24 10:00"
            assert book_slot("Test2", "2026-09-24 10:00") is None  # already taken
        finally:
            voice_agent.SLOTS_PATH = old


def test_incoming_webhook_returns_twiml():
    client = app.test_client()
    resp = client.post("/voice/incoming", data={"From": "+10000000000"})
    assert resp.status_code == 200
    assert b"<Response>" in resp.data


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_"):
            fn()
            print(f"PASS {name}")
    print("All tests passed.")
