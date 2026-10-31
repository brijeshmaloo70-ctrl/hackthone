"""Agents:  SenseAgent -> ReasonAgent -> GovernAgent -> ActAgent (loop)
Features: shared persistent state, tool schemas, routing, human-approval
interrupts (interrupt()/Command(resume=...)), audit log, demo transcript.

Install:  pip install langgraph
Run:      python asha_agent.py            (interactive approval prompt)
          python asha_agent.py --auto     (auto-approve for a quick demo)

All tools are SIMULATED. Asha never diagnoses, prescribes or changes medication.
"""


from __future__ import annotations

import json
import sys
from datetime import datetime
from typing import Annotated, Literal, TypedDict
import operator

from langgraph.checkpoint.memory import MemorySaver  # swap for SqliteSaver/PostgresSaver in production
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

# ---------------------------------------------------------------------------
# Shared state schema
# ---------------------------------------------------------------------------

class Explanation(TypedDict):
    signal: str
    why: str
    confidence: str
    action: str
    responsible_human: str
    follow_up: str


class AuditEntry(TypedDict):
    ts: str
    actor: str
    action: str
    rationale: str
    evidence: list[str]
    approval_status: str


class CareProfile(TypedDict):
    patient_id: str
    name: str
    age: int
    history: list[str]
    medications: list[str]
    allergies: list[str]
    care_plan: str
    baseline: dict[str, float]
    caregivers: dict[str, dict]
    communication_prefs: str
    intervention_history: list[str]
    consent_scope: dict[str, str]
    open_tasks: list[str]


class AshaState(TypedDict):
    profile: CareProfile
    day: int
    readings: list[dict]                       # normalized timeline
    symptoms: dict[str, str]
    risk: float
    risk_label: str
    explanation: Explanation | None
    proposed_actions: list[dict]
    completed_actions: list[str]
    appointment_done: bool
    audit: Annotated[list[AuditEntry], operator.add]
    transcript: Annotated[list[str], operator.add]


# ---------------------------------------------------------------------------
# Simulated data feeds
# ---------------------------------------------------------------------------

SIMULATED_FEED = {
    1: {"steps": 3600, "rhr": 72, "weight": 71.9, "sleep": 6.4, "diuretic_taken": True},
    2: {"steps": 2700, "rhr": 76, "weight": 72.6, "sleep": 5.8, "diuretic_taken": False},
    3: {"steps": 1900, "rhr": 81, "weight": 73.4, "sleep": 5.1, "diuretic_taken": False},
}

SIMULATED_PATIENT_ANSWERS = {
    "ankle_swelling": "Yes, my socks are leaving marks.",
    "breathlessness": "The stairs make me puff more than before.",
    "orthopnea": "Two pillows since Tuesday.",
    "chest_pain": "No.",
    "barrier": "I skip the water tablet — it makes me run to the bathroom.",
}


def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def log(actor, action, rationale, evidence=None, status="n/a") -> AuditEntry:
    return {"ts": now(), "actor": actor, "action": action, "rationale": rationale,
            "evidence": evidence or [], "approval_status": status}


# ---------------------------------------------------------------------------
# Tools (schemas match the spec; implementations are simulated)
# ---------------------------------------------------------------------------

def check_symptoms(patient_id: str, questions: list[str]) -> dict[str, str]:
    return {q: SIMULATED_PATIENT_ANSWERS.get(q, "Not sure.") for q in questions}


def send_sms(contact_id: str, message: str) -> str:
    return f"SMS -> {contact_id}: {message}"


def make_voice_call(contact_id: str, script: str) -> str:
    return f"VOICE -> {contact_id}: {script}"


def schedule_appointment(patient_id: str, care_team_member: str, urgency: str) -> str:
    return f"Booked {urgency} telecheck with {care_team_member} for {patient_id} at 11:30"


def notify_caregiver(caregiver_id: str, summary: str, consent_token: str) -> str:
    if not consent_token:
        raise PermissionError("No consent token — contact blocked")
    return f"CAREGIVER -> {caregiver_id}: {summary}"


def create_clinician_task(patient_id: str, urgency: str, structured_brief: str) -> str:
    return f"EHR task ({urgency}) for {patient_id}:\n{structured_brief}"


def request_human_approval(action: str, rationale: str, evidence: list[str]) -> dict:
    # Pauses the graph; resumed with Command(resume={"decision": ..., "note": ...})
    return interrupt({"action": action, "rationale": rationale, "evidence": evidence})


