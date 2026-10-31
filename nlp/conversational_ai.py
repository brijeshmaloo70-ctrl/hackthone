"""
nlp/conversational_ai.py
Intelligent Conversational AI engine for Asha (Patient Agent).
Provides rich, context-aware, empathetic, and clinical triage responses
across English, Hindi (हिन्दी), and Marathi (मराठी) without requiring external network.
Integrates gracefully with Gemini LLM when API key is present.
"""

import re
from typing import Dict, Any, Optional

class AshaConversationalEngine:
    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client

    def reply(self, user_message: str, lang: str = "hi", day: int = 30, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        msg_raw = user_message.strip()
        msg_lower = msg_raw.lower()
        context = context or {}

        # 1. Normalize language code
        raw_lang = (lang or "hi").strip().lower()
        if raw_lang in ["en", "english", "en-us", "en-in", "en-gb"]:
            lang = "en"
        elif raw_lang in ["mr", "marathi", "mr-in"]:
            lang = "mr"
        else:
            lang = "hi"

        # 2. Risk & Emergency Level Detection
        alert_level = 0
        caregiver_alert = ""

        # Emergency keywords (Chest pain, heart attack, breathlessness, collapse)
        emergency_patterns = [
            r"chest pain", r"सीने में दर्द", r"छातीत दुख", r"छाती दुखन", r"heart", r"दिल में दर्द",
            r"breathless", r"सांस नहीं आ रही", r"श्वास", r"दम घुट", r"चोक", r"attack", r"बेहोश", r"unconscious"
        ]
        if any(re.search(p, msg_lower) for p in emergency_patterns):
            alert_level = 3
            caregiver_alert = "🚨 EMERGENCY: Ramesh Kumar reported acute chest discomfort/breathlessness."

        # High/Moderate Concern (Dizziness, severe headache, sudden nausea)
        elif any(k in msg_lower for k in [
            "चक्कर", "dizzy", "dizziness", "सिरदर्द", "headache", "डोकेदुखी", "उल्टी", "vomit", "vomiting", "nausea"
        ]):
            alert_level = 2
            caregiver_alert = "⚠️ Priority Concern: Ramesh reported dizziness or severe headache."

        # Medication adherence questions
        elif any(k in msg_lower for k in [
            "दवाई", "medicine", "tablet", "भूल", "missed", "औषध", "गोली", "pill", "डोज़", "dose"
        ]):
            alert_level = 1
            caregiver_alert = "💊 Medication notification sent to Suresh Kumar."

        # 3. If Gemini is available, attempt dynamic generation
        if self.gemini_client:
            try:
                lang_name = {"hi": "Hindi (Devanagari script)", "mr": "Marathi (मराठी script)", "en": "warm English"}.get(lang, "Hindi")
                prompt = f"""You are Asha, a loving, respectful, and clinically wise AI healthcare companion for Ramesh Kumar (78M, has Hypertension and Type 2 Diabetes).
Patient language: {lang_name}.
Current Day: Day {day} of 30.
Vitals context: BP normally ~145/88, taking Amlodipine 5mg and Metformin 500mg.
User message: "{msg_raw}"

Instructions:
1. Address the patient with utmost Indian cultural warmth and respect (रमेश जी / Ramesh-ji).
2. Directly answer their query with compassionate, accurate eldercare guidance in {lang_name}.
3. If they complain of chest pain, dizziness, or weakness, give immediate practical safety instructions (sit down, loosen clothes, sip water) and mention that their son Suresh and Dr. Anjali Sharma are alerted.
4. Keep the reply friendly, actionable, and under 80 words.
"""
                res = self.gemini_client.generate_content(prompt)
                if res and res.text:
                    return {
                        "reply": res.text.strip(),
                        "alert_level": alert_level,
                        "caregiver_alert": caregiver_alert,
                        "llm_used": True
                    }
            except Exception:
                pass

        # 4. Comprehensive Deterministic & Semantic Response Engine
        return {
            "reply": self._synthesize_response(msg_lower, lang, alert_level, context),
            "alert_level": alert_level,
            "caregiver_alert": caregiver_alert,
            "llm_used": False
        }

    def _synthesize_response(self, q: str, lang: str, alert_level: int, ctx: Dict[str, Any]) -> str:
        # Category A: Emergency Level 3 (Chest Pain, Breathlessness)
        if alert_level == 3:
            if lang == "mr":
                return (
                    "⚠️ **रमेश जी, छातीत दुखणे किंवा अस्वस्थता अजिबात दुर्लक्षित करू नका!**<br/>"
                    "कृपया लगेच एका जागी शांत बसा, कपडे सैल करा आणि हळूहळू दीर्घ श्वास घ्या. "
                    "मी तात्काळ आपले सुपुत्र सुरेश यांना आणि डॉ. अंजली शर्मा यांना अलर्ट पाठवला आहे. "
                    "त्रास जास्त वाटल्यास वरील **लाल आपत्कालीन १०८ बटण** दाबा."
                )
            elif lang == "en":
                return (
                    "⚠️ **Ramesh-ji, please do not ignore chest pain or breathlessness!**<br/>"
                    "Please sit down immediately, loosen your clothes, and take slow, deep breaths. "
                    "I have sent an urgent emergency alert to your son Suresh and notified Dr. Anjali Sharma. "
                    "Please tap the **Emergency 108 Call button** above right away if distress continues."
                )
            else:
                return (
                    "⚠️ **रमेश जी, सीने में दर्द या भारीपन को बिल्कुल नज़रअंदाज़ न करें!**<br/>"
                    "कृपया तुरंत आराम से बैठ जाइए, ढीले कपड़े पहनें और धीरे-धीरे गहरी सांस लें। "
                    "मैंने आपके बेटे सुरेश को आपातकालीन अलर्ट भेज दिया है और डॉक्टर अंजलि को सूचित कर दिया है। "
                    "कृपया तुरंत ऊपर दिए गए **लाल 108 आपातकालीन बटन** पर कॉल करें।"
                )

        # Category B: Level 2 (Dizziness, Headache, BP Fluctuation)
        if alert_level == 2:
            if lang == "mr":
                return (
                    "रमेश जी, चक्कर येणे किंवा डोकेदुखी हे वाढलेल्या रक्तदाबाचे (High BP) लक्षण असू शकते. 🩺<br/>"
                    "कृपया लगेच विश्रांती घ्या, डोळे मिटून बसा आणि थोडे पाणी प्या. "
                    "आपण आजची सकाळची Amlodipine गोळी घेतली आहे का? मी सुरेश यांना आपल्याकडे लक्ष देण्यास सांगितले आहे."
                )
            elif lang == "en":
                return (
                    "Ramesh-ji, dizziness and headaches are key signs of fluctuating blood pressure. 🩺<br/>"
                    "Please sit or lie down comfortably, drink a glass of water, and rest your eyes. "
                    "Did you take your morning Amlodipine 5mg tablet today? I have notified Suresh to check on you."
                )
            else:
                return (
                    "रमेश जी, चक्कर आना या सिरदर्द हाई ब्लड प्रेशर का स्पष्ट संकेत हो सकता है। 🩺<br/>"
                    "कृपया तुरंत आराम से बैठ जाएं, थोड़ा गुनगुना पानी पिएं और आंखें बंद करके आराम करें। "
                    "क्या आपने आज सुबह की Amlodipine की गोली ली थी? मैंने सुरेश जी को आपके पास ध्यान देने का संदेश भेज दिया है।"
                )

        # Category C: Medications (Adherence, Missed pill, Timings)
        if alert_level == 1 or any(k in q for k in ["दवाई", "medicine", "tablet", "भूल", "गोली", "औषध"]):
            if lang == "mr":
                return (
                    "💊 **रमेश जी, आपली औषधे वेळेवर घेणे अत्यंत महत्त्वाचे आहे!**<br/>"
                    "• **Amlodipine 5mg** — सकाळी ८:०० वाजता (रक्तदाबासाठी)<br/>"
                    "• **Metformin 500mg** — सकाळच्या नाश्त्यानंतर (शुगरसाठी)<br/>"
                    "जर सकाळची गोळी राहिली असेल तर हलका नाश्ता करून आत्ताच एक ग्लास पाण्यासोबत घ्या."
                )
            elif lang == "en":
                return (
                    "💊 **Ramesh-ji, taking your prescribed medications on schedule is vital!**<br/>"
                    "• **Amlodipine 5mg** — Morning 8:00 AM (for Blood Pressure)<br/>"
                    "• **Metformin 500mg** — After breakfast (for Blood Sugar)<br/>"
                    "If you missed this morning's dose, please take it now with a glass of water and light food."
                )
            else:
                return (
                    "💊 **रमेश जी, आपकी दवाइयाँ समय पर लेना आपके स्वास्थ्य की पहली सुरक्षा है!**<br/>"
                    "• **Amlodipine 5mg** — सुबह 8:00 बजे (ब्लड प्रेशर के लिए)<br/>"
                    "• **Metformin 500mg** — सुबह नाश्ते के तुरंत बाद (शुगर के लिए)<br/>"
                    "अगर सुबह की गोली छूट गई है, तो कृपया अभी हल्का सा नाश्ता करके एक गिलास पानी के साथ ले लीजिए।"
                )

        # Category D: Greetings & Wellbeing Questions
        if any(k in q for k in ["hello", "hi", "hey", "नमस्ते", "नमस्कार", "सुप्रभात", "प्रणाम", "कहा", "kaisa", "how are you"]):
            if lang == "mr":
                return (
                    "नमस्कार रमेश जी! 🙏 सुप्रभात! मी आपली २४/७ आरोग्य साथी आशा आहे.<br/>"
                    "आज आपली प्रकृती कशी आहे? आजचा रक्तदाब आणि रक्तातील साखर तपासली का? मला जरूर सांगा!"
                )
            elif lang == "en":
                return (
                    "Good day, Ramesh-ji! 🙏 Warm greetings from Asha, your 24/7 AI health companion.<br/>"
                    "How are you feeling today? Did you check your blood pressure and morning glucose? I am here to help you."
                )
            else:
                return (
                    "नमस्ते रमेश जी! 🙏 सादर प्रणाम! मैं आपकी स्वास्थ्य साथी आशा हमेशा आपके साथ हूँ।<br/>"
                    "आज आप कैसा महसूस कर रहे हैं? क्या आपने आज सुबह का ब्लड प्रेशर और शुगर नापा है? मुझे बेझिझक बताएं!"
                )

        # Category E: Diet, Water & Routine Questions
        if any(k in q for k in ["पानी", "water", "खाना", "diet", "food", "भोजन", "आहार", "टहल", "walk", "वॉक"]):
            if lang == "mr":
                return (
                    "🥗 **रमेश जी, निरोगी दिनचर्येसाठी आजचे नियम:**<br/>"
                    "• दिवसातून किमान ७-८ ग्लास कोमट पाणी अवश्य प्या.<br/>"
                    "• भोजनात मीठ (सोडियम) आणि साखर अत्यंत कमी ठेवा.<br/>"
                    "• संध्याकाळी बागेत किंवा अंगणात १५-२० मिनिटे हलकी फेरफटका मारा."
                )
            elif lang == "en":
                return (
                    "🥗 **Ramesh-ji, healthy daily routine guidance:**<br/>"
                    "• Drink at least 7 to 8 glasses of warm water today to stay well hydrated.<br/>"
                    "• Keep sodium (salt) low to protect your heart, and avoid processed sugars.<br/>"
                    "• Aim for a gentle 15–20 minute walk in the garden or courtyard this evening."
                )
            else:
                return (
                    "🥗 **रमेश जी, आज के स्वस्थ आहार और दिनचर्या के सुझाव:**<br/>"
                    "• दिन भर में कम से कम 7 से 8 गिलास गुनगुना पानी ज़रूर पिएं।<br/>"
                    "• भोजन में नमक की मात्रा कम रखें ताकि बीपी नियंत्रित रहे, और तली-भुनी चीज़ों से बचें।<br/>"
                    "• शाम को 15 से 20 मिनट के लिए घर के आंगन या पार्क में हल्की सैर ज़रूर करें।"
                )

        # Category F: Loneliness, Depression & Emotional Support
        if any(k in q for k in ["अकेला", "lonely", "उदासी", "मन नहीं", "sad", "उदासीन", "करमत नाही", "talk", "बात"]):
            if lang == "mr":
                return (
                    "रमेश जी, मी नेहमी आपल्यासोबत आहे! 💙 एकटे वाटणे स्वाभाविक आहे, पण आपण कधीच एकटे नाही आहात.<br/>"
                    "मी सुरेश यांना आत्ताच व्हॉट्सॲपवर निरोप पाठवला आहे की त्यांनी आज संध्याकाळी आपल्याशी फोनवर मनमोकळे बोलावे!"
                )
            elif lang == "en":
                return (
                    "Ramesh-ji, I am always right here by your side! 💙 Feeling lonely is very natural, but you are cherished.<br/>"
                    "I have sent a gentle nudge to Suresh on WhatsApp so he can call and have a wonderful chat with you this evening!"
                )
            else:
                return (
                    "रमेश जी, मैं हमेशा आपके साथ हूँ! 💙 कभी-कभी अकेलापन या उदासी महसूस होना स्वाभाविक है, पर आप अकेले नहीं हैं।<br/>"
                    "मैंने सुरेश जी को व्हाट्सएप पर संदेश भेज दिया है कि वे आज शाम को आपको फोन करके लंबी बात करें। आप अपने मनपसंद पुराने गीत भी सुन सकते हैं!"
                )

        # Category G: Doctor & Appointment Questions
        if any(k in q for k in ["डॉक्टर", "doctor", "appointment", "clinic", "अस्पताल", "apollo", "anjali"]):
            if lang == "mr":
                return (
                    "🩺 **डॉक्टरांशी भेट (Next Consultation):**<br/>"
                    "डॉ. अंजली शर्मा (अपोलो हॉस्पिटल, नोएडा) यांच्यासोबत डे ३० रोजी आपली तपासणी नियोजित आहे. "
                    "गेल्या ३० दिवसांचा संपूर्ण ईएचआर आणि वाइटल्स अहवाल क्लिनिककडे तयार आहे."
                )
            elif lang == "en":
                return (
                    "🩺 **Doctor Consultation Details:**<br/>"
                    "Your follow-up with Dr. Anjali Sharma (Apollo Hospital, Noida) is scheduled for Day 30. "
                    "Your complete 30-day vitals trend, medication compliance, and health summary are prepared for her review."
                )
            else:
                return (
                    "🩺 **डॉक्टर परामर्श जानकारी:**<br/>"
                    "डॉ. अंजलि शर्मा (अपोलो हॉस्पिटल, नोएडा) के साथ आपका अगला चेकअप डे 30 को निर्धारित है। "
                    "आपके पिछले 30 दिनों का पूरा वाइटल्स रिकॉर्ड और हेल्थ रिपोर्ट मैंने डॉक्टर साहब के लिए तैयार कर दी है।"
                )

        # Default Helpful Contextual Catch-all
        if lang == "mr":
            return (
                f"नमस्कार रमेश जी! 🙏 मी आपली माहिती आरोग्य नोंदवहीत सुरक्षित केली आहे.<br/>"
                f"वेळेवर औषधे घ्या, पुरेसे पाणी प्या आणि कोणतीही शंका असल्यास मला निःसंकोचपणे विचारा!"
            )
        elif lang == "en":
            return (
                f"Hello Ramesh-ji! 🙏 I have carefully noted this in your daily care record.<br/>"
                f"Please stay hydrated, follow your routine, and let me know if you feel any fatigue, pain, or discomfort!"
            )
        else:
            return (
                f"नमस्ते रमेश जी! 🙏 मैंने आपकी बात को ध्यानपूर्वक समझकर आपके दैनिक हेल्थ रिकॉर्ड में दर्ज कर लिया है।<br/>"
                f"समय पर अपनी दवाइयाँ लेते रहें, पानी पीते रहें और कोई भी असुविधा या दर्द महसूस हो तो मुझे तुरंत बताएं!"
            )
