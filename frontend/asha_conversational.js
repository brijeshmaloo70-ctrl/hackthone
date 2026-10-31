/**
 * frontend/asha_conversational.js
 * Client-Side Conversational AI Engine for Asha (Patient Companion).
 * Guarantees immediate, high-quality, empathetic responses across
 * Hindi (हिन्दी), Marathi (मराठी), and English when the server is offline or local.
 */

const AshaAI = {
  reply: function(userMessage, lang) {
    const raw = (userMessage || "").trim();
    const q = raw.toLowerCase();
    lang = (lang || "hi").toLowerCase();
    if (lang.includes("en")) lang = "en";
    else if (lang.includes("mr")) lang = "mr";
    else lang = "hi";

    // 1. Emergency Detection (Chest Pain, Breathlessness, Heart Attack)
    if (
      q.includes("chest") || q.includes("सीने") || q.includes("छातीत") ||
      q.includes("breathless") || q.includes("सांस") || q.includes("दम") ||
      q.includes("heart") || q.includes("दिल") || q.includes("attack")
    ) {
      if (lang === "mr") {
        return {
          reply: "⚠️ **रमेश जी, छातीत दुखणे किंवा अस्वस्थता अजिबात दुर्लक्षित करू नका!**<br/>कृपया लगेच एका जागी शांत बसा, कपडे सैल करा आणि हळूहळू श्वास घ्या. मी तात्काळ आपले सुपुत्र सुरेश यांना आणि डॉ. अंजली शर्मा यांना अलर्ट पाठवला आहे. त्रास जास्त वाटल्यास वरील **लाल १०८ आपत्कालीन कॉल बटण** दाबा.",
          alertLevel: 3,
          isEmergency: true
        };
      } else if (lang === "en") {
        return {
          reply: "⚠️ **Ramesh-ji, please do not ignore chest pain or breathlessness!**<br/>Please sit down immediately, loosen your clothes, and take slow, deep breaths. I have sent an urgent emergency alert to your son Suresh and notified Dr. Anjali Sharma. Please tap the **Emergency 108 Call button** above right away.",
          alertLevel: 3,
          isEmergency: true
        };
      } else {
        return {
          reply: "⚠️ **रमेश जी, सीने में दर्द या भारीपन को बिल्कुल नज़रअंदाज़ न करें!**<br/>कृपया तुरंत आराम से बैठ जाइए, ढीले कपड़े पहनें और धीरे-धीरे गहरी सांस लें। मैंने आपके बेटे सुरेश को आपातकालीन अलर्ट भेज दिया है और डॉक्टर अंजलि को सूचित कर दिया है। कृपया ऊपर दिए गए **लाल 108 आपातकालीन कॉल बटन** को तुरंत दबाएं।",
          alertLevel: 3,
          isEmergency: true
        };
      }
    }

    // 2. High Concern (Dizziness, Headache, Vomiting)
    if (
      q.includes("चक्कर") || q.includes("dizzy") || q.includes("dizziness") ||
      q.includes("सिरदर्द") || q.includes("headache") || q.includes("डोके") ||
      q.includes("उल्टी") || q.includes("vomit") || q.includes("nausea")
    ) {
      if (lang === "mr") {
        return {
          reply: "रमेश जी, चक्कर येणे किंवा डोकेदुखी हे वाढलेल्या रक्तदाबाचे (High BP) लक्षण असू शकते. 🩺<br/>कृपया शांत बसा आणि डोळे मिटून विश्रांती घ्या. थोडे पाणी प्या. आपण आज सकाळची Amlodipine गोळी घेतली आहे का? मी सुरेश यांना आपल्याकडे लक्ष देण्यास सांगितले आहे.",
          alertLevel: 2
        };
      } else if (lang === "en") {
        return {
          reply: "Ramesh-ji, dizziness and headaches are key signs of fluctuating blood pressure. 🩺<br/>Please sit or lie down comfortably, drink a glass of water, and rest your eyes. Did you take your morning Amlodipine 5mg tablet today? I have notified Suresh to check on you.",
          alertLevel: 2
        };
      } else {
        return {
          reply: "रमेश जी, चक्कर आना या सिरदर्द हाई ब्लड प्रेशर का स्पष्ट संकेत हो सकता है। 🩺<br/>कृपया तुरंत आराम से बैठ जाएं, थोड़ा गुनगुना पानी पिएं और आंखें बंद करके आराम करें। क्या आपने आज सुबह की Amlodipine की गोली ली थी? मैंने सुरेश जी को आपके पास ध्यान देने का संदेश भेज दिया है।",
          alertLevel: 2
        };
      }
    }

    // 3. Medications (Adherence, Missed pill, Timings)
    if (
      q.includes("दवाई") || q.includes("medicine") || q.includes("tablet") ||
      q.includes("भूल") || q.includes("miss") || q.includes("गोली") || q.includes("औषध")
    ) {
      if (lang === "mr") {
        return {
          reply: "💊 **रमेश जी, आपली औषधे वेळेवर घेणे अत्यंत महत्त्वाचे आहे!**<br/>• **Amlodipine 5mg** — सकाळी ८:०० वाजता (रक्तदाबासाठी)<br/>• **Metformin 500mg** — सकाळच्या नाश्त्यानंतर (शुगरसाठी)<br/>जर सकाळची गोळी राहिली असेल तर हलका नाश्ता करून आत्ताच एक ग्लास पाण्यासोबत घ्या.",
          alertLevel: 1
        };
      } else if (lang === "en") {
        return {
          reply: "💊 **Ramesh-ji, taking your prescribed medications on schedule is vital!**<br/>• **Amlodipine 5mg** — Morning 8:00 AM (for Blood Pressure)<br/>• **Metformin 500mg** — After breakfast (for Blood Sugar)<br/>If you missed this morning's dose, please take it now with a glass of water and light food.",
          alertLevel: 1
        };
      } else {
        return {
          reply: "💊 **रमेश जी, आपकी दवाइयाँ समय पर लेना आपके स्वास्थ्य की पहली सुरक्षा है!**<br/>• **Amlodipine 5mg** — सुबह 8:00 बजे (ब्लड प्रेशर के लिए)<br/>• **Metformin 500mg** — सुबह नाश्ते के तुरंत बाद (शुगर के लिए)<br/>अगर सुबह की गोली छूट गई है, तो कृपया अभी हल्का सा नाश्ता करके एक गिलास पानी के साथ ले लीजिए।",
          alertLevel: 1
        };
      }
    }

    // 4. Greetings
    if (
      q.includes("hello") || q.includes("hi") || q.includes("hey") ||
      q.includes("नमस्ते") || q.includes("नमस्कार") || q.includes("सुप्रभात") ||
      q.includes("प्रणाम") || q.includes("kaisa") || q.includes("how are you")
    ) {
      if (lang === "mr") {
        return {
          reply: "नमस्कार रमेश जी! 🙏 सुप्रभात! मी आपली २४/७ आरोग्य साथी आशा आहे.<br/>आज आपली प्रकृती कशी आहे? आजचा रक्तदाब आणि रक्तातील साखर तपासली का? मला जरूर सांगा!",
          alertLevel: 0
        };
      } else if (lang === "en") {
        return {
          reply: "Good day, Ramesh-ji! 🙏 Warm greetings from Asha, your 24/7 AI health companion.<br/>How are you feeling today? Did you check your blood pressure and morning glucose? I am here to help you.",
          alertLevel: 0
        };
      } else {
        return {
          reply: "नमस्ते रमेश जी! 🙏 सादर प्रणाम! मैं आपकी स्वास्थ्य साथी आशा हमेशा आपके साथ हूँ।<br/>आज आप कैसा महसूस कर रहे हैं? क्या आपने आज सुबह का ब्लड प्रेशर और शुगर नापा है? मुझे बेझिझक बताएं!",
          alertLevel: 0
        };
      }
    }

    // 5. Diet, Water & Walking
    if (
      q.includes("पानी") || q.includes("water") || q.includes("खाना") ||
      q.includes("diet") || q.includes("food") || q.includes("भोजन") ||
      q.includes("टहल") || q.includes("walk")
    ) {
      if (lang === "mr") {
        return {
          reply: "🥗 **रमेश जी, निरोगी दिनचर्येसाठी आजचे नियम:**<br/>• दिवसातून किमान ७-८ ग्लास कोमट पाणी अवश्य प्या.<br/>• भोजनात मीठ (सोडियम) आणि साखर अत्यंत कमी ठेवा.<br/>• संध्याकाळी बागेत किंवा अंगणात १५-२० मिनिटे हलकी फेरफटका मारा.",
          alertLevel: 0
        };
      } else if (lang === "en") {
        return {
          reply: "🥗 **Ramesh-ji, healthy daily routine guidance:**<br/>• Drink at least 7 to 8 glasses of warm water today to stay well hydrated.<br/>• Keep sodium (salt) low to protect your heart, and avoid processed sugars.<br/>• Aim for a gentle 15–20 minute walk in the garden or courtyard this evening.",
          alertLevel: 0
        };
      } else {
        return {
          reply: "🥗 **रमेश जी, आज के स्वस्थ आहार और दिनचर्या के सुझाव:**<br/>• दिन भर में कम से कम 7 से 8 गिलास गुनगुना पानी ज़रूर पिएं।<br/>• भोजन में नमक की मात्रा कम रखें ताकि बीपी नियंत्रित रहे, और तली-भुनी चीज़ों से बचें।<br/>• शाम को 15 से 20 मिनट के लिए घर के आंगन या पार्क में हल्की सैर ज़रूर करें।",
          alertLevel: 0
        };
      }
    }

    // 6. Loneliness & Emotional Support
    if (
      q.includes("अकेला") || q.includes("lonely") || q.includes("उदासी") ||
      q.includes("मन नहीं") || q.includes("sad") || q.includes("करमत नाही") || q.includes("बात")
    ) {
      if (lang === "mr") {
        return {
          reply: "रमेश जी, मी नेहमी आपल्यासोबत आहे! 💙 एकटे वाटणे स्वाभाविक आहे, पण आपण कधीच एकटे नाही आहात.<br/>मी सुरेश यांना आत्ताच व्हॉट्सॲपवर निरोप पाठवला आहे की त्यांनी आज संध्याकाळी आपल्याशी फोनवर मनमोकळे बोलावे!",
          alertLevel: 0
        };
      } else if (lang === "en") {
        return {
          reply: "Ramesh-ji, I am always right here by your side! 💙 Feeling lonely is very natural, but you are cherished.<br/>I have sent a gentle nudge to Suresh on WhatsApp so he can call and have a wonderful chat with you this evening!",
          alertLevel: 0
        };
      } else {
        return {
          reply: "रमेश जी, मैं हमेशा आपके साथ हूँ! 💙 कभी-कभी अकेलापन या उदासी महसूस होना स्वाभाविक है, पर आप अकेले नहीं हैं।<br/>मैंने सुरेश जी को व्हाट्सएप पर संदेश भेज दिया है कि वे आज शाम को आपको फोन करके लंबी बात करें। आप अपने मनपसंद पुराने गीत भी सुन सकते हैं!",
          alertLevel: 0
        };
      }
    }

    // 7. Doctor & Hospital Info
    if (
      q.includes("डॉक्टर") || q.includes("doctor") || q.includes("appointment") ||
      q.includes("clinic") || q.includes("अस्पताल") || q.includes("apollo") || q.includes("anjali")
    ) {
      if (lang === "mr") {
        return {
          reply: "🩺 **डॉक्टरांशी भेट (Next Consultation):**<br/>डॉ. अंजली शर्मा (अपोलो हॉस्पिटल, नोएडा) यांच्यासोबत डे ३० रोजी आपली तपासणी नियोजित आहे. गेल्या ३० दिवसांचा संपूर्ण ईएचआर आणि वाइटल्स अहवाल क्लिनिककडे तयार आहे.",
          alertLevel: 0
        };
      } else if (lang === "en") {
        return {
          reply: "🩺 **Doctor Consultation Details:**<br/>Your follow-up with Dr. Anjali Sharma (Apollo Hospital, Noida) is scheduled for Day 30. Your complete 30-day vitals trend, medication compliance, and health summary are prepared for her review.",
          alertLevel: 0
        };
      } else {
        return {
          reply: "🩺 **डॉक्टर परामर्श जानकारी:**<br/>डॉ. अंजलि शर्मा (अपोलो हॉस्पिटल, नोएडा) के साथ आपका अगला चेकअप डे 30 को निर्धारित है। आपके पिछले 30 दिनों का पूरा वाइटल्स रिकॉर्ड और हेल्थ रिपोर्ट मैंने डॉक्टर साहब के लिए तैयार कर दी है।",
          alertLevel: 0
        };
      }
    }

    // 8. General Health / Vitals Query
    if (lang === "mr") {
      return {
        reply: "नमस्कार रमेश जी! 🙏 मी आपली माहिती आरोग्य नोंदवहीत सुरक्षित केली आहे.<br/>वेळेवर औषधे घ्या, पुरेसे पाणी प्या आणि कोणतीही शंका असल्यास मला निःसंकोचपणे विचारा!",
        alertLevel: 0
      };
    } else if (lang === "en") {
      return {
        reply: "Hello Ramesh-ji! 🙏 I have carefully noted this in your daily care record.<br/>Please stay hydrated, follow your routine, and let me know if you feel any fatigue, pain, or discomfort!",
        alertLevel: 0
      };
    } else {
      return {
        reply: "नमस्ते रमेश जी! 🙏 मैंने आपकी बात को ध्यानपूर्वक समझकर आपके दैनिक हेल्थ रिकॉर्ड में दर्ज कर लिया है।<br/>समय पर अपनी दवाइयाँ लेते रहें, पानी पीते रहें और कोई भी असुविधा या दर्द महसूस हो तो मुझे तुरंत बताएं!",
        alertLevel: 0
      };
    }
  }
};

if (typeof module !== "undefined" && module.exports) {
  module.exports = AshaAI;
}

