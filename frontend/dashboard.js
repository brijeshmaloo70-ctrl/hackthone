/* ============================================================
   CareSync AI — Patient Dashboard JavaScript
   Complete 30-Day Simulation Visualization, Chart.js Integration,
   Interactive Day Playback, Clinical Modals & Bilingual Chat
   ============================================================ */

// ── 30-Day Enriched Patient Timeline Data ─────────────────────
const TIMELINE_DATA = [{"day": 1, "date": "2024-11-01", "phase": "stable", "bp_systolic": 139, "bp_diastolic": 87, "heart_rate": 73, "blood_glucose": 185.5, "weight": 72.0, "sleep_hours": 6.3, "activity_minutes": 40, "mood": 5, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! सुप्रभात। 🙏 आशा यहाँ से बात कर रही हूँ। आज आपका बीपी और शुगर चेक किया क्या? दिन की शुरुआत कैसी रही?", "en": "Good morning Ramesh ji! Asha here for your daily check-in. Did you check your BP and sugar today? How are you feeling?"}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Baseline stable. BP and glucose within target thresholds. Level 0."}, {"day": 2, "date": "2024-11-02", "phase": "stable", "bp_systolic": 140, "bp_diastolic": 89, "heart_rate": 74, "blood_glucose": 163.9, "weight": 71.8, "sleep_hours": 7.9, "activity_minutes": 35, "mood": 4, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Baseline stable. BP and glucose within target thresholds. Level 0."}, {"day": 3, "date": "2024-11-03", "phase": "stable", "bp_systolic": 138, "bp_diastolic": 89, "heart_rate": 77, "blood_glucose": 171.4, "weight": 72.1, "sleep_hours": 7.1, "activity_minutes": 33, "mood": 5, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Baseline stable. BP and glucose within target thresholds. Level 0."}, {"day": 4, "date": "2024-11-04", "phase": "stable", "bp_systolic": 135, "bp_diastolic": 85, "heart_rate": 77, "blood_glucose": 185.0, "weight": 71.8, "sleep_hours": 7.3, "activity_minutes": 36, "mood": 5, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Baseline stable. BP and glucose within target thresholds. Level 0."}, {"day": 5, "date": "2024-11-05", "phase": "stable", "bp_systolic": 142, "bp_diastolic": 89, "heart_rate": 76, "blood_glucose": 182.2, "weight": 71.9, "sleep_hours": 6.6, "activity_minutes": 45, "mood": 4, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Baseline stable. BP and glucose within target thresholds. Level 0."}, {"day": 6, "date": "2024-11-06", "phase": "stable", "bp_systolic": 137, "bp_diastolic": 90, "heart_rate": 79, "blood_glucose": 182.6, "weight": 72.2, "sleep_hours": 6.6, "activity_minutes": 20, "mood": 5, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Baseline stable. BP and glucose within target thresholds. Level 0."}, {"day": 7, "date": "2024-11-07", "phase": "stable", "bp_systolic": 140, "bp_diastolic": 88, "heart_rate": 72, "blood_glucose": 185.9, "weight": 72.1, "sleep_hours": 8.2, "activity_minutes": 20, "mood": 5, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "प्रणाम रमेश जी! आज सप्ताह का सातवाँ दिन है। आपके सभी वाइटल्स स्थिर हैं। सुरेश जी को साप्ताहिक रिपोर्ट भेज दी गई है। 💙", "en": "Greetings Ramesh ji! Week 1 complete. All your vitals are looking stable. We sent a weekly update to Suresh."}, "caregiver_action": "Sent 7-day health summary to Suresh Kumar: all vitals normal.", "clinician_note": "Baseline stable. BP and glucose within target thresholds. Level 0."}, {"day": 8, "date": "2024-11-08", "phase": "stable", "bp_systolic": 145, "bp_diastolic": 87, "heart_rate": 76, "blood_glucose": 164.1, "weight": 71.9, "sleep_hours": 7.3, "activity_minutes": 62, "mood": 4, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Baseline stable. BP and glucose within target thresholds. Level 0."}, {"day": 9, "date": "2024-11-09", "phase": "stable", "bp_systolic": 141, "bp_diastolic": 88, "heart_rate": 78, "blood_glucose": 188.4, "weight": 72.1, "sleep_hours": 6.5, "activity_minutes": 14, "mood": 3, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Baseline stable. BP and glucose within target thresholds. Level 0."}, {"day": 10, "date": "2024-11-10", "phase": "stable", "bp_systolic": 138, "bp_diastolic": 92, "heart_rate": 74, "blood_glucose": 167.3, "weight": 71.8, "sleep_hours": 6.5, "activity_minutes": 38, "mood": 4, "social_interaction": false, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Baseline stable. BP and glucose within target thresholds. Level 0."}, {"day": 11, "date": "2024-11-11", "phase": "deteriorating", "bp_systolic": 146, "bp_diastolic": 88, "heart_rate": 73, "blood_glucose": 193.6, "weight": 72.5, "sleep_hours": 5.8, "activity_minutes": 31, "mood": 3, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Minor baseline drift detected. Monitoring rolling 7-day averages."}, {"day": 12, "date": "2024-11-12", "phase": "deteriorating", "bp_systolic": 152, "bp_diastolic": 91, "heart_rate": 70, "blood_glucose": 214.9, "weight": 72.3, "sleep_hours": 6.8, "activity_minutes": 16, "mood": 2, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Minor baseline drift detected. Monitoring rolling 7-day averages."}, {"day": 13, "date": "2024-11-13", "phase": "deteriorating", "bp_systolic": 155, "bp_diastolic": 86, "heart_rate": 81, "blood_glucose": 212.6, "weight": 72.8, "sleep_hours": 7.0, "activity_minutes": 15, "mood": 3, "social_interaction": true, "symptoms": ["occasional headache"], "medication_taken": false, "escalation_level": 0, "asha_message": {"hi": "नमस्ते रमेश जी! आज की दवाई का समय हो गया है। कृपया बीपी और शुगर की दवाइयाँ नियमित रूप से लें। 💊", "en": "Hello Ramesh ji! Please do not miss today's prescribed medications. Consistent adherence is vital."}, "caregiver_action": "Gentle WhatsApp reminder sent to Suresh regarding missed morning dose.", "clinician_note": "Minor baseline drift detected. Monitoring rolling 7-day averages."}, {"day": 14, "date": "2024-11-14", "phase": "deteriorating", "bp_systolic": 146, "bp_diastolic": 98, "heart_rate": 74, "blood_glucose": 205.4, "weight": 72.3, "sleep_hours": 5.4, "activity_minutes": 32, "mood": 3, "social_interaction": true, "symptoms": [], "medication_taken": true, "escalation_level": 1, "asha_message": {"hi": "नमस्ते रमेश जी, आज आपका बीपी थोड़ा बढ़ा हुआ (146/98) लग रहा है। कृपया आज हल्का भोजन लें और शाम की दवाई समय पर लें। 💊", "en": "Hello Ramesh ji, your BP is slightly elevated (146/98) today. Please keep meals light and take your evening medicine on time."}, "caregiver_action": "Informed Suresh of upward BP trend; encouraged family check-in.", "clinician_note": "7-day BP trend analysis shows upward slope (+8 mmHg). Escalation Level 1 active."}, {"day": 15, "date": "2024-11-15", "phase": "deteriorating", "bp_systolic": 149, "bp_diastolic": 92, "heart_rate": 83, "blood_glucose": 211.3, "weight": 72.7, "sleep_hours": 6.5, "activity_minutes": 26, "mood": 3, "social_interaction": false, "symptoms": [], "medication_taken": false, "escalation_level": 1, "asha_message": {"hi": "नमस्ते रमेश जी! आज की दवाई का समय हो गया है। कृपया बीपी और शुगर की दवाइयाँ नियमित रूप से लें। 💊", "en": "Hello Ramesh ji! Please do not miss today's prescribed medications. Consistent adherence is vital."}, "caregiver_action": "Gentle WhatsApp reminder sent to Suresh regarding missed morning dose.", "clinician_note": "Adherence declining. Glycaemic variation rising. Continue Level 1 surveillance."}, {"day": 16, "date": "2024-11-16", "phase": "deteriorating", "bp_systolic": 151, "bp_diastolic": 91, "heart_rate": 83, "blood_glucose": 180.5, "weight": 72.8, "sleep_hours": 5.8, "activity_minutes": 19, "mood": 4, "social_interaction": false, "symptoms": [], "medication_taken": true, "escalation_level": 1, "asha_message": {"hi": "नमस्ते रमेश जी! आज आपका स्वास्थ्य सामान्य दिख रहा है। समय पर भोजन और हल्की सैर जारी रखें। ☀️", "en": "Hello Ramesh ji! Your health parameters look good today. Keep up the balanced diet and light activity."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Adherence declining. Glycaemic variation rising. Continue Level 1 surveillance."}, {"day": 17, "date": "2024-11-17", "phase": "deteriorating", "bp_systolic": 148, "bp_diastolic": 90, "heart_rate": 69, "blood_glucose": 236.4, "weight": 73.3, "sleep_hours": 6.8, "activity_minutes": 17, "mood": 3, "social_interaction": true, "symptoms": [], "medication_taken": false, "escalation_level": 1, "asha_message": {"hi": "नमस्ते रमेश जी! आज की दवाई का समय हो गया है। कृपया बीपी और शुगर की दवाइयाँ नियमित रूप से लें। 💊", "en": "Hello Ramesh ji! Please do not miss today's prescribed medications. Consistent adherence is vital."}, "caregiver_action": "Gentle WhatsApp reminder sent to Suresh regarding missed morning dose.", "clinician_note": "Adherence declining. Glycaemic variation rising. Continue Level 1 surveillance."}, {"day": 18, "date": "2024-11-18", "phase": "deteriorating", "bp_systolic": 150, "bp_diastolic": 91, "heart_rate": 77, "blood_glucose": 227.8, "weight": 73.4, "sleep_hours": 6.7, "activity_minutes": 12, "mood": 4, "social_interaction": true, "symptoms": ["slight dizziness"], "medication_taken": false, "escalation_level": 1, "asha_message": {"hi": "नमस्ते रमेश जी! आज की दवाई का समय हो गया है। कृपया बीपी और शुगर की दवाइयाँ नियमित रूप से लें। 💊", "en": "Hello Ramesh ji! Please do not miss today's prescribed medications. Consistent adherence is vital."}, "caregiver_action": "Gentle WhatsApp reminder sent to Suresh regarding missed morning dose.", "clinician_note": "Adherence declining. Glycaemic variation rising. Continue Level 1 surveillance."}, {"day": 19, "date": "2024-11-19", "phase": "deteriorating", "bp_systolic": 160, "bp_diastolic": 86, "heart_rate": 86, "blood_glucose": 205.1, "weight": 73.5, "sleep_hours": 7.2, "activity_minutes": 0, "mood": 2, "social_interaction": false, "symptoms": [], "medication_taken": true, "escalation_level": 1, "asha_message": {"hi": "रमेश जी, आज आपकी बीपी 160 तक पहुँच गई है और पिछले कुछ दिनों से दवाई छूट रही है। क्या कोई परेशानी है? ⚠️", "en": "Ramesh ji, your BP reached 160 mmHg and some medicines were missed recently. Are you feeling alright?"}, "caregiver_action": "Urgent WhatsApp alert sent: 7-day medication adherence dropped below 80%.", "clinician_note": "Adherence declining. Glycaemic variation rising. Continue Level 1 surveillance."}, {"day": 20, "date": "2024-11-20", "phase": "deteriorating", "bp_systolic": 165, "bp_diastolic": 94, "heart_rate": 73, "blood_glucose": 181.5, "weight": 73.7, "sleep_hours": 6.8, "activity_minutes": 18, "mood": 4, "social_interaction": true, "symptoms": ["slight dizziness", "mild fatigue"], "medication_taken": true, "escalation_level": 1, "asha_message": {"hi": "रमेश जी, आज आपने slight dizziness, mild fatigue की शिकायत की है। हमने इसे नोट कर लिया है और डॉक्टर के रिकॉर्ड में दर्ज किया है। 🩺", "en": "Ramesh ji, we noted your symptom: slight dizziness, mild fatigue. This has been logged for Dr. Sharma."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Adherence declining. Glycaemic variation rising. Continue Level 1 surveillance."}, {"day": 21, "date": "2024-11-21", "phase": "dangerous", "bp_systolic": 163, "bp_diastolic": 95, "heart_rate": 77, "blood_glucose": 275.6, "weight": 73.6, "sleep_hours": 5.1, "activity_minutes": 3, "mood": 3, "social_interaction": false, "symptoms": ["persistent headache"], "medication_taken": false, "escalation_level": 1, "asha_message": {"hi": "नमस्ते रमेश जी! आज की दवाई का समय हो गया है। कृपया बीपी और शुगर की दवाइयाँ नियमित रूप से लें। 💊", "en": "Hello Ramesh ji! Please do not miss today's prescribed medications. Consistent adherence is vital."}, "caregiver_action": "Gentle WhatsApp reminder sent to Suresh regarding missed morning dose.", "clinician_note": "Adherence declining. Glycaemic variation rising. Continue Level 1 surveillance."}, {"day": 22, "date": "2024-11-22", "phase": "dangerous", "bp_systolic": 161, "bp_diastolic": 101, "heart_rate": 81, "blood_glucose": 285.0, "weight": 73.5, "sleep_hours": 5.2, "activity_minutes": 13, "mood": 1, "social_interaction": false, "symptoms": ["fatigue", "dizziness"], "medication_taken": true, "escalation_level": 2, "asha_message": {"hi": "⚠️ रमेश जी, आज आपका बीपी 161/101 और शुगर 285 है। आपको चक्कर भी आ रहे हैं। कृपया अभी आराम से बैठ जाइए, मैंने डॉक्टर और सुरेश जी को सूचित कर दिया है।", "en": "⚠️ Ramesh ji, BP is 161/101 and glucose is 285 mg/dL. You reported dizziness. Please sit down; I have alerted Dr. Sharma and Suresh."}, "caregiver_action": "Priority Alert sent to Suresh: BP 161/101, Glucose 285 mg/dL. Clinic appointment recommended.", "clinician_note": "Clinical escalation Level 2 triggered: BP > 160 mmHg & Glucose > 250 mg/dL with dizziness."}, {"day": 23, "date": "2024-11-23", "phase": "dangerous", "bp_systolic": 165, "bp_diastolic": 99, "heart_rate": 80, "blood_glucose": 275.0, "weight": 74.1, "sleep_hours": 4.7, "activity_minutes": 15, "mood": 1, "social_interaction": false, "symptoms": ["dizziness", "fatigue"], "medication_taken": true, "escalation_level": 2, "asha_message": {"hi": "रमेश जी, आज आपने dizziness, fatigue की शिकायत की है। हमने इसे नोट कर लिया है और डॉक्टर के रिकॉर्ड में दर्ज किया है। 🩺", "en": "Ramesh ji, we noted your symptom: dizziness, fatigue. This has been logged for Dr. Sharma."}, "caregiver_action": "Routine monitoring active — no alert required.", "clinician_note": "Persistent hypertension and hyperglycaemia. Pre-visit briefing preparation initiated."}, {"day": 24, "date": "2024-11-24", "phase": "dangerous", "bp_systolic": 169, "bp_diastolic": 103, "heart_rate": 78, "blood_glucose": 287.0, "weight": 73.6, "sleep_hours": 6.7, "activity_minutes": 9, "mood": 3, "social_interaction": false, "symptoms": ["frequent urination"], "medication_taken": true, "escalation_level": 2, "asha_message": {"hi": "रमेश जी, नमस्ते। पिछले 5 दिनों से आप बाहर नहीं गए और किसी से बात नहीं हुई। क्या हम सुरेश जी या किसी मित्र को फोन मिलाएं? 💙", "en": "Ramesh ji, we noticed you have been alone the past 5 days. Would you like me to connect you with Suresh or a friend?"}, "caregiver_action": "Social isolation alert sent: 5 days without social activity. Suresh planned in-person visit.", "clinician_note": "Persistent hypertension and hyperglycaemia. Pre-visit briefing preparation initiated."}, {"day": 25, "date": "2024-11-25", "phase": "dangerous", "bp_systolic": 166, "bp_diastolic": 103, "heart_rate": 88, "blood_glucose": 293.5, "weight": 73.6, "sleep_hours": 5.8, "activity_minutes": 9, "mood": 2, "social_interaction": false, "symptoms": ["fatigue", "frequent urination"], "medication_taken": false, "escalation_level": 2, "asha_message": {"hi": "नमस्ते रमेश जी! आज की दवाई का समय हो गया है। कृपया बीपी और शुगर की दवाइयाँ नियमित रूप से लें। 💊", "en": "Hello Ramesh ji! Please do not miss today's prescribed medications. Consistent adherence is vital."}, "caregiver_action": "Gentle WhatsApp reminder sent to Suresh regarding missed morning dose.", "clinician_note": "Persistent hypertension and hyperglycaemia. Pre-visit briefing preparation initiated."}, {"day": 26, "date": "2024-11-26", "phase": "dangerous", "bp_systolic": 166, "bp_diastolic": 94, "heart_rate": 87, "blood_glucose": 305.0, "weight": 73.4, "sleep_hours": 5.7, "activity_minutes": 2, "mood": 2, "social_interaction": false, "symptoms": ["excessive thirst"], "medication_taken": false, "escalation_level": 2, "asha_message": {"hi": "नमस्ते रमेश जी! आज की दवाई का समय हो गया है। कृपया बीपी और शुगर की दवाइयाँ नियमित रूप से लें। 💊", "en": "Hello Ramesh ji! Please do not miss today's prescribed medications. Consistent adherence is vital."}, "caregiver_action": "Gentle WhatsApp reminder sent to Suresh regarding missed morning dose.", "clinician_note": "Persistent hypertension and hyperglycaemia. Pre-visit briefing preparation initiated."}, {"day": 27, "date": "2024-11-27", "phase": "dangerous", "bp_systolic": 164, "bp_diastolic": 102, "heart_rate": 84, "blood_glucose": 298.9, "weight": 73.9, "sleep_hours": 5.1, "activity_minutes": 4, "mood": 1, "social_interaction": false, "symptoms": ["fatigue"], "medication_taken": false, "escalation_level": 2, "asha_message": {"hi": "नमस्ते रमेश जी! आज की दवाई का समय हो गया है। कृपया बीपी और शुगर की दवाइयाँ नियमित रूप से लें। 💊", "en": "Hello Ramesh ji! Please do not miss today's prescribed medications. Consistent adherence is vital."}, "caregiver_action": "Gentle WhatsApp reminder sent to Suresh regarding missed morning dose.", "clinician_note": "Persistent hypertension and hyperglycaemia. Pre-visit briefing preparation initiated."}, {"day": 28, "date": "2024-11-28", "phase": "intervention", "bp_systolic": 170, "bp_diastolic": 105, "heart_rate": 80, "blood_glucose": 322.4, "weight": 72.9, "sleep_hours": 6.0, "activity_minutes": 9, "mood": 2, "social_interaction": false, "symptoms": ["dizziness", "nausea", "chest tightness"], "medication_taken": false, "escalation_level": 3, "asha_message": {"hi": "🆘 [आपातकालीन कॉल] रमेश जी! आपका बीपी 170/105 और शुगर 322 है, सीने में भारीपन है। कृपया तुरंत बैठें, पानी पिएं। सुरेश जी रास्ते में हैं!", "en": "🆘 [EMERGENCY CALL] Ramesh ji! BP is 170/105 and sugar is 322 with chest tightness. Stay seated; Suresh and medical help are alerted!"}, "caregiver_action": "CRITICAL EMERGENCY: SMS and Automated Call dispatched to Suresh to transport Ramesh ji to clinic.", "clinician_note": "Level 3 Critical: Hypertensive crisis criteria met (170/105, chest discomfort). Emergency protocol triggered."}, {"day": 29, "date": "2024-11-29", "phase": "intervention", "bp_systolic": 172, "bp_diastolic": 98, "heart_rate": 87, "blood_glucose": 310.6, "weight": 73.3, "sleep_hours": 6.5, "activity_minutes": 14, "mood": 3, "social_interaction": true, "symptoms": ["excessive thirst", "dizziness"], "medication_taken": true, "escalation_level": 2, "asha_message": {"hi": "रमेश जी, आज आपने excessive thirst, dizziness की शिकायत की है। हमने इसे नोट कर लिया है और डॉक्टर के रिकॉर्ड में दर्ज किया है। 🩺", "en": "Ramesh ji, we noted your symptom: excessive thirst, dizziness. This has been logged for Dr. Sharma."}, "caregiver_action": "Suresh visited in person; assisted with evening medication and doctor consultation.", "clinician_note": "Post-intervention stabilization observed. Vitals trending back toward safe range."}, {"day": 30, "date": "2024-11-30", "phase": "intervention", "bp_systolic": 162, "bp_diastolic": 97, "heart_rate": 90, "blood_glucose": 296.6, "weight": 73.5, "sleep_hours": 6.2, "activity_minutes": 15, "mood": 3, "social_interaction": true, "symptoms": ["fatigue", "dizziness"], "medication_taken": true, "escalation_level": 1, "asha_message": {"hi": "नमस्ते रमेश जी! आज डॉक्टर अंजलि शर्मा से मुलाक़ात का दिन है। पिछले 30 दिनों की पूरी रिपोर्ट क्लिनिक को भेज दी गई है। 🏥", "en": "Good morning Ramesh ji! Today is your consultation with Dr. Anjali Sharma. Your complete 30-day report is ready for the doctor."}, "caregiver_action": "Suresh visited in person; assisted with evening medication and doctor consultation.", "clinician_note": "30-day pre-visit report finalized. Recommendations: intensify antihypertensive therapy, order HbA1c."}];

// ── Doctor Pre-Visit Clinical Report Markdown ──────────────────
const DOCTOR_REPORT_MD = `# Pre-Visit Clinical Summary

**Patient:** Ramesh Kumar, 78M  
**Conditions:** Hypertension, Type 2 Diabetes  
**Allergies:** Penicillin, Sulfa drugs  
**Doctor:** Dr. Anjali Sharma  
**Report Date:** November 01, 2026 at 02:09  
**Period:** 30-day monitoring (Nov 1–30, 2024)  

---

## 30-Day Vitals Trend

| Day | Date | BP (sys/dia) | HR | Glucose | Weight | Meds | Social | Mood |
|-----|------|-------------|-----|---------|--------|------|--------|------|
|  1 | 11-01 | 139/87 | 73 | 185.5 | 72.0 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
|  2 | 11-02 | 140/89 | 74 | 163.9 | 71.8 | ✅ | ✅ | ⭐⭐⭐⭐ |
|  3 | 11-03 | 138/89 | 77 | 171.4 | 72.1 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
|  4 | 11-04 | 135/85 | 77 | 185.0 | 71.8 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
|  5 | 11-05 | 142/89 | 76 | 182.2 | 71.9 | ✅ | ✅ | ⭐⭐⭐⭐ |
|  6 | 11-06 | 137/90 | 79 | 182.6 | 72.2 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
|  7 | 11-07 | 140/88 | 72 | 185.9 | 72.1 | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
|  8 | 11-08 | 145/87 | 76 | 164.1 | 71.9 | ✅ | ✅ | ⭐⭐⭐⭐ |
|  9 | 11-09 | 141/88 | 78 | 188.4 | 72.1 | ✅ | ✅ | ⭐⭐⭐ |
| 10 | 11-10 | 138/92 | 74 | 167.3 | 71.8 | ✅ | — | ⭐⭐⭐⭐ |
| 11 | 11-11 | 146/88 | 73 | 193.6 | 72.5 | ✅ | ✅ | ⭐⭐⭐ |
| 12 | 11-12 | 152/91 📈 | 70 | 214.9 | 72.3 | ✅ | ✅ | ⭐⭐ |
| 13 | 11-13 | 155/86 📈 | 81 | 212.6 | 72.8 | ❌ | ✅ | ⭐⭐⭐ |
| 14 | 11-14 | 146/98 | 74 | 205.4 | 72.3 | ✅ | ✅ | ⭐⭐⭐ |
| 15 | 11-15 | 149/92 | 83 | 211.3 | 72.7 | ❌ | — | ⭐⭐⭐ |
| 16 | 11-16 | 151/91 📈 | 83 | 180.5 | 72.8 | ✅ | — | ⭐⭐⭐⭐ |
| 17 | 11-17 | 148/90 | 69 | 236.4 | 73.3 | ❌ | ✅ | ⭐⭐⭐ |
| 18 | 11-18 | 150/91 📈 | 77 | 227.8 | 73.4 | ❌ | ✅ | ⭐⭐⭐⭐ |
| 19 | 11-19 | 160/86 ⚠️ | 86 | 205.1 | 73.5 | ✅ | — | ⭐⭐ |
| 20 | 11-20 | 165/94 ⚠️ | 73 | 181.5 | 73.7 | ✅ | ✅ | ⭐⭐⭐⭐ |
| 21 | 11-21 | 163/95 ⚠️ | 77 | 275.6 ⚠️ | 73.6 | ❌ | — | ⭐⭐⭐ |
| 22 | 11-22 | 161/101 ⚠️ | 81 | 285.0 ⚠️ | 73.5 | ✅ | — | ⭐ |
| 23 | 11-23 | 165/99 ⚠️ | 80 | 275.0 ⚠️ | 74.1 | ✅ | — | ⭐ |
| 24 | 11-24 | 169/103 ⚠️ | 78 | 287.0 ⚠️ | 73.6 | ✅ | — | ⭐⭐⭐ |
| 25 | 11-25 | 166/103 ⚠️ | 88 | 293.5 ⚠️ | 73.6 | ❌ | — | ⭐⭐ |
| 26 | 11-26 | 166/94 ⚠️ | 87 | 305.0 🆘 | 73.4 | ❌ | — | ⭐⭐ |
| 27 | 11-27 | 164/102 ⚠️ | 84 | 298.9 ⚠️ | 73.9 | ❌ | — | ⭐ |
| 28 | 11-28 | 170/105 ⚠️ | 80 | 322.4 🆘 | 72.9 | ❌ | — | ⭐⭐ |
| 29 | 11-29 | 172/98 ⚠️ | 87 | 310.6 🆘 | 73.3 | ✅ | ✅ | ⭐⭐⭐ |
| 30 | 11-30 | 162/97 ⚠️ | 90 | 296.6 ⚠️ | 73.5 | ✅ | ✅ | ⭐⭐⭐ |

## Summary Statistics

### Vitals
- **Average BP:** 152.5 mmHg (Max: 172, Min: 135)
- **Average Blood Glucose:** 226.5 mg/dL (Max: 322.4)
- **Average Heart Rate:** 78.6 bpm
- **Weight Change:** 72.0 → 73.5 kg (+1.5 kg)

### Medication
- **30-Day Adherence:** 70.0% 🆘
- **Doses Taken:** 147
- **Doses Missed:** 63

### Social Wellbeing
- **Social Interaction Days:** 18/30
- **Isolation Days:** 12
- **Wellbeing Score:** 1.0/5

### Clinical Events
- **Peak Escalation Level:** 3/3
- **Critical Events:** 0
- **Warning Events:** 0
- **Caregiver Alerts Sent:** 21

---

## Key Clinical Events


---

## Clinical Recommendations

1. **Antihypertensive Review:** BP consistently elevated (avg 152.5 mmHg). Intensify regimen.
2. **Glycaemic Control:** Mean glucose 226.5 mg/dL. Request HbA1c. Consider endocrinology.
3. **Medication Adherence:** 70.0% — Critical: implement pill organiser.
4. **Social Prescription:** 12 days isolation. Screen for depression; community referral.
5. **Weight Management:** +1.5 kg in 30 days. Dietary review.
6. **Physical Activity:** Physiotherapy referral recommended.
7. **Family Involvement:** Invite caregiver to next appointment.

---
*Generated by MedInsightAgent AI Clinical Support System*  
*November 01, 2026 at 02:09*`;

/* ── Global State ─────────────────────────────────────────── */
let currentPhaseStart = 1;
let currentPhaseEnd = 30;
let activeDay = 1;
let isPlaying = false;
let playbackTimer = null;
let playbackSpeed = 800; // ms per simulated day
const speeds = [800, 400, 1500];
let speedIdx = 0;

// Chart.js instances
let chartBP = null;
let chartEsc = null;
let chartGluc = null;
let chartHRWeight = null;
let chartMoodSocial = null;

/* ── Initialize on DOM Load ───────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initCharts();
  renderVitalsTable();
  updateKPIs(currentPhaseStart, currentPhaseEnd);
  drawAllSparklines(currentPhaseStart, currentPhaseEnd);
  updateEscalationMeter(currentPhaseStart, currentPhaseEnd);
  setupTableSearch();
  initChatHistory();
});

/* ── Chart.js Setup ───────────────────────────────────────── */
function initCharts() {
  if (typeof Chart === 'undefined') {
    console.error('Chart.js not loaded');
    return;
  }

  // Global defaults
  Chart.defaults.color = '#8899a6';
  Chart.defaults.font.family = 'Inter, -apple-system, sans-serif';
  Chart.defaults.font.size = 11;
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(10, 13, 20, 0.95)';
  Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)';
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 8;

  const daysSlice = TIMELINE_DATA.slice(currentPhaseStart - 1, currentPhaseEnd);
  const labels = daysSlice.map(d => `Day ${d.day}`);

  // 1. Blood Pressure Chart
  const ctxBP = document.getElementById('chartBP');
  if (ctxBP) {
    chartBP = new Chart(ctxBP, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Systolic (mmHg)',
            data: daysSlice.map(d => d.bp_systolic),
            borderColor: '#EF4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            borderWidth: 2.2,
            tension: 0.35,
            pointRadius: 3.5,
            pointHoverRadius: 6,
            fill: true
          },
          {
            label: 'Diastolic (mmHg)',
            data: daysSlice.map(d => d.bp_diastolic),
            borderColor: '#4F8EF7',
            backgroundColor: 'rgba(79, 142, 247, 0.05)',
            borderWidth: 2,
            tension: 0.35,
            pointRadius: 3,
            pointHoverRadius: 5,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { position: 'top', align: 'end' },
          tooltip: {
            callbacks: {
              afterLabel: (ctx) => {
                const dayObj = TIMELINE_DATA[ctx.dataIndex];
                if (dayObj && dayObj.symptoms && dayObj.symptoms.length > 0) {
                  return `⚠️ Symptoms: ${dayObj.symptoms.join(', ')}`;
                }
                return '';
              }
            }
          }
        },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.04)' } },
          y: {
            min: 70,
            max: 185,
            grid: { color: 'rgba(255, 255, 255, 0.06)' },
            title: { display: true, text: 'mmHg', color: '#64748B' }
          }
        }
      }
    });
  }

  // 2. Escalation Timeline Chart
  const ctxEsc = document.getElementById('chartEsc');
  if (ctxEsc) {
    const escColors = daysSlice.map(d => {
      if (d.escalation_level === 3) return '#EF4444';
      if (d.escalation_level === 2) return '#F97316';
      if (d.escalation_level === 1) return '#F59E0B';
      return '#10B981';
    });

    chartEsc = new Chart(ctxEsc, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Escalation Level',
          data: daysSlice.map(d => d.escalation_level),
          backgroundColor: escColors,
          borderRadius: 4,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false } },
          y: {
            min: 0,
            max: 3,
            ticks: { stepSize: 1, callback: (v) => `Lvl ${v}` },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          }
        }
      }
    });
  }

  // 3. Blood Glucose Chart
  const ctxGluc = document.getElementById('chartGluc');
  if (ctxGluc) {
    chartGluc = new Chart(ctxGluc, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Blood Glucose (mg/dL)',
          data: daysSlice.map(d => d.blood_glucose),
          borderColor: '#F59E0B',
          backgroundColor: 'rgba(245, 158, 11, 0.12)',
          borderWidth: 2.2,
          tension: 0.35,
          pointRadius: 3.5,
          pointHoverRadius: 6,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: (ctx) => {
                const val = ctx.parsed.y;
                if (val >= 300) return '🚨 CRITICAL (≥300)';
                if (val >= 250) return '⚠️ WARNING (≥250)';
                return '✓ Normal Range';
              }
            }
          }
        },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.04)' } },
          y: {
            min: 140,
            max: 350,
            grid: { color: 'rgba(255, 255, 255, 0.06)' },
            title: { display: true, text: 'mg/dL', color: '#64748B' }
          }
        }
      }
    });
  }

  // 4. Heart Rate & Weight Chart (Dual Axis)
  const ctxHR = document.getElementById('chartHRWeight');
  if (ctxHR) {
    chartHRWeight = new Chart(ctxHR, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Heart Rate (bpm)',
            data: daysSlice.map(d => d.heart_rate),
            borderColor: '#4F8EF7',
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 2.5,
            yAxisID: 'y'
          },
          {
            label: 'Weight (kg)',
            data: daysSlice.map(d => d.weight),
            borderColor: '#10B981',
            borderWidth: 2,
            borderDash: [4, 4],
            tension: 0.3,
            pointRadius: 2.5,
            yAxisID: 'y1'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: { legend: { position: 'top', align: 'end' } },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.04)' } },
          y: {
            type: 'linear',
            position: 'left',
            min: 60,
            max: 100,
            title: { display: true, text: 'bpm', color: '#4F8EF7' },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          y1: {
            type: 'linear',
            position: 'right',
            min: 70,
            max: 76,
            title: { display: true, text: 'kg', color: '#10B981' },
            grid: { drawOnChartArea: false }
          }
        }
      }
    });
  }

  // 5. Mood & Social Score Chart
  const ctxMood = document.getElementById('chartMoodSocial');
  if (ctxMood) {
    chartMoodSocial = new Chart(ctxMood, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            type: 'line',
            label: 'Mood (1–5)',
            data: daysSlice.map(d => d.mood),
            borderColor: '#EC4899',
            borderWidth: 2.2,
            tension: 0.25,
            pointRadius: 4,
            pointBackgroundColor: '#EC4899',
            yAxisID: 'y'
          },
          {
            type: 'bar',
            label: 'Social Contact',
            data: daysSlice.map(d => d.social_interaction ? 1 : 0),
            backgroundColor: daysSlice.map(d => d.social_interaction ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.25)'),
            yAxisID: 'y1',
            borderRadius: 3
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: { legend: { position: 'top', align: 'end' } },
        scales: {
          x: { grid: { color: 'rgba(255, 255, 255, 0.04)' } },
          y: {
            min: 0,
            max: 5,
            ticks: { stepSize: 1 },
            title: { display: true, text: 'Mood Score', color: '#EC4899' },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          y1: {
            min: 0,
            max: 1.5,
            display: false,
            grid: { drawOnChartArea: false }
          }
        }
      }
    });
  }
}