TOOL_SCHEMAS = [
    {"name": "check_symptoms", "params": {"patient_id": "str", "questions": "list[str]"}, "risk": "low"},
    {"name": "send_sms", "params": {"contact_id": "str", "message": "str"}, "risk": "low"},
    {"name": "make_voice_call", "params": {"contact_id": "str", "script": "str"}, "risk": "low"},
    {"name": "schedule_appointment", "params": {"patient_id": "str", "care_team_member": "str", "urgency": "str"}, "risk": "medium"},
    {"name": "notify_caregiver", "params": {"caregiver_id": "str", "summary": "str", "consent_token": "str"}, "risk": "medium"},
    {"name": "create_clinician_task", "params": {"patient_id": "str", "urgency": "str", "structured_brief": "str"}, "risk": "high"},
    {"name": "log_action", "params": {"actor": "str", "action": "str", "rationale": "str", "evidence": "list", "approval_status": "str"}, "risk": "none"},
    {"name": "request_human_approval", "params": {"action": "str", "rationale": "str", "evidence": "list"}, "risk": "none"},
]

# Policy: which actions need what
POLICY = {
    "send_sms": "autonomous",
    "check_symptoms": "autonomous",
    "make_voice_call": "autonomous",
    "notify_caregiver": "notify_patient",
    "schedule_appointment": "notify_patient",
    "create_clinician_task": "human_approval",
}

FORBIDDEN = ("diagnose", "prescribe", "change_medication", "adjust_dose")


# ---------------------------------------------------------------------------
# Agents (graph nodes)
# ---------------------------------------------------------------------------

def sense_agent(state: AshaState) -> dict:
    day = state["day"] + 1
    reading = {"day": day, **SIMULATED_FEED[day]}
    b = state["profile"]["baseline"]
    msg = (f"[SenseAgent] Day {day}: steps {reading['steps']} (base {b['steps']:.0f}), "
           f"RHR {reading['rhr']} (base {b['rhr']:.0f}), weight {reading['weight']} kg "
           f"(base {b['weight']}), diuretic {'taken' if reading['diuretic_taken'] else 'MISSED'}")
    return {"day": day, "readings": state["readings"] + [reading], "transcript": [msg],
            "audit": [log("SenseAgent", "normalize_timeline", "Ingested wearable/pharmacy feed", [msg])]}


def reason_agent(state: AshaState) -> dict:
    b = state["profile"]["baseline"]
    r = state["readings"][-1]
    missed = sum(1 for x in state["readings"] if not x["diuretic_taken"])

    # Personalized deviations (not generic thresholds)
    score = 0.0
    score += min(max((r["weight"] - b["weight"]) / 2.0, 0), 1) * 0.30
    score += min(max((r["rhr"] - b["rhr"]) / 15.0, 0), 1) * 0.20
    score += min(max((b["steps"] - r["steps"]) / b["steps"] / 0.5, 0), 1) * 0.15
    score += min(missed / 2, 1) * 0.10
    if state["symptoms"]:
        s = state["symptoms"]
        score += 0.08 * ("yes" in s.get("ankle_swelling", "").lower())
        score += 0.08 * ("puff" in s.get("breathlessness", "").lower())
        score += 0.06 * ("pillow" in s.get("orthopnea", "").lower())
    risk = round(min(score * 0.7 + 0.05, 0.99), 2)
    emergency = state["symptoms"].get("chest_pain", "no").lower().startswith("yes")
    label = "emergency" if emergency else "moderate" if risk >= 0.55 else "watch" if risk >= 0.3 else "low"

    evidence = [f"weight {b['weight']}→{r['weight']} kg", f"RHR {b['rhr']:.0f}→{r['rhr']}",
                f"steps {b['steps']:.0f}→{r['steps']}", f"missed diuretic x{missed}"]

    proposed: list[dict] = []
    if label == "emergency":
        proposed = [{"tool": "emergency_workflow"}]
    elif state["appointment_done"]:
        proposed = [{"tool": "make_voice_call", "purpose": "post-appointment follow-up"}]
    elif label == "moderate" and not state["symptoms"]:
        proposed = [{"tool": "check_symptoms"}]
    elif label == "moderate" and state["symptoms"]:
        proposed = [{"tool": "create_clinician_task"}, {"tool": "schedule_appointment"}, {"tool": "notify_caregiver"}]
    elif not r["diuretic_taken"]:
        proposed = [{"tool": "send_sms", "purpose": "medication reminder"}]

    expl: Explanation = {
        "signal": "; ".join(evidence),
        "why": "Combined weight gain, rising heart rate, falling activity and missed diuretic often precede HF decompensation; matches his prior March episode.",
        "confidence": f"{label} ({risk})" + ("" if state["symptoms"] else " — no symptom report yet"),
        "action": ", ".join(p["tool"] for p in proposed) or "continue monitoring",
        "responsible_human": "Nurse Anjali Mehta, RN" if label == "moderate" else "none",
        "follow_up": "after check-in" if proposed else "next daily reading",
    }
    return {"risk": risk, "risk_label": label, "explanation": expl, "proposed_actions": proposed,
            "transcript": [f"[ReasonAgent] risk={risk} ({label}) → {expl['action']}"],
            "audit": [log("ReasonAgent", "estimate_risk", expl["why"], evidence)]}


