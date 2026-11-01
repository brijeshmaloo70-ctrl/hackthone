"""
scripts/api_check.py — smoke-test every CareSync API endpoint against a running server.

Usage:
    python server.py            # in one terminal
    python scripts/api_check.py [--base http://localhost:8000] [--no-llm]

Checks happy paths AND bad input (missing fields, wrong types, unknown ids, wrong method).
Note: it changes live state (SOS, check-ins, acknowledgements) and calls
POST /api/demo/reset at the end. The 30-day database history is kept.
"""

from __future__ import annotations
import argparse
import json
import sys
import time
import urllib.error
import urllib.request

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

results = []


def call(base, method, path, body=None, raw=None, timeout=60):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            status, text = r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode("utf-8")
    ms = int((time.time() - t) * 1000)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = text
    return status, payload, ms


def check(name, base, method, path, expect=200, body=None, raw=None, test=None, timeout=60):
    try:
        status, payload, ms = call(base, method, path, body, raw, timeout)
        ok = status == expect
        note = ""
        if ok and test:
            res = test(payload)
            ok, note = (res, "") if isinstance(res, bool) else res
        elif not ok:
            note = (payload.get("error") if isinstance(payload, dict) else str(payload))[:90]
    except Exception as e:  # connection refused, timeout…
        status, payload, ms, ok, note = "ERR", None, 0, False, str(e)[:90]
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {method:4} {path:42} {status!s:>4} {ms:>6}ms  {name}{('  — ' + note) if note else ''}")
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--no-llm", action="store_true", help="skip endpoints that call Gemini")
    a = ap.parse_args()
    b = a.base

    print(f"\nCareSync API check → {b}\n" + "-" * 110)
    print("GET endpoints")
    check("status + 5 agents", b, "GET", "/api/status", test=lambda d: len(d["agents"]) == 5)
    check("LLM config", b, "GET", "/api/llm/status", test=lambda d: "configured" in d)
    if not a.no_llm:
        check("LLM live test", b, "GET", "/api/llm/status?test=1",
              test=lambda d: (not d["configured"]) or (d["live_test"]["ok"], d.get("live_test", {}).get("error", "")))
    tl = check("30-day timeline", b, "GET", "/api/timeline", test=lambda d: (len(d) == 30, f"{len(d)} days — run python main.py"))
    check("doctor report", b, "GET", "/api/report", test=lambda d: d["report_markdown"].startswith("#"))
    check("clinician 10-point dashboard", b, "GET", "/api/clinician/dashboard", test=lambda d: "8_ai_observations" in d)
    if not a.no_llm:
        check("AI briefing", b, "GET", "/api/clinician/ai-briefing", test=lambda d: bool(d["briefing"]), timeout=90)
    cg = check("caregiver dashboard", b, "GET", "/api/caregiver/dashboard",
               test=lambda d: ("notifications" in d and "unacknowledged_count" in d, ""))
    plan = check("care plan", b, "GET", "/api/care-plan", test=lambda d: len(d["medications"]) > 0 or (False, "medications empty"))
    check("schedule", b, "GET", "/api/schedule", test=lambda d: len(d["schedules"]) == 4)
    check("events", b, "GET", "/api/events?limit=10", test=lambda d: "events" in d)
    check("events by type", b, "GET", "/api/events?type=RISK_ALERT_ISSUED", test=lambda d: all(e["event_type"] == "RISK_ALERT_ISSUED" for e in d["events"]))
    check("whatsapp log", b, "GET", "/api/whatsapp/messages?limit=5", test=lambda d: "messages" in d)
    check("SPA route serves React", b, "GET", "/caregiver", test=lambda d: isinstance(d, str) and 'id="root"' in d)

    print("\nPOST endpoints (happy path)")
    if not a.no_llm:
        check("chat (en, dizzy → caregiver alert)", b, "POST", "/api/chat", body={"message": "I feel dizzy", "language": "en", "day": 28},
              test=lambda d: (d["alert_level"] == 2, ""), timeout=90)
        check("chat (hi)", b, "POST", "/api/chat", body={"message": "नमस्ते आशा", "language": "hi"}, test=lambda d: bool(d["reply"]), timeout=90)
    day = (tl or [{}])[-1].get("day", 30) if isinstance(tl, list) and tl else 30
    rec = tl[21] if isinstance(tl, list) and len(tl) > 21 else None
    if rec:
        check("run-day (day 22 data)", b, "POST", "/api/schedule/run-day", body={"day": rec["day"], "data": rec},
              test=lambda d: all(r["status"] == "success" for r in d["scheduled_results"]))
    check("check-in (normal vitals)", b, "POST", "/api/patient/checkin",
          body={"day": day, "bp_systolic": 128, "bp_diastolic": 80, "blood_glucose": 140, "heart_rate": 72, "medication_taken": True, "mood": "happy"},
          test=lambda d: (d["risk_analysis"]["risk_level"] == "Normal", d["risk_analysis"]["risk_level"]))
    check("check-in (chest pain → Emergency)", b, "POST", "/api/patient/checkin",
          body={"day": day, "bp_systolic": 172, "bp_diastolic": 104, "blood_glucose": 300, "heart_rate": 95, "medication_taken": True, "mood": "dizzy", "symptoms": ["chest pain"]},
          test=lambda d: (d["risk_analysis"]["risk_level"] == "Emergency" and d["current_escalation"] == 3, d["risk_analysis"]["risk_level"]))
    sos = check("SOS emergency", b, "POST", "/api/emergency", body={"day": day}, test=lambda d: d["escalation_level"] == 3 and bool(d["alert_id"]))

    cg2 = check("caregiver sees SOS alert", b, "GET", "/api/caregiver/dashboard",
                test=lambda d: any(n["alert_id"] == (sos or {}).get("alert_id") for n in d["notifications"]) or (False, "SOS alert missing"))
    if isinstance(sos, dict) and sos.get("alert_id"):
        aid = sos["alert_id"]
        check("acknowledge SOS alert", b, "POST", "/api/caregiver/acknowledge",
              body={"alert_id": aid, "action_taken": "Called Papa", "notes": "He is resting"},
              test=lambda d: d["alert"]["acknowledged"] and d["alert"]["action_taken"] == "Called Papa")
        check("ack persisted + action logged", b, "GET", "/api/caregiver/dashboard",
              test=lambda d: any(n["alert_id"] == aid and n["acknowledged"] for n in d["notifications"]) and any(x.get("alert_id") == aid for x in d["recent_actions"]))

    pending = [p for p in (plan or {}).get("proposals", []) if p["status"] == "pending_review"]
    if pending:
        check("approve proposal", b, "POST", "/api/care-plan/review", body={"proposal_id": pending[0]["id"], "approve": True, "notes": "ok"},
              test=lambda d: d["status"] == "approved")
        check("meds list survives approval", b, "GET", "/api/care-plan", test=lambda d: isinstance(d["medications"], list) and len(d["medications"]) > 1)
        check("review twice → 409", b, "POST", "/api/care-plan/review", expect=409, body={"proposal_id": pending[0]["id"], "approve": True})
    newp = check("propose change", b, "POST", "/api/care-plan/propose",
                 body={"proposed_by": "Dr. Sharma", "category": "dietary_recommendations", "proposed_value": "Limit salt to 1.5g/day", "reason": "BP"},
                 test=lambda d: d["proposal"]["status"] == "pending_review")
    if isinstance(newp, dict) and newp.get("proposal"):
        check("reject proposal", b, "POST", "/api/care-plan/review", body={"proposal_id": newp["proposal"]["id"], "approve": False, "notes": "later"},
              test=lambda d: d["status"] == "rejected")
    check("simulate inbound WhatsApp", b, "POST", "/api/whatsapp/simulate-inbound", body={"message": "Papa is fine"}, test=lambda d: d["success"])

    print("\nBad input / error handling")
    check("unknown API → 404", b, "GET", "/api/does-not-exist", expect=404)
    check("POST on GET route → 405", b, "POST", "/api/status", expect=405, body={})
    check("GET on POST route → 405", b, "GET", "/api/chat", expect=405)
    check("invalid JSON → 400", b, "POST", "/api/chat", expect=400, raw=b"{not json")
    check("JSON array body → 400", b, "POST", "/api/chat", expect=400, raw=b"[1,2]")
    check("empty chat message → 400", b, "POST", "/api/chat", expect=400, body={"message": "  "})
    check("non-numeric BP → 400", b, "POST", "/api/patient/checkin", expect=400, body={"bp_systolic": "abc"})
    check("BP out of range → 400", b, "POST", "/api/patient/checkin", expect=400, body={"bp_systolic": 999})
    check("symptoms not a list → 400", b, "POST", "/api/patient/checkin", expect=400, body={"symptoms": "headache"})
    check("ack missing alert_id → 400", b, "POST", "/api/caregiver/acknowledge", expect=400, body={"action_taken": "x"})
    check("ack missing action → 400", b, "POST", "/api/caregiver/acknowledge", expect=400, body={"alert_id": "alert_x"})
    check("ack unknown alert → 404", b, "POST", "/api/caregiver/acknowledge", expect=404, body={"alert_id": "alert_nope", "action_taken": "x"})
    check("review unknown proposal → 404", b, "POST", "/api/care-plan/review", expect=404, body={"proposal_id": "prop_nope"})
    check("propose without value → 400", b, "POST", "/api/care-plan/propose", expect=400, body={"category": "x"})
    check("bad limit → 400", b, "GET", "/api/events?limit=abc", expect=400)
    check("run-day bad data → 400", b, "POST", "/api/schedule/run-day", expect=400, body={"day": 3, "data": "x"})

    print("\nCleanup")
    r = check("reset live session", b, "POST", "/api/demo/reset", body={}, test=lambda d: d["success"])
    restored = (r or {}).get("escalation_level") if isinstance(r, dict) else None
    check("escalation restored from latest reading", b, "GET", "/api/status",
          test=lambda d: (d["escalation_level"] == restored and d["escalation_level"] < 3, f"level {d['escalation_level']}"))
    check("events cleared by reset", b, "GET", "/api/events", test=lambda d: d["count"] == 0)

    passed = sum(results)
    print("-" * 110 + f"\n{passed}/{len(results)} checks passed\n")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