/* ── Sparklines on HTML5 Canvas ────────────────────────────── */
function drawSparkline(canvasId, values, strokeColor, fillColor) {
  const cvs = document.getElementById(canvasId);
  if (!cvs || !values || values.length === 0) return;
  const ctx = cvs.getContext('2d');
  const w = cvs.width;
  const h = cvs.height;
  ctx.clearRect(0, 0, w, h);

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  ctx.beginPath();
  values.forEach((v, i) => {
    const x = (i / (values.length - 1 || 1)) * (w - 6) + 3;
    const y = h - 4 - ((v - min) / range) * (h - 8);
    if (i === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });

  ctx.strokeStyle = strokeColor;
  ctx.lineWidth = 1.8;
  ctx.stroke();

  // Gradient fill under curve
  if (fillColor) {
    ctx.lineTo(w - 3, h);
    ctx.lineTo(3, h);
    ctx.closePath();
    ctx.fillStyle = fillColor;
    ctx.fill();
  }
}

function drawAllSparklines(start, end) {
  const slice = TIMELINE_DATA.slice(start - 1, end);
  drawSparkline('sparkBP', slice.map(d => d.bp_systolic), '#EF4444', 'rgba(239, 68, 68, 0.15)');
  drawSparkline('sparkGluc', slice.map(d => d.blood_glucose), '#F59E0B', 'rgba(245, 158, 11, 0.15)');
  drawSparkline('sparkHR', slice.map(d => d.heart_rate), '#4F8EF7', 'rgba(79, 142, 247, 0.15)');
  drawSparkline('sparkAdh', slice.map((d, i) => {
    const sub = slice.slice(0, i + 1);
    const taken = sub.filter(x => x.medication_taken).length;
    return Math.round((taken / sub.length) * 100);
  }), '#10B981', 'rgba(16, 185, 129, 0.15)');
}

/* ── Phase Filtering ───────────────────────────────────────── */
window.setPhase = function(btnEl, start, end) {
  currentPhaseStart = start;
  currentPhaseEnd = end;

  // Toggle active pill button
  document.querySelectorAll('#phasePills .phase-pill').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');

  const slice = TIMELINE_DATA.slice(start - 1, end);
  const labels = slice.map(d => `Day ${d.day}`);

  // Update Charts
  if (chartBP) {
    chartBP.data.labels = labels;
    chartBP.data.datasets[0].data = slice.map(d => d.bp_systolic);
    chartBP.data.datasets[1].data = slice.map(d => d.bp_diastolic);
    chartBP.update();
  }

  if (chartEsc) {
    chartEsc.data.labels = labels;
    chartEsc.data.datasets[0].data = slice.map(d => d.escalation_level);
    chartEsc.data.datasets[0].backgroundColor = slice.map(d => {
      if (d.escalation_level === 3) return '#EF4444';
      if (d.escalation_level === 2) return '#F97316';
      if (d.escalation_level === 1) return '#F59E0B';
      return '#10B981';
    });
    chartEsc.update();
  }

  if (chartGluc) {
    chartGluc.data.labels = labels;
    chartGluc.data.datasets[0].data = slice.map(d => d.blood_glucose);
    chartGluc.update();
  }

  if (chartHRWeight) {
    chartHRWeight.data.labels = labels;
    chartHRWeight.data.datasets[0].data = slice.map(d => d.heart_rate);
    chartHRWeight.data.datasets[1].data = slice.map(d => d.weight);
    chartHRWeight.update();
  }

  if (chartMoodSocial) {
    chartMoodSocial.data.labels = labels;
    chartMoodSocial.data.datasets[0].data = slice.map(d => d.mood);
    chartMoodSocial.data.datasets[1].data = slice.map(d => d.social_interaction ? 1 : 0);
    chartMoodSocial.data.datasets[1].backgroundColor = slice.map(d =>
      d.social_interaction ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.25)'
    );
    chartMoodSocial.update();
  }

  // Update KPIs and Sparklines
  updateKPIs(start, end);
  drawAllSparklines(start, end);
  updateEscalationMeter(start, end);

  // Filter Table View
  filterTableByPhase(start, end);
};