def govern_agent(state: AshaState) -> dict:
    """Enforces hard constraints, consent and human-in-the-loop approval."""
    approved: list[dict] = []
    audit: list[AuditEntry] = []
    transcript: list[str] = []

    for action in state["proposed_actions"]:
        tool = action["tool"]
        if any(f in tool for f in FORBIDDEN):
            audit.append(log("GovernAgent", tool, "Hard constraint: refused", status="refused"))
            continue
        if tool == "emergency_workflow":
            approved.append(action)  # predefined workflow runs immediately
            continue
        policy = POLICY.get(tool, "human_approval")

        if tool == "notify_caregiver":
            token = state["profile"]["consent_scope"].get("priya")
            if not token:
                audit.append(log("GovernAgent", tool, "No verified consent — blocked", status="refused"))
                continue
            action["consent_token"] = token

        if policy == "human_approval":
            e = state["explanation"]
            decision = request_human_approval(
                action=f"{tool}(urgency=same-day) + schedule_appointment(nurse telecheck)",
                rationale=f"{e['confidence']}. {e['why']} Asha does not diagnose or adjust medication.",
                evidence=e["signal"].split("; "),
            )
            status = decision.get("decision", "rejected")
            audit.append(log("GovernAgent", tool, decision.get("note", ""), e["signal"].split("; "), status))
            transcript.append(f"[Human] Nurse decision: {status} — {decision.get('note', '')}")
            if status != "approved":
                # Override respected: drop all escalation actions, schedule safe fallback
                approved = [{"tool": "send_sms", "purpose": "self-care education + recheck in 4h"}]
                break
            approved.append(action)
        else:
            if policy == "notify_patient":
                transcript.append(f"[GovernAgent] Patient informed before {tool}")
            approved.append(action)

    transcript.append(f"[GovernAgent] Cleared: {[a['tool'] for a in approved]}")
    return {"proposed_actions": approved, "audit": audit, "transcript": transcript}


def act_agent(state: AshaState) -> dict:
    p = state["profile"]
    pid = p["patient_id"]
    out: list[str] = []
    audit: list[AuditEntry] = []
    symptoms = state["symptoms"]
    appointment_done = state["appointment_done"]
    done = list(state["completed_actions"])

    for a in state["proposed_actions"]:
        t = a["tool"]
        if t == "send_sms":
            r = send_sms(pid, "Good morning Mr. Rao — your water tablet is still in the cap. Shall I remind you at 10?"
                         if a.get("purpose") == "medication reminder"
                         else "Please rest with legs raised and weigh yourself at 4 pm. I'll check in then.")
        elif t == "check_symptoms":
            symptoms = check_symptoms(pid, list(SIMULATED_PATIENT_ANSWERS))
            r = "VOICE check-in:\n" + "\n".join(f"   Q {q}: {ans}" for q, ans in symptoms.items())
        elif t == "create_clinician_task":
            brief = ("SBAR · S: 74M HFrEF, 3-day weight +2.2 kg, RHR +13. "
                     "B: March admission w/ similar pattern. "
                     "A: edema, exertional dyspnea, 2-pillow orthopnea; missed furosemide x2 (urination burden). "
                     "R: same-day assessment; consider adherence plan. Asha has NOT advised medication changes.")
            r = create_clinician_task(pid, "same-day", brief)
        elif t == "schedule_appointment":
            r = schedule_appointment(pid, "Nurse Anjali Mehta", "same-day")
        elif t == "notify_caregiver":
            r = notify_caregiver("priya", "Your father's nurse will video-call him today at 11:30 about swelling and "
                                 "breathlessness. He agreed. Could you help him join? No emergency right now.",
                                 a["consent_token"])
        elif t == "make_voice_call":
            r = make_voice_call(pid, "How did the nurse call go? I'll remind you at 2 pm and check your weight tomorrow.")
            p = {**p,
                 "intervention_history": p["intervention_history"] + [
                     "Day 3: early HF deterioration caught via wt+RHR+steps; nurse telecheck same day."],
                 "care_plan": p["care_plan"] + " | Clinician moved diuretic to 2 pm (adherence barrier: morning urination).",
                 "open_tasks": []}
            r += "\n   [Memory] care profile updated with episode outcome & adherence barrier"
            appointment_done = False
            done.append("follow_up")
        elif t == "emergency_workflow":
            r = "EMERGENCY workflow: call emergency services + on-call clinician + caregiver"
        else:
            continue
        out.append(f"[ActAgent] {r}")
        audit.append(log("ActAgent", t, a.get("purpose", "policy-cleared action"), status="executed"))
        done.append(t)

    if "schedule_appointment" in [a["tool"] for a in state["proposed_actions"]]:
        out.append("[Human] Nurse telecheck completed; clinician updated plan (diuretic → 2 pm).")
        appointment_done = True

    return {"profile": p, "symptoms": symptoms, "appointment_done": appointment_done,
            "completed_actions": done, "proposed_actions": [], "transcript": out, "audit": audit}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def route_after_reason(state: AshaState) -> Literal["govern", "sense", "__end__"]:
    if state["proposed_actions"]:
        return "govern"
    return "sense" if state["day"] < max(SIMULATED_FEED) else END


