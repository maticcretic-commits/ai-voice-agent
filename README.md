# AI Voice Agent

A portfolio practice project: starter for the **AI voice-agent build** gig pattern
(Vapi/Retell + Twilio, scheduling, CRM integration — the "$2,000 fixed" bracket).

> Demo/study project — connect real telephony and EHR/CRM APIs before any
> production use.

## What it does

- `POST /voice/incoming` — Twilio-style webhook, answers with TwiML
  (hand-built XML, no SDK required).
- `POST /voice/gather` — routes caller speech to intents: **booking**,
  **hours**, **human handoff**, fallback.
- `POST /sms/confirm` — books a slot from `data/slots.json` and logs the
  confirmation SMS (stub — swap `log_sms()` for the Twilio API).
- Every call and SMS is appended to `call_log.jsonl` for review.

## Setup & run

```bash
pip install -r requirements.txt
python voice_agent.py          # http://localhost:5000
python tests/test_voice_agent.py
```

Try it:

```bash
curl -X POST localhost:5000/voice/gather \
  -d "From=+10000000000" -d "SpeechResult=I want to book an appointment"
```

## What I'd build next (learning roadmap)

- [ ] LLM intent classifier instead of keywords
- [ ] Real Twilio + Vapi/Retell wiring
- [ ] Calendar/EHR API for live availability
- [ ] CRM write-back on completed calls
- [ ] Call recording summaries with an LLM

## Support My Work

If you find this project useful, consider supporting my work with a Bitcoin donation:

`BC1Q6Q75K8ZJXVW7W02LMDPRPY6XX6QK4LZZ2RMVAY`