/* ── Update KPI Numbers ────────────────────────────────────── */
function updateKPIs(start, end) {
  const slice = TIMELINE_DATA.slice(start - 1, end);
  if (!slice.length) return;

  const avgSys = (slice.reduce((acc, d) => acc + d.bp_systolic, 0) / slice.length).toFixed(1);
  const avgDia = Math.round(slice.reduce((acc, d) => acc + d.bp_diastolic, 0) / slice.length);
  const avgGluc = (slice.reduce((acc, d) => acc + d.blood_glucose, 0) / slice.length).toFixed(1);
  const avgHR = (slice.reduce((acc, d) => acc + d.heart_rate, 0) / slice.length).toFixed(1);
  const medsTaken = slice.filter(d => d.medication_taken).length;
  const adhPct = ((medsTaken / slice.length) * 100).toFixed(1);

  const kBP = document.getElementById('kpiBP');
  const kGluc = document.getElementById('kpiGluc');
  const kHR = document.getElementById('kpiHR');
  const kAdh = document.getElementById('kpiAdh');

  if (kBP) kBP.textContent = `${avgSys} / ${avgDia}`;
  if (kGluc) kGluc.textContent = `${avgGluc} mg/dL`;
  if (kHR) kHR.textContent = `${avgHR} bpm`;
  if (kAdh) {
    kAdh.textContent = `${adhPct}%`;
    kAdh.classList.toggle('kpi-card__value--warn', parseFloat(adhPct) < 85);
  }
}