def route_after_act(state: AshaState) -> Literal["reason", "sense", "__end__"]:
    if "follow_up" in state["completed_actions"]:
        return END
    if state["symptoms"] and "check_symptoms" in state["completed_actions"][-1:]:
        return "reason"          # re-evaluate right after check-in
    if state["appointment_done"]:
        return "reason"          # plan follow-up
    return "sense" if state["day"] < max(SIMULATED_FEED) else END


def build_graph():
    g = StateGraph(AshaState)
    g.add_node("sense", sense_agent)
    g.add_node("reason", reason_agent)
    g.add_node("govern", govern_agent)
    g.add_node("act", act_agent)
    g.add_edge(START, "sense")
    g.add_edge("sense", "reason")
    g.add_conditional_edges("reason", route_after_reason)
    g.add_edge("govern", "act")
    g.add_conditional_edges("act", route_after_act)
    return g.compile(checkpointer=MemorySaver())


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def initial_state() -> AshaState:
    return {
        "profile": {
            "patient_id": "rao-74",
            "name": "Mr. Venkat Rao", "age": 74,
            "history": ["HFrEF (NYHA II)", "Hypertension", "HF admission in March"],
            "medications": ["Furosemide 40 mg AM", "Sacubitril/valsartan 49/51 mg BID", "Bisoprolol 5 mg"],
            "allergies": ["Penicillin"],
            "care_plan": "Daily weights; call if +2 kg in 3 days",
            "baseline": {"steps": 4200, "rhr": 68, "weight": 71.2, "sleep": 7.1},
            "caregivers": {"priya": {"name": "Priya Rao", "relation": "daughter", "channel": "sms"}},
            "communication_prefs": "Voice, Telugu/English, mornings, no calls after 8 pm",
            "intervention_history": [],
            "consent_scope": {"priya": "tok_priya_care_updates_2026"},
            "open_tasks": [],
        },
        "day": 0, "readings": [], "symptoms": {}, "risk": 0.0, "risk_label": "low",
        "explanation": None, "proposed_actions": [], "completed_actions": [],
        "appointment_done": False, "audit": [], "transcript": [],
    }


def main():
    auto = "--auto" in sys.argv
    graph = build_graph()
    config = {"configurable": {"thread_id": "rao-74"}, "recursion_limit": 50}
    printed = 0

    def flush():
        nonlocal printed
        st = graph.get_state(config).values
        for line in st.get("transcript", [])[printed:]:
            print(line)
        printed = len(st.get("transcript", []))

    result = graph.invoke(initial_state(), config)
    while "__interrupt__" in result:
        flush()
        req = result["__interrupt__"][0].value
        print("\n⏸  APPROVAL REQUIRED")
        print("   Action:   ", req["action"])
        print("   Rationale:", req["rationale"])
        print("   Evidence: ", ", ".join(req["evidence"]))
        if auto:
            decision = {"decision": "approved", "note": "Agree, book 11:30 telecheck."}
        else:
            ans = input("   Approve? [y/n]: ").strip().lower()
            note = input("   Note (optional): ").strip()
            decision = {"decision": "approved" if ans == "y" else "rejected", "note": note}
        print()
        result = graph.invoke(Command(resume=decision), config)
    flush()

    final = graph.get_state(config).values
    print("\n===== AUDIT LOG =====")
    for e in final["audit"]:
        print(f"{e['ts']}  {e['actor']:<12} {e['action']:<22} {e['approval_status']:<9} {e['rationale'][:70]}")
    print("\n===== LAST EXPLANATION =====")
    print(json.dumps(final["explanation"], indent=2))
    print("\n===== UPDATED MEMORY =====")
    print("Care plan:", final["profile"]["care_plan"])
    print("History:  ", final["profile"]["intervention_history"])


if __name__ == "__main__":
    main()