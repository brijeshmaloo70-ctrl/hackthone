"""
nlp/language_handler.py
Multilingual support for Hindi and English.
Provides greetings, check-in messages, medication reminders,
and family alerts in both languages — with genuine Devanagari Hindi.
"""

from __future__ import annotations
import random
from typing import Dict, List


class LanguageHandler:
    """
    Handles multilingual message generation.
    All Hindi messages include genuine Devanagari script.
    """

    # ─── Greetings ─────────────────────────────────────────────────────────

    GREETINGS: Dict[str, Dict[str, List[str]]] = {
        "Hindi": {
            "morning": [
                "नमस्ते राजी! सुप्रभात। 🌅",
                "राम राम जी! सुबह बहुत अच्छी हो। 🙏",
                "प्रणाम जी! आज का दिन मंगलमय हो। ☀️",
            ],
            "afternoon": [
                "नमस्ते! दोपहर में कैसे हैं आप? 🌞",
                "राम राम जी! दोपहर की जाँच के लिए आई हूँ। 🙏",
                "प्रणाम जी! दोपहर में कुशल हैं? 💙",
            ],
            "evening": [
                "नमस्ते जी! शाम को कैसा महसूस हो रहा है? 🌆",
                "प्रणाम! शाम की दवाई याद है ना? 💊",
                "राम राम जी! शाम ढल रही है — आराम से हैं? 🌙",
            ],
        },
        "English": {
            "morning": [
                "Good morning! Hope you slept well. 🌅",
                "Rise and shine! How are you feeling this morning? ☀️",
                "Good morning! Time for your morning health check. 💙",
            ],
            "afternoon": [
                "Good afternoon! Just checking in on you. 🌞",
                "Hello! How has your day been so far? 💙",
                "Afternoon check-in — hope you're feeling good! 🌼",
            ],
            "evening": [
                "Good evening! Don't forget your evening medicines. 🌆",
                "Evening check-in — how are you feeling? 🌙",
                "Good evening! Time to wind down. How was your day? 💙",
            ],
        },
    }

    # ─── Check-in Messages ─────────────────────────────────────────────────

    CHECKIN_MESSAGES: Dict[str, List[str]] = {
        "Hindi": [
            "रमेश जी, आज आपका बीपी और शुगर चेक किया क्या? "
            "मुझे बताइए — सब कैसा है आज?\n"
            "(Ramesh ji, did you check your BP and sugar today? Tell me — how is everything?)",

            "नमस्ते रमेश जी! 🙏 आज की दवाई ली? "
            "अपनी तबीयत के बारे में बताइए।\n"
            "(Hello Ramesh ji! Did you take today's medicine? Tell me about your health.)",

            "रमेश जी, आशा यहाँ से बात कर रही हूँ। 💙 "
            "आज कैसा महसूस हो रहा है? कोई तकलीफ तो नहीं?\n"
            "(Ramesh ji, Asha here. How are you feeling today? Any discomfort?)",
        ],
        "English": [
            "Ramesh ji, this is Asha checking in. How are you feeling today? "
            "Have you taken your morning medicines?",
            "Hello Ramesh ji! Just a quick health check — how is your BP and sugar today?",
            "Good day, Ramesh ji! Asha here for your daily check-in. All okay?",
        ],
    }

    # ─── Medication Reminders ──────────────────────────────────────────────

    MEDICATION_REMINDERS: Dict[str, List[str]] = {
        "Hindi": [
            "⚠️ {medication} लेना न भूलें! यह दवाई आपके बीपी के लिए बहुत ज़रूरी है।\n"
            "(Don't forget to take {medication}! This medicine is very important for your BP.)",

            "💊 रमेश जी, {medication} की दवाई का समय हो गया है। "
            "कृपया अभी ले लीजिए।\n"
            "(Ramesh ji, it's time for {medication}. Please take it now.)",

            "🔔 दवाई याद दिला रही हूँ — {medication} ज़रूर लें। "
            "डॉक्टर की सलाह है।\n"
            "(Reminding you about medicine — do take {medication}. Doctor's advice.)",
        ],
        "English": [
            "💊 Reminder: Please take your {medication} now. It's very important for your health.",
            "⏰ Medicine time! Don't forget {medication}.",
            "🔔 Health reminder: {medication} is due. Please take it with water.",
        ],
    }

    # ─── Family Alert Messages ─────────────────────────────────────────────

    FAMILY_ALERTS: Dict[str, Dict[str, List[str]]] = {
        "English": {
            "isolation": [
                "👴 Dear {caregiver_name}, we've noticed that {patient_name} hasn't had any "
                "social interactions recently. He may be feeling lonely. "
                "Please give him a call or plan a visit soon. 💙",

                "🔔 Health Update: {patient_name} has been spending more time alone lately. "
                "Social connection is important for his wellbeing. "
                "Please check in with him today.",
            ],
            "medication": [
                "💊 Alert: {patient_name} has been missing medications. "
                "Please remind him to take his medicines regularly. "
                "Missing BP medication can lead to serious complications.",

                "⚠️ Medicine Alert: Our system detected that {patient_name} missed his "
                "prescribed medications. Please ensure he takes them at the right time.",
            ],
            "vitals": [
                "🩺 Medical Alert: {patient_name}'s vital signs need attention. "
                "His blood pressure and/or sugar levels have been elevated. "
                "Please consult with the doctor soon.",

                "⚠️ Health Warning: We're monitoring concerning trends in {patient_name}'s "
                "vitals. Please schedule a medical review.",
            ],
            "critical": [
                "🆘 URGENT: {patient_name}'s health metrics are in the danger zone. "
                "Please contact him immediately and consider emergency medical assistance "
                "if he is unresponsive or in distress.",
            ],
        },
        "Hindi": {
            "isolation": [
                "🙏 {caregiver_name} जी, {patient_name} कई दिनों से अकेले हैं। "
                "कृपया उनसे बात करें या मिलने जाएं। वे आपकी याद कर रहे हैं।\n"
                "(They are missing you — please call or visit.)",

                "💙 नमस्ते! {patient_name} हाल के दिनों में सामाजिक रूप से अलग-थलग लग रहे हैं। "
                "उन्हें आपके साथ की जरूरत है।",
            ],
            "medication": [
                "💊 ध्यान दें: {patient_name} दवाई लेना भूल रहे हैं। "
                "कृपया उन्हें समय पर दवाई दिलाएं।",
            ],
            "critical": [
                "🆘 आपातकाल! {patient_name} की तबीयत बहुत खराब है। "
                "तुरंत उनसे संपर्क करें और डॉक्टर को बुलाएं!\n"
                "(EMERGENCY! Please contact them immediately and call a doctor!)",
            ],
        },
    }

    # ─── Symptom Response Templates ────────────────────────────────────────

    SYMPTOM_RESPONSES: Dict[str, Dict[str, str]] = {
        "Hindi": {
            "chest pain": (
                "⚠️ रमेश जी, सीने में दर्द गंभीर बात है! "
                "कृपया अभी बैठ जाइए और सुरेश को फोन करें। "
                "अगर दर्द बढ़े तो 108 पर कॉल करें!\n"
                "(IMPORTANT: Chest pain is serious! Please sit down and call Suresh. "
                "If pain increases, call 108!)"
            ),
            "dizziness": (
                "चक्कर आ रहे हैं? कृपया बैठ जाइए और पानी पिएं। "
                "BP चेक करें — अगर बहुत ज्यादा हो तो मुझे बताएं।\n"
                "(Feeling dizzy? Please sit down and drink water. Check BP.)"
            ),
            "headache": (
                "सिरदर्द हो रहा है? ज्यादा बीपी की वजह से भी हो सकता है। "
                "BP चेक करें और आराम करें।\n"
                "(Headache? It could be due to high BP. Please check your BP and rest.)"
            ),
            "breathlessness": (
                "⚠️ सांस लेने में तकलीफ? यह गंभीर हो सकता है। "
                "सीधे बैठें और सुरेश को अभी फोन करें!\n"
                "(Difficulty breathing? This can be serious. Sit upright and call Suresh now!)"
            ),
        },
        "English": {
            "chest pain": (
                "⚠️ Ramesh ji, chest pain is serious! Please sit down immediately "
                "and call Suresh. If pain worsens, call emergency services (108)!"
            ),
            "dizziness": (
                "Feeling dizzy? Please sit or lie down. Check your BP — "
                "if it's very high, please let me know immediately."
            ),
            "headache": (
                "A headache can sometimes indicate high blood pressure. "
                "Please check your BP and rest. Let me know if it gets worse."
            ),
            "breathlessness": (
                "⚠️ Difficulty breathing is a serious symptom. "
                "Sit upright and call Suresh immediately. If severe, call 108!"
            ),
        },
    }

    # ─── Public Methods ────────────────────────────────────────────────────

    def get_greeting(self, language: str, time_of_day: str) -> str:
        """Return a random contextual greeting in the specified language."""
        lang = self._normalize_language(language)
        time_key = time_of_day.lower()
        if time_key not in ("morning", "afternoon", "evening"):
            time_key = "morning"
        options = self.GREETINGS.get(lang, self.GREETINGS["English"]).get(
            time_key, ["Hello!"]
        )
        return random.choice(options)

    def get_checkin_message(self, language: str, patient_name: str) -> str:
        """Return a personalised check-in message."""
        lang = self._normalize_language(language)
        options = self.CHECKIN_MESSAGES.get(lang, self.CHECKIN_MESSAGES["English"])
        return random.choice(options).format(patient_name=patient_name)

    def get_medication_reminder(self, language: str, medication: str) -> str:
        """Return a medication reminder message."""
        lang = self._normalize_language(language)
        options = self.MEDICATION_REMINDERS.get(lang, self.MEDICATION_REMINDERS["English"])
        return random.choice(options).format(medication=medication)

    def get_family_alert(
        self,
        language: str,
        severity: str,
        patient_name: str,
        caregiver_name: str = "Suresh Kumar",
    ) -> str:
        """Return a family alert message."""
        lang = self._normalize_language(language)
        alerts_by_lang = self.FAMILY_ALERTS.get(lang, self.FAMILY_ALERTS["English"])
        options = alerts_by_lang.get(severity, alerts_by_lang.get("vitals", ["Health alert!"]))
        template = random.choice(options)
        return template.format(
            patient_name=patient_name,
            caregiver_name=caregiver_name,
        )

    def get_symptom_response(self, language: str, symptom: str) -> str:
        """Return a symptom-specific response."""
        lang = self._normalize_language(language)
        responses = self.SYMPTOM_RESPONSES.get(lang, self.SYMPTOM_RESPONSES["English"])
        symptom_lower = symptom.lower()
        for key, response in responses.items():
            if key in symptom_lower:
                return response
        return (
            f"कृपया डॉक्टर से बात करें। / Please consult your doctor about {symptom}."
        )

    def get_isolation_nudge(self, language: str, days_isolated: int) -> str:
        """Return a gentle nudge to re-engage socially."""
        if language.lower() == "hindi":
            return (
                f"रमेश जी, आप {days_isolated} दिनों से अकेले हैं। 😔 "
                f"क्या आप आज सुरेश को फोन कर सकते हैं? "
                f"अपने पुराने दोस्तों से भी बात करें — "
                f"अकेलापन स्वास्थ्य के लिए अच्छा नहीं है। 💙\n"
                f"(Ramesh ji, you've been alone for {days_isolated} days. "
                f"Can you call Suresh today? Social connection is good for your health.)"
            )
        return (
            f"Ramesh ji, you've been quite alone for {days_isolated} days. 💙 "
            f"Would you like to call Suresh or a friend today? "
            f"Social connection is very important for your health and happiness."
        )

    def get_wellbeing_check(self, language: str) -> str:
        """Return a social wellbeing check question."""
        if language.lower() == "hindi":
            return (
                "रमेश जी, आज किससे बात हुई? "
                "सुरेश से या किसी दोस्त से मिले? "
                "आज कुछ अच्छा हुआ जो मुझे बताना चाहें? 😊\n"
                "(Ramesh ji, who did you talk to today? "
                "Did you meet Suresh or any friends? Anything good happen today?)"
            )
        return (
            "Ramesh ji, who did you chat with today? "
            "Did you meet or speak with anyone — family, friends, or neighbours? "
            "Staying connected is very good for your health! 😊"
        )

    # ─── Helpers ───────────────────────────────────────────────────────────

    def _normalize_language(self, language: str) -> str:
        """Normalise language string to a known key."""
        lang_lower = language.lower().strip()
        if lang_lower in ("hindi", "हिन्दी", "hi"):
            return "Hindi"
        return "English"