/* ── Update Escalation Meter ───────────────────────────────── */
function updateEscalationMeter(start, end) {
  const slice = TIMELINE_DATA.slice(start - 1, end);
  const peakLevel = Math.max(...slice.map(d => d.escalation_level), 0);

  document.querySelectorAll('#escalationMeter .esc-level').forEach(el => {
    const lvl = parseInt(el.dataset.level);
    if (lvl === peakLevel) {
      el.classList.add('esc-level--active');
      const strong = el.querySelector('strong');
      if (strong && !strong.textContent.includes('CURRENT')) {
        strong.textContent = `Level ${lvl} ← ACTIVE`;
      }
    } else {
      el.classList.remove('esc-level--active');
      const strong = el.querySelector('strong');
      if (strong) {
        strong.textContent = `Level ${lvl}`;
      }
    }
  });
}

/* ── Render 30-Day Vitals Table ────────────────────────────── */
function renderVitalsTable() {
  const tbody = document.getElementById('vitalsTableBody');
  if (!tbody) return;
  tbody.innerHTML = '';

  TIMELINE_DATA.forEach(d => {
    const tr = document.createElement('tr');
    tr.id = `rowDay${d.day}`;
    tr.className = `tr-${d.phase}`;
    tr.dataset.day = d.day;
    tr.dataset.phase = d.phase;
    tr.onclick = () => openDayModal(d.day);

    // Format Flags
    const bpClass = d.bp_systolic >= 165 ? 'vf-crit' : (d.bp_systolic >= 150 ? 'vf-warn' : 'vf-ok');
    const glucClass = d.blood_glucose >= 300 ? 'vf-crit' : (d.blood_glucose >= 220 ? 'vf-warn' : 'vf-ok');
    const medBadge = d.medication_taken
      ? '<span class="badge badge--green">Taken</span>'
      : '<span class="badge badge--red vf-miss">Missed</span>';
    const socialBadge = d.social_interaction
      ? '<span class="badge badge--green">Yes</span>'
      : '<span class="badge badge--orange">No (Alone)</span>';

    // Mood star rating
    const moodStars = '⭐'.repeat(d.mood);

    // Status label
    let statusBadge = '<span class="badge badge--green">Normal</span>';
    if (d.escalation_level === 3) statusBadge = '<span class="badge badge--red">CRITICAL</span>';
    else if (d.escalation_level === 2) statusBadge = '<span class="badge badge--orange">Warning</span>';
    else if (d.escalation_level === 1) statusBadge = '<span class="badge badge--yellow">Watch</span>';

    tr.innerHTML = `
      <td><strong>Day ${d.day}</strong></td>
      <td>${d.date.slice(5)}</td>
      <td><span class="badge badge--${getPhaseBadgeColor(d.phase)}">${capitalize(d.phase)}</span></td>
      <td class="${bpClass}">${d.bp_systolic}/${d.bp_diastolic} ${d.bp_systolic >= 160 ? '⚠️' : ''}</td>
      <td>${d.heart_rate} bpm</td>
      <td class="${glucClass}">${d.blood_glucose}</td>
      <td>${d.weight} kg</td>
      <td>${medBadge}</td>
      <td>${socialBadge}</td>
      <td title="Mood score ${d.mood}/5">${moodStars}</td>
      <td>${statusBadge}</td>
    `;
    tbody.appendChild(tr);
  });
}

