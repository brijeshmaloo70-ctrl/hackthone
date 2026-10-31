"""
nlp/language_handler.py
Multilingual support for Hindi, Marathi, and English.
Provides greetings, check-in messages, medication reminders,
family alerts, and symptom guidance in all three languages.
"""

from __future__ import annotations
import random
from typing import Dict, List


class LanguageHandler:
    """
    Handles multilingual message generation across Hindi, Marathi, and English.
    All Indic messages use genuine Devanagari script.
    """

    # ─── Greetings ─────────────────────────────────────────────────────────

    GREETINGS: Dict[str, Dict[str, List[str]]] = {
        "Hindi": {
            "morning": [
                "नमस्ते जी! सुप्रभात। 🌅",
                "राम राम जी! सुबह बहुत अच्छी हो। 🙏",
                "प्रणाम जी! आज का दिन मंगलमय हो। ☀️",
            ],
            "afternoon": [
                "नमस्ते! दोपहर में कैसे हैं आप? 🌞",
                "राम राम जी! दोपहर की जाँच के लिए आई हूँ। 🙏",
                "प्रणाम जी! दोपहर में सब ठीक है? 💙",
            ],
            "evening": [
                "नमस्ते जी! शाम को कैसा महसूस हो रहा है? 🌆",
                "प्रणाम! शाम की दवाई याद है ना? 💊",
                "राम राम जी! शाम ढल रही है — आराम से हैं? 🌙",
            ],
        },
        "Marathi": {
            "morning": [
                "नमस्कार! शुभ सकाळ। 🌅",
                "राम राम! आजची सकाळ छान जावो। 🙏",
                "प्रणाम! आजचा दिवस आनंदाचा जावो। ☀️",
            ],
            "afternoon": [
                "नमस्कार! दुपार कशी चालली आहे? 🌞",
                "प्रणाम! दुपारच्या आरोग्याची विचारपूस करण्यासाठी आले आहे। 💙",
                "दुपारचे जेवण झाले का? विश्रांती घेत आहात ना? 🌼",
            ],
            "evening": [
                "नमस्कार! शुभ संध्याकाळ। संध्याकाळी कसे वाटत आहे? 🌆",
                "संध्याकाळच्या औषधांची आठवण आहे ना? 💊",
                "दिवसभरात काही त्रास झाला नाही ना? 🌙",
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
            "रमेश जी, आज आपका बीपी और शुगर चेक किया क्या? मुझे बताइए — सब कैसा है आज?\n(Ramesh ji, did you check your BP and sugar today? Tell me — how is everything?)",
            "नमस्ते रमेश जी! 🙏 आज की दवाई ली? अपनी तबीयत के बारे में बताइए।\n(Hello Ramesh ji! Did you take today's medicine? Tell me about your health.)",
            "रमेश जी, आशा यहाँ से बात कर रही हूँ। 💙 आज कैसा महसूस हो रहा है? कोई तकलीफ तो नहीं?\n(Ramesh ji, Asha here. How are you feeling today? Any discomfort?)",
        ],
        "Marathi": [
            "रमेश जी, आज तुमचा बीपी आणि साखर तपासली का? आज प्रकृती कशी आहे सांगा?\n(Ramesh ji, did you check your BP and sugar today? How is your health?)",
            "नमस्कार रमेश जी! 🙏 आजची औषधे वेळेवर घेतली का? कसे वाटत आहे?\n(Hello Ramesh ji! Did you take today's medicines on time? How are you feeling?)",
            "रमेश जी, आशा बोलतेय। 💙 आज काही त्रास किंवा अस्वस्थता जाणवत आहे का?\n(Ramesh ji, Asha speaking. Are you feeling any discomfort today?)",
        ],
        "English": [
            "Ramesh ji, this is Asha checking in. How are you feeling today? Have you taken your morning medicines?",
            "Hello Ramesh ji! Just a quick health check — how is your BP and sugar today?",
            "Good day, Ramesh ji! Asha here for your daily check-in. All okay?",
        ],
    }

    # ─── Medication Reminders ──────────────────────────────────────────────

    MEDICATION_REMINDERS: Dict[str, List[str]] = {
        "Hindi": [
            "⚠️ {medication} लेना न भूलें! यह दवाई आपके बीपी के लिए बहुत ज़रूरी है।\n(Don't forget to take {medication}! This medicine is very important for your BP.)",
            "💊 रमेश जी, {medication} की दवाई का समय हो गया है। कृपया अभी ले लीजिए।\n(Ramesh ji, it's time for {medication}. Please take it now.)",
            "🔔 दवाई याद दिला रही हूँ — {medication} ज़रूर लें। डॉक्टर की सलाह है।\n(Reminding you about medicine — do take {medication}. Doctor's advice.)",
        ],
        "Marathi": [
            "⚠️ {medication} औषध घेणे विसरू नका! हे तुमच्या रक्तदाबासाठी अत्यंत महत्त्वाचे आहे।\n(Don't forget {medication}! Very important for your blood pressure.)",
            "💊 रमेश जी, {medication} औषधाची वेळ झाली आहे। कृपया आताच घ्या।\n(Ramesh ji, it's time for {medication}. Please take it now.)",
            "🔔 औषधाची आठवण — {medication} वेळेवर घ्या, डॉक्टरांचा सल्ला आहे।\n(Medication reminder — please take {medication} on time.)",
        ],
        "English": [
            "💊 Reminder: Please take your {medication} now. It's very important for your health.",
            "⏰ Medicine time! Don't forget {medication}.",
            "🔔 Health reminder: {medication} is due. Please take it with water.",
        ],
    }

    # ─── Family Alert Messages ─────────────────────────────────────────────

    FAMILY_ALERTS: Dict[str, Dict[str, List[str]]] = {
        "Hindi": {
            "isolation": [
                "🙏 {caregiver_name} जी, {patient_name} कई दिनों से अकेले हैं। कृपया उनसे बात करें या मिलने जाएं। वे आपकी याद कर रहे हैं।",
                "💙 नमस्ते! {patient_name} हाल के दिनों में सामाजिक रूप से अलग-थलग लग रहे हैं। उन्हें आपके साथ की जरूरत है।",
            ],
            "medication": [
                "💊 ध्यान दें: {patient_name} दवाई लेना भूल रहे हैं। कृपया उन्हें समय पर दवाई दिलाएं।",
            ],
            "vitals": [
                "🩺 मेडिकल अलर्ट: {patient_name} का बीपी या शुगर बढ़ा हुआ है। कृपया डॉक्टर से सलाह लें।",
            ],
            "critical": [
                "🆘 आपातकाल! {patient_name} की तबीयत बहुत खराब है। तुरंत उनसे संपर्क करें और डॉक्टर को बुलाएं!",
            ],
        },
        "Marathi": {
            "isolation": [
                "🙏 {caregiver_name} जी, {patient_name} बरेच दिवस एकटे आहेत। कृपया त्यांना फोन करा किंवा भेटायला या।",
                "💙 नमस्कार! {patient_name} आजकाल एकटेपणा जाणवत असल्याचे दिसत आहे। त्यांना तुमच्या संवादाची गरज आहे।",
            ],
            "medication": [
                "💊 लक्ष द्या: {patient_name} औषधे वेळेवर घेत नाहीत। कृपया त्यांच्या औषधांकडे लक्ष द्या।",
            ],
            "vitals": [
                "🩺 वैद्यकीय इशारा: {patient_name} यांचा रक्तदाब किंवा साखर वाढली आहे। त्वरित डॉक्टरांशी चर्चा करा।",
            ],
            "critical": [
                "🆘 तातडीची सूचना! {patient_name} यांची प्रकृती गंभीर आहे। तात्काळ संपर्क करा आणि वैद्यकीय मदत मिळवा!",
            ],
        },
        "English": {
            "isolation": [
                "👴 Dear {caregiver_name}, we've noticed that {patient_name} hasn't had any social interactions recently. He may be feeling lonely. Please give him a call or plan a visit soon. 💙",
                "🔔 Health Update: {patient_name} has been spending more time alone lately. Social connection is important for his wellbeing. Please check in with him today.",
            ],
            "medication": [
                "💊 Alert: {patient_name} has been missing medications. Please remind him to take his medicines regularly. Missing BP medication can lead to serious complications.",
            ],
            "vitals": [
                "🩺 Medical Alert: {patient_name}'s vital signs need attention. His blood pressure and/or sugar levels have been elevated. Please consult with the doctor soon.",
            ],
            "critical": [
                "🆘 URGENT: {patient_name}'s health metrics are in the danger zone. Please contact him immediately and consider emergency medical assistance.",
            ],
        },
    }

    # ─── Symptom Response Templates ────────────────────────────────────────

    SYMPTOM_RESPONSES: Dict[str, Dict[str, str]] = {
        "Hindi": {
            "chest pain": (
                "⚠️ रमेश जी, सीने में दर्द गंभीर बात है! कृपया अभी बैठ जाइए और सुरेश को फोन करें। अगर दर्द बढ़े तो तुरंत 108 पर कॉल करें!"
            ),
            "dizziness": (
                "चक्कर आ रहे हैं? कृपया बैठ जाइए और पानी पिएं। BP चेक करें — अगर बहुत ज्यादा हो तो मुझे बताएं।"
            ),
            "headache": (
                "सिरदर्द हो रहा है? ज्यादा बीपी की वजह से भी हो सकता है। BP चेक करें और आराम करें।"
            ),
            "breathlessness": (
                "⚠️ सांस लेने में तकलीफ? यह गंभीर हो सकता है। सीधे बैठें और सुरेश को अभी फोन करें!"
            ),
        },
        "Marathi": {
            "chest pain": (
                "⚠️ रमेश जी, छातीत दुखणे गंभीर लक्षण आहे! कृपया त्वरित बसा आणि सुरेश यांना फोन करा। वेदना वाढल्यास 108 वर कॉल करा!"
            ),
            "dizziness": (
                "चक्कर येत आहे का? कृपया शांत बसा आणि थोडे पाणी प्या। रक्तदाब तपासा आणि मला कळवा।"
            ),
            "headache": (
                "डोके दुखत आहे का? वाढलेल्या रक्तदाबामुळे असू शकते। रक्तदाब तपासा आणि विश्रांती घ्या।"
            ),
            "breathlessness": (
                "⚠️ श्वास घेण्यास त्रास? हे गंभीर असू शकते। सरळ बसा आणि तातडीने सुरेश यांना संपर्क करा!"
            ),
        },
        "English": {
            "chest pain": (
                "⚠️ Ramesh ji, chest pain is serious! Please sit down immediately and call Suresh. If pain worsens, call emergency services (108)!"
            ),
            "dizziness": (
                "Feeling dizzy? Please sit or lie down. Check your BP — if it's very high, please let me know immediately."
            ),
            "headache": (
                "A headache can sometimes indicate high blood pressure. Please check your BP and rest. Let me know if it gets worse."
            ),
            "breathlessness": (
                "⚠️ Difficulty breathing is a serious symptom. Sit upright and call Suresh immediately. If severe, call 108!"
            ),
        },
    }

    # ─── Public Methods ────────────────────────────────────────────────────

    def get_greeting(self, language: str, time_of_day: str) -> str:
        lang = self._normalize_language(language)
        time_key = time_of_day.lower()
        if time_key not in ("morning", "afternoon", "evening"):
            time_key = "morning"
        options = self.GREETINGS.get(lang, self.GREETINGS["English"]).get(time_key, ["Hello!"])
        return random.choice(options)

    def get_checkin_message(self, language: str, patient_name: str) -> str:
        lang = self._normalize_language(language)
        options = self.CHECKIN_MESSAGES.get(lang, self.CHECKIN_MESSAGES["English"])
        return random.choice(options).format(patient_name=patient_name)

    def get_medication_reminder(self, language: str, medication: str) -> str:
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
        lang = self._normalize_language(language)
        alerts_by_lang = self.FAMILY_ALERTS.get(lang, self.FAMILY_ALERTS["English"])
        options = alerts_by_lang.get(severity, alerts_by_lang.get("vitals", ["Health alert!"]))
        template = random.choice(options)
        return template.format(patient_name=patient_name, caregiver_name=caregiver_name)

    def get_symptom_response(self, language: str, symptom: str) -> str:
        lang = self._normalize_language(language)
        responses = self.SYMPTOM_RESPONSES.get(lang, self.SYMPTOM_RESPONSES["English"])
        symptom_lower = symptom.lower()
        for key, response in responses.items():
            if key in symptom_lower:
                return response
        if lang == "Marathi":
            return f"कृपया या लक्षणाबद्दल डॉक्टरांशी संपर्क साधा ({symptom})।"
        elif lang == "Hindi":
            return f"कृपया डॉक्टर से बात करें ({symptom})।"
        return f"Please consult your doctor about {symptom}."

    def get_isolation_nudge(self, language: str, days_isolated: int) -> str:
        lang = self._normalize_language(language)
        if lang == "Marathi":
            return (
                f"रमेश जी, तुम्ही {days_isolated} दिवसांपासून कोणाशीही बोलला नाही आहात। 💙 "
                f"आज सुरेश यांना फोन करा किंवा मित्रांशी बोला। सामाजिक संवाद आरोग्यासाठी अत्यंत गरजेचा आहे।"
            )
        elif lang == "Hindi":
            return (
                f"रमेश जी, आप {days_isolated} दिनों से अकेले हैं। 💙 "
                f"क्या आप आज सुरेश को फोन कर सकते हैं? अकेलापन स्वास्थ्य के लिए ठीक नहीं है।"
            )
        return (
            f"Ramesh ji, you've been quite alone for {days_isolated} days. 💙 "
            f"Would you like to call Suresh or a friend today? Social connection is vital for healthy ageing!"
        )

    def get_wellbeing_check(self, language: str) -> str:
        lang = self._normalize_language(language)
        if lang == "Marathi":
            return (
                "रमेश जी, आज कोणाशी गप्पा झाल्या का? सुरेश यांच्याशी किंवा मित्रांशी भेट झाली का? "
                "आजचा दिवस कसा वाटला? 😊"
            )
        elif lang == "Hindi":
            return (
                "रमेश जी, आज किससे बात हुई? सुरेश से या किसी दोस्त से मिले? आज कुछ अच्छा हुआ? 😊"
            )
        return (
            "Ramesh ji, who did you chat with today? Did you meet or speak with family or friends? "
            "Staying connected is wonderful for your health! 😊"
        )

    # ─── Helpers ───────────────────────────────────────────────────────────

    def _normalize_language(self, language: str) -> str:
        lang_lower = (language or "").lower().strip()
        if lang_lower in ("hindi", "हिन्दी", "hi"):
            return "Hindi"
        if lang_lower in ("marathi", "मराठी", "mr"):
            return "Marathi"
        return "English"
