import i18n from "i18next";
import { initReactI18next } from "react-i18next";

const resources = {
  en: {
    translation: {

      /* =================================================
         LANGUAGE
      ================================================= */

      language: "Language",


      /* =================================================
         HEADER
      ================================================= */

      systemLabel: "HYPERLOCAL WATERLOGGING RISK SYSTEM",

      waterlogging: "Waterlogging",
      riskIntelligence: "Risk Intelligence",

      heroDescription:
        "AI-powered road-waterlogging risk monitoring.",

      liveWeather: "LIVE WEATHER",
      locations: "LOCATIONS",
      currentRisk: "CURRENT RISK",

      refreshRisk: "Refresh Risk",
      updating: "Updating...",


      /* =================================================
         LIVE OVERVIEW
      ================================================= */

      liveOverview: "LIVE OVERVIEW",

      clickCardToFilter:
        "Click a card to filter the map",

      allLocations: "All Locations",
      lowRisk: "Low Risk",
      moderateRisk: "Moderate Risk",
      highRisk: "High Risk",
      extremeRisk: "Extreme Risk",

      active: "ACTIVE",


      /* =================================================
         STAKEHOLDER
      ================================================= */

      personalizedGuidance:
        "PERSONALIZED GUIDANCE",

      whoAreYou: "Who are you?",

      selectRole:
        "Select your role to receive relevant current-risk precautions and actions.",

      resident: "Resident",
      ngoVolunteer: "NGO / Volunteer",
      farmer: "Farmer",
      localAuthority: "Local Authority",


      /* =================================================
         LOCATION SEARCH
      ================================================= */

      locationSearch: "LOCATION SEARCH",

      whereAreYouGoing: "Where are you going?",

      selectDestinationDescription:
        "Select a destination to see nearby waterlogging risk.",

      selectPuneArea:
        "Select a Pune / PMC area",

      detectingLocation:
        "Detecting location...",

      locationUnavailable:
        "Location unavailable",

      currentLocationDetected:
        "Current location detected",


      /* =================================================
         MAP
      ================================================= */

      geospatialView: "GEOSPATIAL VIEW",

      hyperlocalRiskMap:
        "Hyperlocal Risk Map",

      livePredictedRisk:
        "Live predicted waterlogging risk across monitored locations.",

      showingRiskLocations:
        "Showing {{risk}}-risk locations.",

      live: "LIVE",

      riskLevel: "Risk Level",

      yourLocation: "Your location",

      destination: "Destination",

      showing:
        "Showing",

      of:
        "of",

      locationsLabel:
        "locations",


      /* =================================================
         MAP POPUPS
      ================================================= */

      yourCurrentLocation:
        "Your Current Location",

      nearbyArea:
        "Nearby Area",

      risk:
        "Risk",

      score:
        "Score",

      samplingPoint:
        "Sampling Point",

      riskScore:
        "Risk Score",

      type:
        "Type",


      /* =================================================
         DESTINATION / RISK PANEL
      ================================================= */

      yourLocationPanel:
        "YOUR LOCATION",

      destinationPanel:
        "DESTINATION",

      selectDestination:
        "Select a destination",

      chooseAreaDescription:
        "Choose an area above to see its current nearby risk.",

      detectingCurrentRisk:
        "Detecting current location risk...",

      riskDataUnavailable:
        "Risk data is currently unavailable.",


      /* =================================================
         GUIDANCE
      ================================================= */

      whatThisMeans:
        "What this means",

      residentGuidance:
        "Resident Guidance",

      ngoActions:
        "NGO / Volunteer Actions",

      farmerPrecautions:
        "Farmer Precautions",

      authorityActions:
        "Authority Actions",

      riskInformationUnavailable:
        "Risk information is currently unavailable.",


      /* =================================================
         RESIDENT GUIDANCE
      ================================================= */

      residentLowTitle:
        "Conditions are currently favorable.",

      residentLow1:
        "Normal travel can continue.",

      residentLow2:
        "Stay aware of sudden local water accumulation.",

      residentLow3:
        "Monitor weather updates.",


      residentModerateTitle:
        "Some waterlogging may occur in vulnerable areas.",

      residentModerate1:
        "Use extra caution while travelling.",

      residentModerate2:
        "Avoid known low-lying and poorly drained roads.",

      residentModerate3:
        "Monitor rainfall and local alerts.",


      residentHighTitle:
        "Heavy rainfall and waterlogging are possible.",

      residentHigh1:
        "Avoid unnecessary travel.",

      residentHigh2:
        "Avoid low-lying roads and underpasses.",

      residentHigh3:
        "Use safer alternate routes where possible.",

      residentHigh4:
        "Do not enter visibly flooded roads.",


      residentExtremeTitle:
        "Dangerous waterlogging may occur. Prioritize safety.",

      residentExtreme1:
        "Avoid unnecessary travel.",

      residentExtreme2:
        "Do not walk, ride or drive through flooded roads.",

      residentExtreme3:
        "Move to a safer location if water levels rise.",

      residentExtreme4:
        "Follow local authority instructions.",


      /* =================================================
         NGO GUIDANCE
      ================================================= */

      ngoLowTitle:
        "Routine community monitoring is sufficient.",

      ngoLow1:
        "Keep communication channels ready.",

      ngoLow2:
        "Continue monitoring vulnerable communities.",


      ngoModerateTitle:
        "Prepare for possible local waterlogging.",

      ngoModerate1:
        "Prepare community alert messages.",

      ngoModerate2:
        "Check vulnerable households in affected areas.",

      ngoModerate3:
        "Keep volunteers informed.",


      ngoHighTitle:
        "Community-level preparedness should be increased.",

      ngoHigh1:
        "Activate community communication.",

      ngoHigh2:
        "Check on vulnerable residents.",

      ngoHigh3:
        "Prepare volunteers for assistance.",

      ngoHigh4:
        "Coordinate with local response teams.",


      ngoExtremeTitle:
        "Emergency community response may be required.",

      ngoExtreme1:
        "Activate emergency volunteer teams.",

      ngoExtreme2:
        "Coordinate relief and shelter support.",

      ngoExtreme3:
        "Prioritize vulnerable communities.",

      ngoExtreme4:
        "Coordinate closely with local authorities.",


      /* =================================================
         FARMER GUIDANCE
      ================================================= */

      farmerLowTitle:
        "Normal agricultural activities can continue.",

      farmerLow1:
        "Monitor rainfall and drainage conditions.",


      farmerModerateTitle:
        "Wet conditions may affect field operations.",

      farmerModerate1:
        "Inspect field drainage.",

      farmerModerate2:
        "Avoid unnecessary machinery movement.",

      farmerModerate3:
        "Monitor livestock and field conditions.",


      farmerHighTitle:
        "Heavy rainfall may affect agricultural operations.",

      farmerHigh1:
        "Check and maintain field drainage where safe.",

      farmerHigh2:
        "Protect livestock and equipment.",

      farmerHigh3:
        "Avoid unnecessary machinery movement.",

      farmerHigh4:
        "Move critical assets away from low-lying areas.",


      farmerExtremeTitle:
        "Agricultural assets may be at serious risk.",

      farmerExtreme1:
        "Move livestock to safer ground.",

      farmerExtreme2:
        "Protect critical equipment and materials.",

      farmerExtreme3:
        "Restrict access to severely waterlogged fields.",

      farmerExtreme4:
        "Monitor rapidly rising water levels.",


      /* =================================================
         AUTHORITY GUIDANCE
      ================================================= */

      authorityLowTitle:
        "Routine monitoring is appropriate.",

      authorityLow1:
        "Continue monitoring vulnerable locations.",

      authorityLow2:
        "Maintain normal drainage preparedness.",


      authorityModerateTitle:
        "Preventive monitoring should be increased.",

      authorityModerate1:
        "Inspect vulnerable drainage points.",

      authorityModerate2:
        "Monitor recurring waterlogging locations.",

      authorityModerate3:
        "Prepare response resources.",


      authorityHighTitle:
        "Active preparedness measures are recommended.",

      authorityHigh1:
        "Prioritize drainage clearance.",

      authorityHigh2:
        "Monitor high-risk roads.",

      authorityHigh3:
        "Prepare traffic diversions.",

      authorityHigh4:
        "Deploy pumps or response resources where required.",


      authorityExtremeTitle:
        "Emergency response measures may be required.",

      authorityExtreme1:
        "Activate emergency response procedures.",

      authorityExtreme2:
        "Close dangerous roads where necessary.",

      authorityExtreme3:
        "Deploy drainage and pumping resources.",

      authorityExtreme4:
        "Coordinate evacuation where required.",

      authorityExtreme5:
        "Continuously monitor critical locations.",


      /* =================================================
         HOW IT WORKS
      ================================================= */

      systemInformation:
        "SYSTEM INFORMATION",

      howSystemWorks:
        "How does the system work?",


      weatherRainfall:
        "Weather & Rainfall",

      weatherRainfallDescription:
        "Current rainfall, rainfall persistence and recent weather conditions are analyzed.",


      locationConditions:
        "Location Conditions",

      locationConditionsDescription:
        "Terrain, drainage, built-up area, road characteristics and other local factors are included.",


      aiRiskPrediction:
        "AI Risk Prediction",

      aiRiskPredictionDescription:
        "The prediction model estimates a continuous waterlogging risk score for each monitored point.",


      riskGuidance:
        "Risk & Guidance",

      riskGuidanceDescription:
        "Scores are presented as Low, Moderate, High or Extreme with practical safety guidance.",


      /* =================================================
         LOADING
      ================================================= */

      hyperlocalWaterloggingRisk:
        "Hyperlocal Waterlogging Risk",

      connectingLiveRisk:
        "Connecting to live risk intelligence...",


      /* =================================================
         ERROR
      ================================================= */

      backendConnectionError:
        "Backend Connection Error",

      tryAgain:
        "Try Again",

      backendConnectionMessage:
        "Could not connect to the live waterlogging-risk backend.",

      refreshConnectionError:
        "Could not refresh live waterlogging-risk data.",


      /* =================================================
         FOOTER
      ================================================= */

      footerTitle:
        "Hyperlocal Waterlogging Risk Monitoring System",

      footerTechnology:
        "AI-powered spatial risk intelligence • FastAPI • React • Leaflet",

    },
  },


  /* =====================================================
     HINDI
  ===================================================== */

  hi: {
    translation: {

      language: "भाषा",

      systemLabel:
        "हाइपरलोकल जलभराव जोखिम प्रणाली",

      waterlogging:
        "जलभराव",

      riskIntelligence:
        "जोखिम जानकारी",

      heroDescription:
        "AI-संचालित सड़क जलभराव जोखिम निगरानी।",

      liveWeather:
        "लाइव मौसम",

      locations:
        "स्थान",

      currentRisk:
        "वर्तमान जोखिम",

      refreshRisk:
        "जोखिम अपडेट करें",

      updating:
        "अपडेट हो रहा है...",


      liveOverview:
        "लाइव अवलोकन",

      clickCardToFilter:
        "मानचित्र को फ़िल्टर करने के लिए कार्ड पर क्लिक करें",

      allLocations:
        "सभी स्थान",

      lowRisk:
        "कम जोखिम",

      moderateRisk:
        "मध्यम जोखिम",

      highRisk:
        "उच्च जोखिम",

      extremeRisk:
        "अत्यधिक जोखिम",

      active:
        "सक्रिय",


      personalizedGuidance:
        "व्यक्तिगत मार्गदर्शन",

      whoAreYou:
        "आप कौन हैं?",

      selectRole:
        "अपने वर्तमान जोखिम के अनुसार उचित सावधानियाँ और कार्य देखने के लिए अपनी भूमिका चुनें।",

      resident:
        "निवासी",

      ngoVolunteer:
        "NGO / स्वयंसेवक",

      farmer:
        "किसान",

      localAuthority:
        "स्थानीय प्राधिकरण",


      locationSearch:
        "स्थान खोज",

      whereAreYouGoing:
        "आप कहाँ जा रहे हैं?",

      selectDestinationDescription:
        "अपने आसपास के जलभराव जोखिम को देखने के लिए गंतव्य चुनें।",

      selectPuneArea:
        "पुणे / PMC क्षेत्र चुनें",

      detectingLocation:
        "स्थान का पता लगाया जा रहा है...",

      locationUnavailable:
        "स्थान उपलब्ध नहीं है",

      currentLocationDetected:
        "वर्तमान स्थान का पता चल गया है",


      geospatialView:
        "भौगोलिक दृश्य",

      hyperlocalRiskMap:
        "हाइपरलोकल जोखिम मानचित्र",

      livePredictedRisk:
        "निगरानी किए गए स्थानों में अनुमानित वर्तमान जलभराव जोखिम।",

      showingRiskLocations:
        "{{risk}} जोखिम वाले स्थान दिखाए जा रहे हैं।",

      live:
        "लाइव",

      riskLevel:
        "जोखिम स्तर",

      yourLocation:
        "आपका स्थान",

      destination:
        "गंतव्य",

      showing:
        "दिखाए जा रहे हैं",

      of:
        "में से",

      locationsLabel:
        "स्थान",


      yourCurrentLocation:
        "आपका वर्तमान स्थान",

      nearbyArea:
        "निकटतम क्षेत्र",

      risk:
        "जोखिम",

      score:
        "स्कोर",

      samplingPoint:
        "सैंपलिंग पॉइंट",

      riskScore:
        "जोखिम स्कोर",

      type:
        "प्रकार",


      yourLocationPanel:
        "आपका स्थान",

      destinationPanel:
        "गंतव्य",

      selectDestination:
        "गंतव्य चुनें",

      chooseAreaDescription:
        "वर्तमान निकटतम जोखिम देखने के लिए ऊपर कोई क्षेत्र चुनें।",

      detectingCurrentRisk:
        "वर्तमान स्थान के जोखिम का पता लगाया जा रहा है...",

      riskDataUnavailable:
        "जोखिम डेटा वर्तमान में उपलब्ध नहीं है।",


      whatThisMeans:
        "इसका क्या अर्थ है",

      residentGuidance:
        "निवासी मार्गदर्शन",

      ngoActions:
        "NGO / स्वयंसेवक कार्रवाई",

      farmerPrecautions:
        "किसान सावधानियाँ",

      authorityActions:
        "प्राधिकरण कार्रवाई",

      riskInformationUnavailable:
        "जोखिम की जानकारी वर्तमान में उपलब्ध नहीं है।",


      residentLowTitle:
        "वर्तमान परिस्थितियाँ अनुकूल हैं।",

      residentLow1:
        "सामान्य यात्रा जारी रखी जा सकती है।",

      residentLow2:
        "अचानक स्थानीय जलभराव से सावधान रहें।",

      residentLow3:
        "मौसम संबंधी अपडेट देखते रहें।",


      residentModerateTitle:
        "संवेदनशील क्षेत्रों में कुछ जलभराव हो सकता है।",

      residentModerate1:
        "यात्रा करते समय अतिरिक्त सावधानी बरतें।",

      residentModerate2:
        "ज्ञात निचले और खराब जलनिकासी वाले मार्गों से बचें।",

      residentModerate3:
        "वर्षा और स्थानीय चेतावनियों पर नजर रखें।",


      residentHighTitle:
        "भारी वर्षा और जलभराव की संभावना है।",

      residentHigh1:
        "अनावश्यक यात्रा से बचें।",

      residentHigh2:
        "निचले क्षेत्रों की सड़कों और अंडरपास से बचें।",

      residentHigh3:
        "जहाँ संभव हो सुरक्षित वैकल्पिक मार्गों का उपयोग करें।",

      residentHigh4:
        "दिखाई देने वाले बाढ़ग्रस्त मार्गों में प्रवेश न करें।",


      residentExtremeTitle:
        "खतरनाक जलभराव हो सकता है। सुरक्षा को प्राथमिकता दें।",

      residentExtreme1:
        "अनावश्यक यात्रा से बचें।",

      residentExtreme2:
        "बाढ़ग्रस्त सड़कों पर पैदल, बाइक या वाहन से न जाएँ।",

      residentExtreme3:
        "जलस्तर बढ़ने पर सुरक्षित स्थान पर जाएँ।",

      residentExtreme4:
        "स्थानीय प्राधिकरण के निर्देशों का पालन करें।",


      ngoLowTitle:
        "नियमित सामुदायिक निगरानी पर्याप्त है.",

      ngoLow1:
        "संचार माध्यम तैयार रखें।",

      ngoLow2:
        "संवेदनशील समुदायों की निगरानी जारी रखें।",


      ngoModerateTitle:
        "संभावित स्थानीय जलभराव के लिए तैयारी करें।",

      ngoModerate1:
        "सामुदायिक चेतावनी संदेश तैयार करें।",

      ngoModerate2:
        "प्रभावित क्षेत्रों में संवेदनशील परिवारों की स्थिति जाँचें।",

      ngoModerate3:
        "स्वयंसेवकों को सूचित रखें।",


      ngoHighTitle:
        "सामुदायिक स्तर की तैयारी बढ़ाई जानी चाहिए।",

      ngoHigh1:
        "सामुदायिक संचार सक्रिय करें।",

      ngoHigh2:
        "संवेदनशील निवासियों की स्थिति जाँचें।",

      ngoHigh3:
        "सहायता के लिए स्वयंसेवकों को तैयार रखें।",

      ngoHigh4:
        "स्थानीय प्रतिक्रिया टीमों के साथ समन्वय करें।",


      ngoExtremeTitle:
        "आपातकालीन सामुदायिक प्रतिक्रिया आवश्यक हो सकती है।",

      ngoExtreme1:
        "आपातकालीन स्वयंसेवक टीमों को सक्रिय करें।",

      ngoExtreme2:
        "राहत और आश्रय सहायता का समन्वय करें।",

      ngoExtreme3:
        "संवेदनशील समुदायों को प्राथमिकता दें।",

      ngoExtreme4:
        "स्थानीय प्राधिकरणों के साथ निकट समन्वय करें।",


      farmerLowTitle:
        "सामान्य कृषि गतिविधियाँ जारी रखी जा सकती हैं।",

      farmerLow1:
        "वर्षा और जलनिकासी की स्थिति पर नजर रखें।",


      farmerModerateTitle:
        "गीली परिस्थितियाँ खेत के कार्यों को प्रभावित कर सकती हैं।",

      farmerModerate1:
        "खेत की जलनिकासी की जाँच करें।",

      farmerModerate2:
        "अनावश्यक मशीनरी की आवाजाही से बचें।",

      farmerModerate3:
        "पशुधन और खेत की स्थिति पर नजर रखें।",


      farmerHighTitle:
        "भारी वर्षा कृषि गतिविधियों को प्रभावित कर सकती है।",

      farmerHigh1:
        "जहाँ सुरक्षित हो वहाँ खेत की जलनिकासी की जाँच और रखरखाव करें।",

      farmerHigh2:
        "पशुधन और उपकरणों की सुरक्षा करें।",

      farmerHigh3:
        "अनावश्यक मशीनरी की आवाजाही से बचें।",

      farmerHigh4:
        "महत्वपूर्ण संसाधनों को निचले क्षेत्रों से दूर ले जाएँ।",


      farmerExtremeTitle:
        "कृषि संसाधनों पर गंभीर जोखिम हो सकता है।",

      farmerExtreme1:
        "पशुधन को सुरक्षित ऊँचे स्थान पर ले जाएँ।",

      farmerExtreme2:
        "महत्वपूर्ण उपकरणों और सामग्रियों की सुरक्षा करें।",

      farmerExtreme3:
        "अत्यधिक जलभराव वाले खेतों में प्रवेश सीमित करें।",

      farmerExtreme4:
        "तेजी से बढ़ते जलस्तर पर नजर रखें।",


      authorityLowTitle:
        "नियमित निगरानी उचित है।",

      authorityLow1:
        "संवेदनशील स्थानों की निगरानी जारी रखें।",

      authorityLow2:
        "सामान्य जलनिकासी तैयारी बनाए रखें।",


      authorityModerateTitle:
        "रोकथाम संबंधी निगरानी बढ़ाई जानी चाहिए।",

      authorityModerate1:
        "संवेदनशील जलनिकासी बिंदुओं का निरीक्षण करें।",

      authorityModerate2:
        "बार-बार जलभराव वाले स्थानों की निगरानी करें।",

      authorityModerate3:
        "प्रतिक्रिया संसाधनों को तैयार रखें।",


      authorityHighTitle:
        "सक्रिय तैयारी के उपाय सुझाए जाते हैं।",

      authorityHigh1:
        "जलनिकासी की सफाई को प्राथमिकता दें।",

      authorityHigh2:
        "उच्च जोखिम वाली सड़कों की निगरानी करें।",

      authorityHigh3:
        "यातायात के वैकल्पिक मार्गों की तैयारी करें।",

      authorityHigh4:
        "आवश्यकतानुसार पंप और प्रतिक्रिया संसाधन तैनात करें।",


      authorityExtremeTitle:
        "आपातकालीन प्रतिक्रिया उपाय आवश्यक हो सकते हैं।",

      authorityExtreme1:
        "आपातकालीन प्रतिक्रिया प्रक्रियाएँ सक्रिय करें।",

      authorityExtreme2:
        "आवश्यकतानुसार खतरनाक सड़कों को बंद करें।",

      authorityExtreme3:
        "जलनिकासी और पंपिंग संसाधन तैनात करें।",

      authorityExtreme4:
        "जहाँ आवश्यक हो निकासी का समन्वय करें।",

      authorityExtreme5:
        "महत्वपूर्ण स्थानों की लगातार निगरानी करें।",


      systemInformation:
        "सिस्टम जानकारी",

      howSystemWorks:
        "सिस्टम कैसे काम करता है?",

      weatherRainfall:
        "मौसम और वर्षा",

      weatherRainfallDescription:
        "वर्तमान वर्षा, वर्षा की निरंतरता और हाल की मौसम स्थितियों का विश्लेषण किया जाता है।",

      locationConditions:
        "स्थान की परिस्थितियाँ",

      locationConditionsDescription:
        "भू-भाग, जलनिकासी, निर्मित क्षेत्र, सड़क की विशेषताएँ और अन्य स्थानीय कारकों को शामिल किया जाता है।",

      aiRiskPrediction:
        "AI जोखिम पूर्वानुमान",

      aiRiskPredictionDescription:
        "मॉडल प्रत्येक निगरानी बिंदु के लिए निरंतर जलभराव जोखिम स्कोर का अनुमान लगाता है।",

      riskGuidance:
        "जोखिम और मार्गदर्शन",

      riskGuidanceDescription:
        "स्कोर को कम, मध्यम, उच्च या अत्यधिक जोखिम के रूप में प्रस्तुत किया जाता है और व्यावहारिक सुरक्षा मार्गदर्शन दिया जाता है।",


      hyperlocalWaterloggingRisk:
        "हाइपरलोकल जलभराव जोखिम",

      connectingLiveRisk:
        "लाइव जोखिम जानकारी से कनेक्ट किया जा रहा है...",


      backendConnectionError:
        "बैकएंड कनेक्शन त्रुटि",

      tryAgain:
        "फिर प्रयास करें",

      backendConnectionMessage:
        "लाइव जलभराव जोखिम बैकएंड से कनेक्ट नहीं हो सका।",

      refreshConnectionError:
        "लाइव जलभराव जोखिम डेटा अपडेट नहीं किया जा सका।",


      footerTitle:
        "हाइपरलोकल जलभराव जोखिम निगरानी प्रणाली",

      footerTechnology:
        "AI-संचालित स्थानिक जोखिम जानकारी • FastAPI • React • Leaflet",

    },
  },


  /* =====================================================
     MARATHI
  ===================================================== */

  mr: {
    translation: {

      language: "भाषा",

      systemLabel:
        "हायपरलोकल रस्ते जलसाचणे जोखीम प्रणाली",

      waterlogging:
        "जलसाचणे",

      riskIntelligence:
        "जोखीम माहिती",

      heroDescription:
        "AI-आधारित रस्ते जलसाचणे जोखीम निरीक्षण.",

      liveWeather:
        "लाईव्ह हवामान",

      locations:
        "ठिकाणे",

      currentRisk:
        "सध्याचा धोका",

      refreshRisk:
        "जोखीम अपडेट करा",

      updating:
        "अपडेट होत आहे...",


      liveOverview:
        "लाईव्ह आढावा",

      clickCardToFilter:
        "नकाशा फिल्टर करण्यासाठी कार्डवर क्लिक करा",

      allLocations:
        "सर्व ठिकाणे",

      lowRisk:
        "कमी धोका",

      moderateRisk:
        "मध्यम धोका",

      highRisk:
        "उच्च धोका",

      extremeRisk:
        "अत्यंत धोका",

      active:
        "सक्रिय",


      personalizedGuidance:
        "वैयक्तिक मार्गदर्शन",

      whoAreYou:
        "तुम्ही कोण आहात?",

      selectRole:
        "तुमच्या भूमिकेनुसार सध्याच्या जोखमीसाठी योग्य काळजी आणि कृती पाहण्यासाठी भूमिका निवडा.",

      resident:
        "रहिवासी",

      ngoVolunteer:
        "NGO / स्वयंसेवक",

      farmer:
        "शेतकरी",

      localAuthority:
        "स्थानिक प्राधिकरण",


      locationSearch:
        "स्थान शोध",

      whereAreYouGoing:
        "तुम्ही कुठे जात आहात?",

      selectDestinationDescription:
        "जवळपासचा जलसाचण्याचा धोका पाहण्यासाठी गंतव्यस्थान निवडा.",

      selectPuneArea:
        "पुणे / PMC क्षेत्र निवडा",

      detectingLocation:
        "स्थान शोधले जात आहे...",

      locationUnavailable:
        "स्थान उपलब्ध नाही",

      currentLocationDetected:
        "सध्याचे स्थान शोधले गेले आहे",


      geospatialView:
        "भौगोलिक दृश्य",

      hyperlocalRiskMap:
        "हायपरलोकल जोखीम नकाशा",

      livePredictedRisk:
        "निगराणी केलेल्या ठिकाणांवरील सध्याच्या जलसाचण्याच्या जोखमीचा अंदाज.",

      showingRiskLocations:
        "{{risk}} जोखीम असलेली ठिकाणे दाखवली जात आहेत.",

      live:
        "लाईव्ह",

      riskLevel:
        "जोखीम पातळी",

      yourLocation:
        "तुमचे स्थान",

      destination:
        "गंतव्यस्थान",

      showing:
        "दाखवत आहे",

      of:
        "पैकी",

      locationsLabel:
        "ठिकाणे",


      yourCurrentLocation:
        "तुमचे सध्याचे स्थान",

      nearbyArea:
        "जवळचा परिसर",

      risk:
        "जोखीम",

      score:
        "स्कोअर",

      samplingPoint:
        "सॅम्पलिंग पॉइंट",

      riskScore:
        "जोखीम स्कोअर",

      type:
        "प्रकार",


      yourLocationPanel:
        "तुमचे स्थान",

      destinationPanel:
        "गंतव्यस्थान",

      selectDestination:
        "गंतव्यस्थान निवडा",

      chooseAreaDescription:
        "सध्याचा जवळचा धोका पाहण्यासाठी वरून एखादा परिसर निवडा.",

      detectingCurrentRisk:
        "सध्याच्या स्थानाचा धोका शोधला जात आहे...",

      riskDataUnavailable:
        "जोखीम माहिती सध्या उपलब्ध नाही.",


      whatThisMeans:
        "याचा अर्थ काय",

      residentGuidance:
        "रहिवासी मार्गदर्शन",

      ngoActions:
        "NGO / स्वयंसेवक कृती",

      farmerPrecautions:
        "शेतकरी काळजी",

      authorityActions:
        "प्राधिकरण कृती",

      riskInformationUnavailable:
        "जोखीम माहिती सध्या उपलब्ध नाही.",


      residentLowTitle:
        "सध्याची परिस्थिती अनुकूल आहे.",

      residentLow1:
        "सामान्य प्रवास सुरू ठेवता येऊ शकतो.",

      residentLow2:
        "अचानक स्थानिक जलसाचण्याबाबत सतर्क रहा.",

      residentLow3:
        "हवामानाचे अपडेट पाहत रहा.",


      residentModerateTitle:
        "संवेदनशील भागात काही प्रमाणात जलसाचणे होऊ शकते.",

      residentModerate1:
        "प्रवास करताना अतिरिक्त काळजी घ्या.",

      residentModerate2:
        "सखल आणि खराब जलनिस्सारण असलेल्या रस्त्यांपासून दूर रहा.",

      residentModerate3:
        "पाऊस आणि स्थानिक इशाऱ्यांवर लक्ष ठेवा.",


      residentHighTitle:
        "मुसळधार पाऊस आणि जलसाचण्याची शक्यता आहे.",

      residentHigh1:
        "अनावश्यक प्रवास टाळा.",

      residentHigh2:
        "सखल भागातील रस्ते आणि अंडरपास टाळा.",

      residentHigh3:
        "शक्य असल्यास सुरक्षित पर्यायी मार्ग वापरा.",

      residentHigh4:
        "दिसत असलेल्या पूरग्रस्त रस्त्यावर प्रवेश करू नका.",


      residentExtremeTitle:
        "धोकादायक जलसाचणे होऊ शकते. सुरक्षिततेला प्राधान्य द्या.",

      residentExtreme1:
        "अनावश्यक प्रवास टाळा.",

      residentExtreme2:
        "पूरग्रस्त रस्त्यावर पायी, दुचाकीने किंवा वाहनाने जाऊ नका.",

      residentExtreme3:
        "पाण्याची पातळी वाढल्यास सुरक्षित ठिकाणी जा.",

      residentExtreme4:
        "स्थानिक प्राधिकरणांच्या सूचनांचे पालन करा.",


      ngoLowTitle:
        "नियमित समुदाय निरीक्षण पुरेसे आहे.",

      ngoLow1:
        "संपर्काची साधने तयार ठेवा.",

      ngoLow2:
        "संवेदनशील समुदायांचे निरीक्षण सुरू ठेवा.",


      ngoModerateTitle:
        "संभाव्य स्थानिक जलसाचण्यासाठी तयारी करा.",

      ngoModerate1:
        "समुदायासाठी इशारा संदेश तयार ठेवा.",

      ngoModerate2:
        "प्रभावित भागातील संवेदनशील कुटुंबांची स्थिती तपासा.",

      ngoModerate3:
        "स्वयंसेवकांना माहिती देत रहा.",


      ngoHighTitle:
        "समुदाय स्तरावरील तयारी वाढवणे आवश्यक आहे.",

      ngoHigh1:
        "समुदाय संपर्क व्यवस्था सक्रिय करा.",

      ngoHigh2:
        "संवेदनशील रहिवाशांची विचारपूस करा.",

      ngoHigh3:
        "मदतीसाठी स्वयंसेवक तयार ठेवा.",

      ngoHigh4:
        "स्थानिक प्रतिसाद पथकांशी समन्वय साधा.",


      ngoExtremeTitle:
        "आपत्कालीन समुदाय प्रतिसादाची आवश्यकता असू शकते.",

      ngoExtreme1:
        "आपत्कालीन स्वयंसेवक पथके सक्रिय करा.",

      ngoExtreme2:
        "मदत आणि निवारा व्यवस्थेचा समन्वय करा.",

      ngoExtreme3:
        "संवेदनशील समुदायांना प्राधान्य द्या.",

      ngoExtreme4:
        "स्थानिक प्राधिकरणांशी जवळून समन्वय साधा.",


      farmerLowTitle:
        "सामान्य शेतीची कामे सुरू ठेवता येऊ शकतात.",

      farmerLow1:
        "पाऊस आणि जलनिस्सारणाच्या परिस्थितीवर लक्ष ठेवा.",


      farmerModerateTitle:
        "ओलसर परिस्थितीमुळे शेतातील कामांवर परिणाम होऊ शकतो.",

      farmerModerate1:
        "शेतातील जलनिस्सारण तपासा.",

      farmerModerate2:
        "अनावश्यक यंत्रसामग्रीची हालचाल टाळा.",

      farmerModerate3:
        "पशुधन आणि शेताच्या परिस्थितीवर लक्ष ठेवा.",


      farmerHighTitle:
        "मुसळधार पावसामुळे शेतीच्या कामांवर परिणाम होऊ शकतो.",

      farmerHigh1:
        "सुरक्षित असल्यास शेतातील जलनिस्सारण तपासा आणि देखभाल करा.",

      farmerHigh2:
        "पशुधन आणि उपकरणांचे संरक्षण करा.",

      farmerHigh3:
        "अनावश्यक यंत्रसामग्रीची हालचाल टाळा.",

      farmerHigh4:
        "महत्त्वाची साधने सखल भागांपासून दूर हलवा.",


      farmerExtremeTitle:
        "शेतीच्या साधनसंपत्तीवर गंभीर धोका निर्माण होऊ शकतो.",

      farmerExtreme1:
        "पशुधन सुरक्षित उंच ठिकाणी हलवा.",

      farmerExtreme2:
        "महत्त्वाची उपकरणे आणि साहित्य सुरक्षित ठेवा.",

      farmerExtreme3:
        "अत्यंत जलसाचलेल्या शेतांमध्ये प्रवेश मर्यादित करा.",

      farmerExtreme4:
        "वेगाने वाढणाऱ्या पाण्याच्या पातळीवर लक्ष ठेवा.",


      authorityLowTitle:
        "नियमित निरीक्षण योग्य आहे.",

      authorityLow1:
        "संवेदनशील ठिकाणांचे निरीक्षण सुरू ठेवा.",

      authorityLow2:
        "सामान्य जलनिस्सारणाची तयारी कायम ठेवा.",


      authorityModerateTitle:
        "प्रतिबंधात्मक निरीक्षण वाढवावे.",

      authorityModerate1:
        "संवेदनशील जलनिस्सारण ठिकाणांची तपासणी करा.",

      authorityModerate2:
        "वारंवार जलसाचणाऱ्या ठिकाणांचे निरीक्षण करा.",

      authorityModerate3:
        "प्रतिसादासाठी आवश्यक साधने तयार ठेवा.",


      authorityHighTitle:
        "सक्रिय तयारीचे उपाय आवश्यक आहेत.",

      authorityHigh1:
        "जलनिस्सारणाची साफसफाई प्राधान्याने करा.",

      authorityHigh2:
        "उच्च जोखीम असलेल्या रस्त्यांवर लक्ष ठेवा.",

      authorityHigh3:
        "वाहतुकीसाठी पर्यायी मार्गांची तयारी करा.",

      authorityHigh4:
        "आवश्यकतेनुसार पंप किंवा प्रतिसाद साधने तैनात करा.",


      authorityExtremeTitle:
        "आपत्कालीन प्रतिसाद उपायांची आवश्यकता असू शकते.",

      authorityExtreme1:
        "आपत्कालीन प्रतिसाद प्रक्रिया सक्रिय करा.",

      authorityExtreme2:
        "आवश्यकतेनुसार धोकादायक रस्ते बंद करा.",

      authorityExtreme3:
        "जलनिस्सारण आणि पंपिंग साधने तैनात करा.",

      authorityExtreme4:
        "आवश्यकतेनुसार स्थलांतराचे समन्वय करा.",

      authorityExtreme5:
        "महत्त्वाच्या ठिकाणांचे सतत निरीक्षण करा.",


      systemInformation:
        "प्रणाली माहिती",

      howSystemWorks:
        "प्रणाली कशी कार्य करते?",

      weatherRainfall:
        "हवामान आणि पाऊस",

      weatherRainfallDescription:
        "सध्याचा पाऊस, पावसाची सातत्यता आणि अलीकडील हवामान परिस्थितीचे विश्लेषण केले जाते.",

      locationConditions:
        "ठिकाणाची परिस्थिती",

      locationConditionsDescription:
        "भूप्रदेश, जलनिस्सारण, बांधकाम क्षेत्र, रस्त्यांची वैशिष्ट्ये आणि इतर स्थानिक घटकांचा समावेश केला जातो.",

      aiRiskPrediction:
        "AI जोखीम अंदाज",

      aiRiskPredictionDescription:
        "प्रत्येक निरीक्षण बिंदूसाठी सतत जलसाचण्याच्या जोखमीच्या स्कोअरचा अंदाज लावला जातो.",

      riskGuidance:
        "जोखीम आणि मार्गदर्शन",

      riskGuidanceDescription:
        "स्कोअर कमी, मध्यम, उच्च किंवा अत्यंत जोखीम म्हणून दाखवले जातात आणि व्यावहारिक सुरक्षा मार्गदर्शन दिले जाते.",


      hyperlocalWaterloggingRisk:
        "हायपरलोकल जलसाचणे जोखीम",

      connectingLiveRisk:
        "लाईव्ह जोखीम माहितीसोबत कनेक्ट होत आहे...",


      backendConnectionError:
        "बॅकएंड कनेक्शन त्रुटी",

      tryAgain:
        "पुन्हा प्रयत्न करा",

      backendConnectionMessage:
        "लाईव्ह जलसाचणे जोखीम बॅकएंडशी कनेक्ट होऊ शकले नाही.",

      refreshConnectionError:
        "लाईव्ह जलसाचणे जोखीम डेटा अपडेट करता आला नाही.",


      footerTitle:
        "हायपरलोकल जलसाचणे जोखीम निरीक्षण प्रणाली",

      footerTechnology:
        "AI-आधारित स्थानिक जोखीम माहिती • FastAPI • React • Leaflet",

    },
  },
};

const savedLanguage =
  localStorage.getItem("appLanguage") || "en";

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: savedLanguage,
    fallbackLng: "en",

    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;