function getPhaseBadgeColor(phase) {
  if (phase === 'stable') return 'green';
  if (phase === 'deteriorating') return 'yellow';
  if (phase === 'dangerous') return 'orange';
  return 'red';
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/* ── Filter Table Rows ─────────────────────────────────────── */
function filterTableByPhase(start, end) {
  document.querySelectorAll('#vitalsTableBody tr').forEach(tr => {
    const d = parseInt(tr.dataset.day);
    if (d >= start && d <= end) {
      tr.style.display = '';
    } else {
      tr.style.display = 'none';
    }
  });
}

function setupTableSearch() {
  const searchInput = document.getElementById('tableSearch');
  if (!searchInput) return;

  searchInput.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    document.querySelectorAll('#vitalsTableBody tr').forEach(tr => {
      const text = tr.textContent.toLowerCase();
      const match = text.includes(q);
      tr.style.display = match ? '' : 'none';
    });
  });
}

/* ── CSV Export ────────────────────────────────────────────── */
window.exportTableCSV = function() {
  const headers = ['Day', 'Date', 'Phase', 'BP_Systolic', 'BP_Diastolic', 'Heart_Rate', 'Glucose_mg_dL', 'Weight_kg', 'Sleep_Hours', 'Activity_Mins', 'Mood_1_to_5', 'Meds_Taken', 'Social_Interaction', 'Symptoms', 'Escalation_Level'];
  const rows = TIMELINE_DATA.map(d => [
    d.day,
    d.date,
    d.phase,
    d.bp_systolic,
    d.bp_diastolic,
    d.heart_rate,
    d.blood_glucose,
    d.weight,
    d.sleep_hours,
    d.activity_minutes,
    d.mood,
    d.medication_taken ? 'YES' : 'NO',
    d.social_interaction ? 'YES' : 'NO',
    `"${(d.symptoms || []).join('; ')}"`,
    d.escalation_level
  ]);

  const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement('a');
  link.setAttribute('href', encodedUri);
  link.setAttribute('download', `CareSync_RameshKumar_30Day_Vitals.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  showToast('CSV Exported', '30-Day vitals log downloaded successfully.', 'success');
};

/* ── Day Details Modal ─────────────────────────────────────── */
window.openDayModal = function(day) {
  const d = TIMELINE_DATA.find(x => x.day === day);
  if (!d) return;

  activeDay = day;
  const modal = document.getElementById('dayModal');
  const mTitle = document.getElementById('mDayTitle');
  const mPhaseBadge = document.getElementById('mPhaseBadge');
  const mBody = document.getElementById('mBody');

  if (mTitle) mTitle.textContent = `Day ${d.day} Overview · ${d.date}`;
  if (mPhaseBadge) {
    mPhaseBadge.className = `badge badge--${getPhaseBadgeColor(d.phase)}`;
    mPhaseBadge.textContent = `${capitalize(d.phase)} · Level ${d.escalation_level}`;
  }

  const symptomsList = d.symptoms && d.symptoms.length > 0
    ? d.symptoms.map(s => `<span class="badge badge--red">${s}</span>`).join(' ')
    : '<span class="badge badge--green">No symptoms reported</span>';

  const medDetail = d.medication_taken
    ? '<span style="color:var(--green);font-weight:700;">✓ All doses confirmed taken</span>'
    : '<span style="color:var(--red);font-weight:700;">⚠️ Prescribed doses MISSED today</span>';

  if (mBody) {
    mBody.innerHTML = `
      <div class="modal-grid">
        <div class="modal-stat-box">
          <span class="lbl">Blood Pressure</span>
          <span class="val" style="color:${d.bp_systolic >= 160 ? 'var(--red)' : 'var(--text)'}">${d.bp_systolic}/${d.bp_diastolic} mmHg</span>
        </div>
        <div class="modal-stat-box">
          <span class="lbl">Blood Glucose</span>
          <span class="val" style="color:${d.blood_glucose >= 250 ? 'var(--orange)' : 'var(--text)'}">${d.blood_glucose} mg/dL</span>
        </div>
        <div class="modal-stat-box">
          <span class="lbl">Heart Rate</span>
          <span class="val">${d.heart_rate} bpm</span>
        </div>
        <div class="modal-stat-box">
          <span class="lbl">Weight</span>
          <span class="val">${d.weight} kg</span>
        </div>
        <div class="modal-stat-box">
          <span class="lbl">Sleep / Activity</span>
          <span class="val" style="font-size:0.95rem;">${d.sleep_hours}h sleep · ${d.activity_minutes}m walk</span>
        </div>
        <div class="modal-stat-box">
          <span class="lbl">Mood & Social</span>
          <span class="val" style="font-size:0.95rem;">${'⭐'.repeat(d.mood)} · ${d.social_interaction ? 'Connected' : 'Isolated'}</span>
        </div>
      </div>

      <div class="modal-section">
        <h4><span>💊</span> Medication & Symptoms</h4>
        <p>${medDetail}</p>
        <div style="margin-top:0.4rem;"><strong>Symptoms:</strong> ${symptomsList}</div>
      </div>

      <div class="modal-section">
        <h4><span>🤖</span> Asha (Patient Agent) Interaction</h4>
        <p style="font-style:italic;color:var(--text);margin-bottom:0.4rem;">"${d.asha_message.hi}"</p>
        <p style="font-size:0.75rem;color:var(--text-dim);">English translation: "${d.asha_message.en}"</p>
      </div>

      <div class="modal-section">
        <h4><span>👨‍👩‍👦</span> ConnectAgent Action</h4>
        <p>${d.caregiver_action}</p>
      </div>

      <div class="modal-section">
        <h4><span>🩺</span> MedInsightAgent Clinical Assessment</h4>
        <p>${d.clinician_note}</p>
      </div>
    `;
  }

  modal.classList.add('open');
};

window.closeDayModal = function(e) {
  if (e && e.target && e.target.id !== 'dayModal' && !e.target.classList.contains('modal-close')) {
    return;
  }
  const modal = document.getElementById('dayModal');
  if (modal) modal.classList.remove('open');
};

/* ── Doctor Report Modal ───────────────────────────────────── */
window.openReportModal = function() {
  const modal = document.getElementById('reportModal');
  const body = document.getElementById('reportModalBody');
  if (body) {
    // Format Markdown into clean HTML
    let html = DOCTOR_REPORT_MD
      .replace(/^# (.*$)/gim, '<h1 style="font-size:1.4rem;font-weight:800;color:var(--text);margin-bottom:0.75rem;">$1</h1>')
      .replace(/^## (.*$)/gim, '<h2 style="font-size:1.1rem;font-weight:700;color:var(--text);margin:1.25rem 0 0.5rem 0;border-bottom:1px solid var(--border);padding-bottom:0.3rem;">$1</h2>')
      .replace(/^### (.*$)/gim, '<h3 style="font-size:0.95rem;font-weight:700;color:var(--text);margin:0.75rem 0 0.35rem;">$1</h3>')
      .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/gim, '<em>$1</em>')
      .replace(/\n\n/gim, '<br/><br/>');

    body.innerHTML = `
      <div style="font-family:var(--font);font-size:0.85rem;color:var(--text-muted);line-height:1.6;">
        ${html}
      </div>
    `;
  }
  if (modal) modal.classList.add('open');
};

window.closeReportModal = function(e) {
  if (e && e.target && e.target.id !== 'reportModal' && !e.target.classList.contains('modal-close')) {
    return;
  }
  const modal = document.getElementById('reportModal');
  if (modal) modal.classList.remove('open');
};

// Close modals on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeDayModal();
    closeReportModal();
  }
});

/* ── Interactive Day Playback Engine ───────────────────────── */
window.togglePlaySimulation = function() {
  if (isPlaying) {
    pauseSimulation();
  } else {
    playSimulation();
  }
};

window.playSimulation = function() {
  isPlaying = true;
  const playIcon = document.getElementById('playIcon');
  const playText = document.getElementById('playText');
  if (playIcon) playIcon.textContent = '⏸';
  if (playText) playText.textContent = 'Pause';

  playbackTimer = setInterval(() => {
    stepSimulation();
  }, playbackSpeed);
};

window.pauseSimulation = function() {
  isPlaying = false;
  if (playbackTimer) clearInterval(playbackTimer);
  const playIcon = document.getElementById('playIcon');
  const playText = document.getElementById('playText');
  if (playIcon) playIcon.textContent = '▶';
  if (playText) playText.textContent = 'Play Sim';
};

window.resetSimulation = function() {
  pauseSimulation();
  activeDay = 1;
  highlightDay(1);
  updateLiveDayIndicator(1);
  updateKPIs(1, 1);
  updateEscalationMeter(1, 1);
  showToast('Simulation Reset', 'Rewound to Day 1 baseline.', 'info');
};

window.cycleSpeed = function() {
  speedIdx = (speedIdx + 1) % speeds.length;
  playbackSpeed = speeds[speedIdx];
  const badge = document.getElementById('speedBadge');
  if (badge) {
    const label = speedIdx === 0 ? '1x' : (speedIdx === 1 ? '2x' : '0.5x');
    badge.textContent = label;
  }
  if (isPlaying) {
    pauseSimulation();
    playSimulation();
  }
};

function stepSimulation() {
  if (activeDay >= 30) {
    pauseSimulation();
    showToast('Simulation Complete', 'Reached Day 30 doctor visit report.', 'success');
    return;
  }

  activeDay++;
  highlightDay(activeDay);
  updateLiveDayIndicator(activeDay);
  updateKPIs(1, activeDay);
  updateEscalationMeter(1, activeDay);
  checkMilestoneEvents(activeDay);
}

function highlightDay(day) {
  document.querySelectorAll('#vitalsTableBody tr').forEach(tr => tr.classList.remove('selected'));
  const row = document.getElementById(`rowDay${day}`);
  if (row) {
    row.classList.add('selected');
    row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}

function updateLiveDayIndicator(day) {
  const ind = document.getElementById('simDayIndicator');
  if (ind) ind.textContent = `Day ${day} / 30`;
}

function checkMilestoneEvents(day) {
  const d = TIMELINE_DATA.find(x => x.day === day);
  if (!d) return;

  if (day === 7) {
    showToast('Day 7: Weekly Summary', 'ConnectAgent sent Week 1 health summary to Suresh. All vitals stable.', 'success');
  } else if (day === 14) {
    showToast('Day 14: BP Trend Detected', 'MedInsightAgent identified 7-day rising systolic trend. Escalated to Level 1.', 'warning');
  } else if (day === 19) {
    showToast('Day 19: Medication Alert', 'Medication adherence dropped below 80%. Urgent WhatsApp sent to Suresh.', 'warning');
  } else if (day === 22) {
    showToast('Day 22: Level 2 Warning', `BP ${d.bp_systolic}/${d.bp_diastolic} & Glucose ${d.blood_glucose}. Doctor and family notified!`, 'danger');
  } else if (day === 24) {
    showToast('Day 24: Social Isolation', '5 days without social activity. Asha nudged patient; family alert sent.', 'warning');
  } else if (day === 28) {
    showToast('Day 28: CRITICAL Level 3', `Emergency call dispatched! BP ${d.bp_systolic}/${d.bp_diastolic}, Glucose ${d.blood_glucose}.`, 'danger', 6000);
  } else if (day === 30) {
    showToast('Day 30: Doctor Visit Report', 'Full 30-day pre-visit report delivered to Dr. Anjali Sharma.', 'info');
  }
}

/* ── Toast Alert Notifications ─────────────────────────────── */
function showToast(title, desc, type = 'info', duration = 3500) {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;

  const iconMap = {
    info: 'ℹ️',
    success: '✅',
    warning: '⚠️',
    danger: '🚨'
  };

  toast.innerHTML = `
    <span class="toast__icon">${iconMap[type] || '🔔'}</span>
    <div class="toast__content">
      <div class="toast__title">${title}</div>
      <div class="toast__desc">${desc}</div>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(60px)';
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 300);
  }, duration);
}

