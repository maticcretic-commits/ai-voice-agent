#!/usr/bin/env python3
"""
AI Voice Agent — portfolio practice project.

Starter for the "$2,000 fixed" AI voice-agent gig pattern
(Vapi/Retell + Twilio + scheduling + CRM).

What this demo implements (Flask, stdlib + flask only):
  * POST /voice/incoming  — Twilio-style webhook; replies with TwiML
    (built as plain XML strings, no SDK needed).
  * Intent routing: booking, hours, human handoff, fallback.
  * Appointment booking against data/slots.json; confirmation "SMS"
    is logged (swap log_sms() for the Twilio API in production).
  * Every call appended to call_log.jsonl for review.

Usage:
    pip install -r requirements.txt
    python voice_agent.py            # http://localhost:5000
    python tests/test_voice_agent.py

Point a Twilio number's voice webhook at /voice/incoming in production.
"""

import json
import re
from datetime import datetime
from pathlib import Path

from flask import Flask, request, Response

BASE = Path(__file__).resolve().parent
SLOTS_PATH = BASE / "data" / "slots.json"
LOG_PATH = BASE / "call_log.jsonl"

# TODO(learn): replace keyword intents with an LLM classifier and compare
# accuracy on 20 sample caller phrases.

INTENTS = {
    "booking": ["book", "appointment", "schedule", "slot", "available"],
    "hours": ["hour", "open", "close", "timing", "when are you"],
    "human": ["human", "agent", "person", "representative", "someone"],
}


def classify_intent(text):
    text = text.lower()
    for intent, keywords in INTENTS.items():
        if any(k in text for k in keywords):
            return intent
    return "fallback"


def twiml_say(message, next_action=None):
    action = f' action="{next_action}"' if next_action else ""
    return (f'<?xml version="1.0" encoding="UTF-8"?>'
            f'<Response><Say>{message}</Say>'
            f'<Gather input="speech"{action}></Gather></Response>')


def load_slots():
    return json.loads(SLOTS_PATH.read_text())


def book_slot(name, slot):
    slots = load_slots()
    if slot not in slots.get("available", []):
        return None
    slots["available"].remove(slot)
    slots.setdefault("booked", []).append({"slot": slot, "name": name})
    SLOTS_PATH.write_text(json.dumps(slots, indent=2))
    return slot


def log_sms(to_number, body):
    # TODO(learn): swap this stub for Twilio's messages.create() call.
    entry = {"type": "sms", "to": to_number, "body": body,
             "at": datetime.utcnow().isoformat()}
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def log_call(caller, speech, intent, outcome):
    entry = {"type": "call", "caller": caller, "speech": speech,
             "intent": intent, "outcome": outcome,
             "at": datetime.utcnow().isoformat()}
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def handle_speech(caller, speech):
    intent = classify_intent(speech or "")
    if intent == "booking":
        slots = load_slots()["available"][:3]
        options = ", ".join(slots) if slots else "no open slots right now"
        outcome = f"offered slots: {options}"
        reply = (f"We have these openings: {options}. "
                 f"Reply with the date and time to confirm.")
    elif intent == "hours":
        outcome = "gave hours"
        reply = "We are open Monday to Friday, 9 AM to 6 PM."
    elif intent == "human":
        outcome = "escalated to human"
        reply = "Connecting you to a team member now."
    else:
        outcome = "fallback"
        reply = ("Sorry, I didn't catch that. You can ask about booking, "
                 "our hours, or say 'human' to reach the team.")
    log_call(caller, speech, intent, outcome)
    return twiml_say(reply)


app = Flask(__name__)


@app.post("/voice/incoming")
def voice_incoming():
    caller = request.form.get("From", "unknown")
    return Response(twiml_say("Hello! How can I help you today?"),
                    mimetype="text/xml")


@app.post("/voice/gather")
def voice_gather():
    caller = request.form.get("From", "unknown")
    speech = request.form.get("SpeechResult", "")
    return Response(handle_speech(caller, speech), mimetype="text/xml")


@app.post("/sms/confirm")
def sms_confirm():
    """Book a slot and 'send' the SMS confirmation. Form: name, slot, to."""
    slot = book_slot(request.form.get("name", "guest"),
                     request.form.get("slot", ""))
    if not slot:
        return {"ok": False, "error": "slot not available"}, 400
    log_sms(request.form.get("to", "unknown"),
            f"Your appointment is confirmed for {slot}. Reply STOP to cancel.")
    return {"ok": True, "slot": slot}


if __name__ == "__main__":
    app.run(port=5000, debug=True)