/* ── Interactive Bilingual Asha Chat Assistant ─────────────── */
window.toggleChat = function() {
  const drawer = document.getElementById('chatDrawer');
  if (drawer) {
    drawer.classList.toggle('open');
    if (drawer.classList.contains('open')) {
      const input = document.getElementById('chatInput');
      if (input) input.focus();
    }
  }
};

function initChatHistory() {
  const container = document.getElementById('chatMessages');
  if (!container) return;
  container.innerHTML = `
    <div class="chat-msg chat-msg--bot">
      <div class="chat-msg__bubble">
        नमस्ते रमेश जी! 🙏 मैं आपकी केयर साथी <strong>आशा (Asha)</strong> हूँ।<br/>
        आप मुझसे हिंदी या English में कुछ भी पूछ सकते हैं — जैसे आज की दवाई, बीपी या कोई तकलीफ।
      </div>
      <span class="chat-msg__meta">Asha · Just now</span>
    </div>
  `;
}

window.sendQuickChat = function(text) {
  const input = document.getElementById('chatInput');
  if (input) input.value = text;
  handleChatSubmit();
};

window.handleChatSubmit = function(e) {
  if (e) e.preventDefault();
  const input = document.getElementById('chatInput');
  if (!input) return;
  const text = input.value.trim();
  if (!text) return;

  appendChatMessage(text, 'user');
  input.value = '';

  // Show typing animation then reply
  setTimeout(() => {
    respondAshaChat(text);
  }, 500);
};

function appendChatMessage(text, sender = 'bot', meta = '') {
  const container = document.getElementById('chatMessages');
  if (!container) return;

  const msg = document.createElement('div');
  msg.className = `chat-msg chat-msg--${sender}`;
  const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  msg.innerHTML = `
    <div class="chat-msg__bubble">${text}</div>
    <span class="chat-msg__meta">${sender === 'bot' ? 'Asha' : 'You'} · ${now} ${meta}</span>
  `;

  container.appendChild(msg);
  container.scrollTop = container.scrollHeight;
}

function respondAshaChat(query) {
  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: query, day: activeDay, language: currentLang })
  })
  .then(res => res.json())
  .then(data => {
    if (data && data.reply) {
      appendChatMessage(data.reply, 'bot');
      if (data.alert_level && data.alert_level >= 2) {
        showToast('Clinical Alert Triggered', 'Asha coordinated with Dr. Sharma & Caregiver.', 'danger');
      }
      return;
    }
    clientSideAshaResponse(query);
  })
  .catch(() => {
    clientSideAshaResponse(query);
  });
}

function clientSideAshaResponse(q) {
  if (typeof AshaAI !== 'undefined' && AshaAI.reply) {
    const res = AshaAI.reply(q, currentLang || 'hi');
    appendChatMessage(res.reply, 'bot');
    if (res.alert_level >= 3) {
      showToast('EMERGENCY ALERT', 'Emergency protocol triggered. Alert sent to Suresh and 108 helpline.', 'danger', 7000);
    } else if (res.alert_level >= 2) {
      showToast('Clinical Alert Triggered', 'Symptom recorded and flagged for Dr. Sharma review.', 'warning', 5000);
    }
    return;
  }

  const lower = q.toLowerCase();
  if (lower.includes('chest') || lower.includes('दर्द') || lower.includes('pain') || lower.includes('सांस')) {
    appendChatMessage('⚠️ रमेश जी, कृपया तुरंत आराम से बैठें। आपातकालीन हेल्पलाइन 108 डायल करें। हमने सुरेश जी और डॉ. शर्मा को सूचित किया है।', 'bot');
    showToast('EMERGENCY ALERT', 'Emergency alert dispatched.', 'danger');
  } else {
    appendChatMessage('नमस्ते रमेश जी! मैंने आपकी बात नोट कर ली है। समय पर दवाइयाँ लें और पर्याप्त पानी पिएं। 🙏', 'bot');
  }
}
