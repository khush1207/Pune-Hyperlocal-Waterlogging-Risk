import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  MapContainer,
  TileLayer,
  CircleMarker,
  Popup,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";

import {
  getCurrentRisk,
  refreshRisk,
} from "./services/api";

/* =========================================================
   PMC DESTINATIONS
   ========================================================= */

const PMC_DESTINATIONS = [
  { name: "Aundh", lat: 18.5590, lng: 73.8075 },
  { name: "Baner", lat: 18.5590, lng: 73.7868 },
  { name: "Balewadi", lat: 18.5762, lng: 73.7680 },
  { name: "Bavdhan", lat: 18.5174, lng: 73.7785 },
  { name: "Kothrud", lat: 18.5074, lng: 73.8077 },
  { name: "Karve Nagar", lat: 18.4900, lng: 73.8200 },
  { name: "Warje", lat: 18.4860, lng: 73.7980 },
  { name: "Shivajinagar", lat: 18.5308, lng: 73.8475 },
  { name: "Deccan Gymkhana", lat: 18.5167, lng: 73.8410 },
  { name: "Model Colony", lat: 18.5325, lng: 73.8390 },
  { name: "Erandwane", lat: 18.5080, lng: 73.8300 },
  { name: "Prabhat Road", lat: 18.5175, lng: 73.8290 },
  { name: "Koregaon Park", lat: 18.5362, lng: 73.8930 },
  { name: "Kalyani Nagar", lat: 18.5480, lng: 73.9020 },
  { name: "Viman Nagar", lat: 18.5679, lng: 73.9143 },
  { name: "Yerawada", lat: 18.5510, lng: 73.8770 },
  { name: "Kharadi", lat: 18.5530, lng: 73.9470 },
  { name: "Wadgaon Sheri", lat: 18.5520, lng: 73.9270 },
  { name: "Mundhwa", lat: 18.5308, lng: 73.9365 },
  { name: "Magarpatta", lat: 18.5158, lng: 73.9270 },
  { name: "Hadapsar", lat: 18.5089, lng: 73.9260 },
  { name: "Mundhwa - Keshav Nagar", lat: 18.5350, lng: 73.9390 },
  { name: "Manjari", lat: 18.5230, lng: 73.9800 },
  { name: "Wanowrie", lat: 18.5010, lng: 73.9000 },
  { name: "Fatima Nagar", lat: 18.4965, lng: 73.8990 },
  { name: "Camp", lat: 18.5135, lng: 73.8780 },
  { name: "Pune Cantonment", lat: 18.5050, lng: 73.8840 },
  { name: "Kondhwa", lat: 18.4690, lng: 73.8890 },
  { name: "Kondhwa Budruk", lat: 18.4540, lng: 73.8950 },
  { name: "NIBM Road", lat: 18.4725, lng: 73.8975 },
  { name: "Undri", lat: 18.4540, lng: 73.9160 },
  { name: "Mohammed Wadi", lat: 18.4780, lng: 73.9200 },
  { name: "Bibwewadi", lat: 18.4765, lng: 73.8660 },
  { name: "Sahakar Nagar", lat: 18.4815, lng: 73.8550 },
  { name: "Parvati", lat: 18.4900, lng: 73.8510 },
  { name: "Dhankawadi", lat: 18.4655, lng: 73.8490 },
  { name: "Ambegaon", lat: 18.4600, lng: 73.8440 },
  { name: "Sinhagad Road", lat: 18.4750, lng: 73.8230 },
  { name: "Dhayari", lat: 18.4475, lng: 73.8000 },
  { name: "Narhe", lat: 18.4420, lng: 73.8260 },
  { name: "Vadgaon Budruk", lat: 18.4670, lng: 73.8320 },
  { name: "Pashan", lat: 18.5390, lng: 73.7920 },
  { name: "Sus", lat: 18.5320, lng: 73.7520 },
  { name: "Pimple Nilakh", lat: 18.5867, lng: 73.7805 },
  { name: "Aundh Road", lat: 18.5635, lng: 73.8200 },
  { name: "Dapodi", lat: 18.5815, lng: 73.8323 },
  { name: "Bopodi", lat: 18.5770, lng: 73.8230 },
  { name: "Khadki", lat: 18.5635, lng: 73.8520 },
  { name: "Dhanori", lat: 18.5820, lng: 73.8970 },
  { name: "Lohegaon", lat: 18.5990, lng: 73.9160 },
  { name: "Vishrantwadi", lat: 18.5800, lng: 73.8780 },
  { name: "Katraj", lat: 18.4529, lng: 73.8652 },
  { name: "Gultekdi", lat: 18.4930, lng: 73.8670 },
  { name: "Swargate", lat: 18.5018, lng: 73.8636 },
  { name: "Market Yard", lat: 18.4855, lng: 73.8690 },
  { name: "Sadashiv Peth", lat: 18.5090, lng: 73.8490 },
  { name: "Shukrawar Peth", lat: 18.5100, lng: 73.8570 },
  { name: "Narayan Peth", lat: 18.5170, lng: 73.8500 },
  { name: "Kasba Peth", lat: 18.5220, lng: 73.8560 },
  { name: "Rasta Peth", lat: 18.5225, lng: 73.8640 },
  { name: "Bund Garden", lat: 18.5390, lng: 73.8830 },
  { name: "Sangamwadi", lat: 18.5430, lng: 73.8680 },
  { name: "Khadakwasla", lat: 18.4420, lng: 73.7650 },
];

/* =========================================================
   DEFAULT MAP LOCATION
   ========================================================= */

const DEFAULT_LOCATION = {
  lat: 18.6298,
  lng: 73.8000,
};

/* =========================================================
   MAP HELPER
   ========================================================= */

function MapUpdater({ target }) {
  const map = useMap();

  useEffect(() => {
    if (!target) return;

    const lat = Number(target.lat);
    const lng = Number(target.lng);

    if (!Number.isNaN(lat) && !Number.isNaN(lng)) {
      map.flyTo(
        [lat, lng],
        14,
        {
          duration: 1.2,
        }
      );
    }
  }, [target, map]);

  return null;
}

/* =========================================================
   STAKEHOLDER-SPECIFIC RISK GUIDANCE
========================================================= */

function RiskGuidance({ level, stakeholder = "RESIDENT" }) {
  const { t } = useTranslation();

  const risk = String(level || "").toUpperCase();
  const role = String(stakeholder || "RESIDENT").toUpperCase();

  const guidance = {
    RESIDENT: {
      LOW: {
        title: t("residentLowTitle"),
        points: [t("residentLow1"), t("residentLow2"), t("residentLow3")],
      },
      MODERATE: {
        title: t("residentModerateTitle"),
        points: [t("residentModerate1"), t("residentModerate2"), t("residentModerate3")],
      },
      HIGH: {
        title: t("residentHighTitle"),
        points: [t("residentHigh1"), t("residentHigh2"), t("residentHigh3"), t("residentHigh4")],
      },
      EXTREME: {
        title: t("residentExtremeTitle"),
        points: [t("residentExtreme1"), t("residentExtreme2"), t("residentExtreme3"), t("residentExtreme4")],
      },
    },
    NGO: {
      LOW: {
        title: t("ngoLowTitle"),
        points: [t("ngoLow1"), t("ngoLow2")],
      },
      MODERATE: {
        title: t("ngoModerateTitle"),
        points: [t("ngoModerate1"), t("ngoModerate2"), t("ngoModerate3")],
      },
      HIGH: {
        title: t("ngoHighTitle"),
        points: [t("ngoHigh1"), t("ngoHigh2"), t("ngoHigh3"), t("ngoHigh4")],
      },
      EXTREME: {
        title: t("ngoExtremeTitle"),
        points: [t("ngoExtreme1"), t("ngoExtreme2"), t("ngoExtreme3"), t("ngoExtreme4")],
      },
    },
    FARMER: {
      LOW: {
        title: t("farmerLowTitle"),
        points: [t("farmerLow1")],
      },
      MODERATE: {
        title: t("farmerModerateTitle"),
        points: [t("farmerModerate1"), t("farmerModerate2"), t("farmerModerate3")],
      },
      HIGH: {
        title: t("farmerHighTitle"),
        points: [t("farmerHigh1"), t("farmerHigh2"), t("farmerHigh3"), t("farmerHigh4")],
      },
      EXTREME: {
        title: t("farmerExtremeTitle"),
        points: [t("farmerExtreme1"), t("farmerExtreme2"), t("farmerExtreme3"), t("farmerExtreme4")],
      },
    },
    AUTHORITY: {
      LOW: {
        title: t("authorityLowTitle"),
        points: [t("authorityLow1"), t("authorityLow2")],
      },
      MODERATE: {
        title: t("authorityModerateTitle"),
        points: [t("authorityModerate1"), t("authorityModerate2"), t("authorityModerate3")],
      },
      HIGH: {
        title: t("authorityHighTitle"),
        points: [t("authorityHigh1"), t("authorityHigh2"), t("authorityHigh3"), t("authorityHigh4")],
      },
      EXTREME: {
        title: t("authorityExtremeTitle"),
        points: [t("authorityExtreme1"), t("authorityExtreme2"), t("authorityExtreme3"), t("authorityExtreme4"), t("authorityExtreme5")],
      },
    },
  };

  if (!risk) {
    return null;
  }

  const selected = guidance[role]?.[risk];

  if (!selected) {
    return (
      <div className="risk-guidance">
        <div className="guidance-header">
          <span className="guidance-icon">✓</span>
          <span>
            {role === "RESIDENT"
              ? t("residentGuidance")
              : role === "NGO"
                ? t("ngoActions")
                : role === "FARMER"
                  ? t("farmerPrecautions")
                  : t("authorityActions")}
          </span>
        </div>
        <p className="guidance-title">
          {t("riskInformationUnavailable")}
        </p>
      </div>
    );
  }

  return (
    <div className={`risk-guidance ${risk.toLowerCase()}`}>
      <div className="guidance-header">
        <span className="guidance-icon">✓</span>
        <span>{t("whatThisMeans")}</span>
      </div>
      <p className="guidance-title">{selected.title}</p>
      {selected.points.length > 0 && (
        <ul>
          {selected.points.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

/* =========================================================
   MAIN APP
========================================================= */

function App() {
  const { t, i18n } = useTranslation();

  const handleLanguageChange = (event) => {
    const language = event.target.value;
    i18n.changeLanguage(language);
    localStorage.setItem("appLanguage", language);
  };

  /* =======================================================
     BACKEND DATA
  ======================================================= */

  const [stats, setStats] = useState(null);
  const [points, setPoints] = useState([]);
  const [wards, setWards] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  /* =======================================================
     DEVICE LOCATION
  ======================================================= */

  const [deviceLocation, setDeviceLocation] = useState(null);
  const [locationError, setLocationError] = useState("");
  const [locationLoading, setLocationLoading] = useState(true);

  /* =======================================================
     DESTINATION
  ======================================================= */

  const [selectedDestination, setSelectedDestination] = useState(null);
  const [mapTarget, setMapTarget] = useState(null);

  /* =======================================================
     STAKEHOLDER
  ======================================================= */

  const [selectedStakeholder, setSelectedStakeholder] = useState("RESIDENT");

  /* =======================================================
     NEW FRONTEND-ONLY FILTER
  ======================================================= */

  const [activeRiskFilter, setActiveRiskFilter] = useState("ALL");

  /* =======================================================
     HOW IT WORKS OPEN/CLOSE
  ======================================================= */

  const [showHowItWorks, setShowHowItWorks] = useState(false);

  /* =======================================================
     RISK COLOR
  ======================================================= */

  const getRiskColor = (level) => {
    const risk = String(level || "").toUpperCase();
    if (risk === "LOW") return "#22c55e";
    if (risk === "MODERATE") return "#facc15";
    if (risk === "HIGH") return "#fb923c";
    if (risk === "EXTREME") return "#ef4444";
    return "#94a3b8";
  };

  /* =======================================================
     RISK CLASS
  ======================================================= */

  const getRiskClass = (level) => {
    if (!level) return "moderate";
    return String(level).toLowerCase();
  };

  /* =======================================================
     SAFE NUMBER
  ======================================================= */

  const safeNumber = (value, fallback = 0) => {
    if (value === null || value === undefined || value === "") return fallback;
    const number = Number(value);
    return Number.isNaN(number) ? fallback : number;
  };

  /* =======================================================
     GET AREA NAME
  ======================================================= */

  const getAreaName = (point) => {
    if (!point) return "Unknown Area";
    if (point.Location_ID) {
      const locationId = String(point.Location_ID);
      if (locationId.includes("__")) return locationId.split("__")[0];
      return locationId;
    }
    if (point.Area_Name) return point.Area_Name;
    if (point.area_name) return point.area_name;
    if (point.Ward_Name) return point.Ward_Name;
    if (point.Ward) return point.Ward;
    return "Unknown Area";
  };

  /* =======================================================
     GET POINT ID
  ======================================================= */

  const getPointId = (point) => {
    if (!point) return "";
    return point.Point_ID || point.Point || "";
  };

  /* =======================================================
     GET RISK LEVEL
  ======================================================= */

  const getPointRiskLevel = (point) => {
    return String(
      point?.risk_level ??
      point?.Risk_Level ??
      point?.riskLevel ??
      point?.level ??
      ""
    ).toUpperCase();
  };

  /* =======================================================
     GET RISK SCORE
  ======================================================= */

  const getPointRiskScore = (point) => {
    return safeNumber(
      point?.risk_score ??
      point?.Risk_Score ??
      point?.score ??
      point?.predicted_risk ??
      0
    );
  };

  /* =======================================================
     NORMALIZE API RESPONSE
  ======================================================= */

  const normalizeApiResponse = (response) => {
    let data = response?.data ?? response;

    if (data && !Array.isArray(data) && data.data && typeof data.data === "object" && !Array.isArray(data.data)) {
      data = data.data;
    }

    if (Array.isArray(data)) {
      return { points: data, wards: [], stats: {}, timestamp: "" };
    }

    let loadedPoints = [];
    if (Array.isArray(data?.points)) loadedPoints = data.points;
    else if (Array.isArray(data?.locations)) loadedPoints = data.locations;
    else if (Array.isArray(data?.results)) loadedPoints = data.results;
    else if (Array.isArray(data?.predictions)) loadedPoints = data.predictions;
    else if (Array.isArray(data?.data)) loadedPoints = data.data;

    let loadedWards = [];
    if (Array.isArray(data?.wards)) loadedWards = data.wards;

    if (!loadedWards.length && loadedPoints.length) {
      const uniqueWards = new Set();
      loadedPoints.forEach((point) => {
        const ward = point.Ward_Name || point.Ward || "";
        if (ward) uniqueWards.add(ward);
      });
      loadedWards = Array.from(uniqueWards);
    }

    return {
      points: loadedPoints,
      wards: loadedWards,
      stats: data?.stats || {},
      timestamp: data?.timestamp || "",
    };
  };

  /* =======================================================
     LOAD BACKEND DATA
  ======================================================= */

  const loadData = async () => {
    try {
      setError("");
      setRefreshing(true);

      const response = await getCurrentRisk();
      const data = normalizeApiResponse(response);

      const loadedPoints = data.points || [];
      const loadedWards = data.wards || [];

      const riskCounts = { LOW: 0, MODERATE: 0, HIGH: 0, EXTREME: 0 };
      loadedPoints.forEach((point) => {
        const level = getPointRiskLevel(point);
        if (Object.prototype.hasOwnProperty.call(riskCounts, level)) {
          riskCounts[level] += 1;
        }
      });

      const rainfallValues = loadedPoints
        .map((point) => {
          return Number(
            point["Rainfall Now"] ?? point.Rainfall_Now ?? point.Rain_mm ?? point.rainfall_now ?? point.rain_mm ?? 0
          );
        })
        .filter((value) => Number.isFinite(value));

      const currentRainfall = rainfallValues.length
        ? rainfallValues.reduce((sum, value) => sum + value, 0) / rainfallValues.length
        : 0;

      const calculatedStats = {
        total_wards: loadedWards.length,
        total_points: loadedPoints.length,
        risk_counts: riskCounts,
        current_rainfall: currentRainfall,
        timestamp: data.stats?.timestamp || data.timestamp || "",
      };

      setStats(calculatedStats);
      setPoints(loadedPoints);
      setWards(loadedWards);
    } catch (err) {
      setError("backendConnectionMessage");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  /* =======================================================
     INITIAL LOAD
  ======================================================= */

  useEffect(() => {
    loadData();
    const refreshInterval = setInterval(() => {
      loadData();
    }, 15 * 60 * 1000);
    return () => clearInterval(refreshInterval);
  }, []);

  /* =======================================================
     GET DEVICE LOCATION
  ======================================================= */

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationError("Location services are not supported by this browser.");
      setLocationLoading(false);
      setMapTarget(DEFAULT_LOCATION);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const location = { lat: position.coords.latitude, lng: position.coords.longitude };
        setDeviceLocation(location);
        setMapTarget(location);
        setLocationLoading(false);
      },
      (error) => {
        setLocationError("Unable to access your current location. Please allow location access.");
        setLocationLoading(false);
        setMapTarget(DEFAULT_LOCATION);
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    );
  }, []);

  /* =======================================================
     REFRESH
  ======================================================= */

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      setError("");
      await refreshRisk();
      await loadData();
    } catch (err) {
      setError("refreshConnectionError");
      setRefreshing(false);
    }
  };

  /* =======================================================
     SELECT DESTINATION
  ======================================================= */

  const handleDestinationChange = (event) => {
    const destinationName = event.target.value;

    if (!destinationName) {
      setSelectedDestination(null);
      if (deviceLocation) {
        setMapTarget(deviceLocation);
      } else {
        setMapTarget(DEFAULT_LOCATION);
      }
      return;
    }

    const destination = PMC_DESTINATIONS.find((item) => item.name === destinationName);
    if (!destination) return;

    setSelectedDestination(destination);
    setMapTarget({ lat: destination.lat, lng: destination.lng });
  };

  /* =======================================================
     DISTANCE CALCULATION
  ======================================================= */

  const calculateDistanceKm = (lat1, lng1, lat2, lng2) => {
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLng = ((lng2 - lng1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  /* =======================================================
     GET DESTINATION RISK
  ======================================================= */

  const getDestinationRisk = () => {
    if (!selectedDestination || !points.length) return null;

    const destinationLat = selectedDestination.lat;
    const destinationLng = selectedDestination.lng;

    const nearbyPoints = points
      .map((point) => {
        const lat = Number(point.Latitude ?? point.latitude ?? point.lat);
        const lng = Number(point.Longitude ?? point.longitude ?? point.lng);
        if (Number.isNaN(lat) || Number.isNaN(lng)) return null;

        const distance = calculateDistanceKm(destinationLat, destinationLng, lat, lng);
        return { point, distance };
      })
      .filter(Boolean)
      .sort((a, b) => a.distance - b.distance);

    if (!nearbyPoints.length) return null;

    const pointsWithinRadius = nearbyPoints.filter((item) => item.distance <= 2);
    const candidates = pointsWithinRadius.length ? pointsWithinRadius : [nearbyPoints[0]];

    const riskOrder = { LOW: 1, MODERATE: 2, HIGH: 3, EXTREME: 4 };

    candidates.sort((a, b) => {
      const levelA = getPointRiskLevel(a.point);
      const levelB = getPointRiskLevel(b.point);
      const orderDifference = (riskOrder[levelB] || 0) - (riskOrder[levelA] || 0);
      if (orderDifference !== 0) return orderDifference;
      return getPointRiskScore(b.point) - getPointRiskScore(a.point);
    });

    const selectedPoint = candidates[0].point;

    return {
      level: getPointRiskLevel(selectedPoint) || "MODERATE",
      point: selectedPoint,
      distance: candidates[0].distance,
      nearbyCount: candidates.length,
    };
  };

  /* =======================================================
     GET CURRENT LOCATION RISK
  ======================================================= */

  const getCurrentLocationRisk = () => {
    if (!deviceLocation || !points.length) return null;

    const currentLat = Number(deviceLocation.lat);
    const currentLng = Number(deviceLocation.lng);

    if (Number.isNaN(currentLat) || Number.isNaN(currentLng)) return null;

    let nearestPoint = null;
    let nearestDistance = Infinity;

    points.forEach((point) => {
      const lat = Number(point.Latitude ?? point.latitude ?? point.lat);
      const lng = Number(point.Longitude ?? point.longitude ?? point.lng);
      if (Number.isNaN(lat) || Number.isNaN(lng)) return;

      const distance = calculateDistanceKm(currentLat, currentLng, lat, lng);
      if (distance < nearestDistance) {
        nearestDistance = distance;
        nearestPoint = point;
      }
    });

    if (!nearestPoint) return null;

    return {
      level: getPointRiskLevel(nearestPoint) || "MODERATE",
      point: nearestPoint,
      distance: nearestDistance,
    };
  };

  const currentLocationRisk = getCurrentLocationRisk();
  const destinationRisk = getDestinationRisk();

  /* =======================================================
     KPI DATA
  ======================================================= */

  const totalPoints = stats?.total_points || points.length || 0;
  const riskCounts = stats?.risk_counts || { LOW: 0, MODERATE: 0, HIGH: 0, EXTREME: 0 };

  const kpis = [
    { key: "ALL", label: t("allLocations"), value: totalPoints, icon: "◉", className: "all" },
    { key: "LOW", label: t("lowRisk"), value: riskCounts.LOW || 0, icon: "✓", className: "low" },
    { key: "MODERATE", label: t("moderateRisk"), value: riskCounts.MODERATE || 0, icon: "!", className: "moderate" },
    { key: "HIGH", label: t("highRisk"), value: riskCounts.HIGH || 0, icon: "▲", className: "high" },
    { key: "EXTREME", label: t("extremeRisk"), value: riskCounts.EXTREME || 0, icon: "!", className: "extreme" },
  ];

  /* =======================================================
     FILTER MAP POINTS
  ======================================================= */

  const visiblePoints =
    activeRiskFilter === "ALL"
      ? points
      : points.filter((point) => getPointRiskLevel(point) === activeRiskFilter);

  const handleRiskFilter = (filter) => {
    setActiveRiskFilter(filter);
  };

  /* =======================================================
     LOADING SCREEN
  ======================================================= */

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-orbit">
          <div className="loading-ring"></div>
          <span>🌧️</span>
        </div>
        <h1>{t("hyperlocalWaterloggingRisk")}</h1>
        <p>{t("connectingLiveRisk")}</p>
      </div>
    );
  }

  /* =======================================================
     ERROR SCREEN
  ======================================================= */

  if (error) {
    return (
      <div className="error-page">
        <div className="error-card">
          <div className="error-icon">⚠</div>
          <h1>{t("backendConnectionError")}</h1>
          <p>{t(error)}</p>
          <button className="primary-button" onClick={handleRefresh}>
            {t("tryAgain")}
          </button>
        </div>
      </div>
    );
  }

  /* =======================================================
     MAIN DASHBOARD
  ======================================================= */

  return (
    <div className="app-shell">
      <main className="main-content">

        {/* =================================================
            LANGUAGE SELECTOR
        ================================================= */}
        <div className="language-selector">
          <span className="language-label">🌐 {t("language")}</span>
          <select value={i18n.language} onChange={handleLanguageChange} aria-label={t("language")}>
            <option value="en">English</option>
            <option value="hi">हिंदी</option>
            <option value="mr">मराठी</option>
          </select>
        </div>

        {/* =================================================
            HEADER
        ================================================= */}
        <header className="hero-header">
          <div className="hero-glow"></div>
          <div className="hero-content">
            <div className="hero-eyebrow">
              <span className="live-pulse"></span>
              {t("systemLabel")}
            </div>
            <h1>
              {t("waterlogging")}
              <span> {t("riskIntelligence")}</span>
            </h1>
            <p>{t("heroDescription")}</p>
            <div className="hero-meta">
              <div className="hero-meta-item">
                <span>●</span>
                {t("liveWeather")}
              </div>
              <div className="hero-meta-item">
                <span>◉</span>
                {totalPoints} {t("locations")}
              </div>
              <div className="hero-meta-item">
                <span>◷</span>
                {t("currentRisk")}
              </div>
            </div>
          </div>
          <button className={`refresh-button ${refreshing ? "refreshing" : ""}`} onClick={handleRefresh} disabled={refreshing}>
            <span className="refresh-icon">↻</span>
            {refreshing ? t("updating") : t("refreshRisk")}
          </button>
        </header>

        {/* =================================================
            KPI SECTION
        ================================================= */}
        <section className="kpi-section">
          <div className="section-heading">
            <div>
              <span className="section-kicker">{t("liveOverview")}</span>
            </div>
            <span className="filter-hint">{t("clickCardToFilter")}</span>
          </div>

          <div className="kpi-grid">
            {kpis.map((kpi) => (
              <button
                key={kpi.key}
                className={`kpi-card ${kpi.className} ${activeRiskFilter === kpi.key ? "active" : ""}`}
                onClick={() => handleRiskFilter(kpi.key)}
              >
                <div className="kpi-card-top">
                  <div className="kpi-icon">{kpi.icon}</div>
                  {activeRiskFilter === kpi.key && <span className="active-pill">{t("active")}</span>}
                </div>
                <div className="kpi-value">{Number(kpi.value).toLocaleString("en-IN")}</div>
                <div className="kpi-label">{kpi.label}</div>
                <div className="kpi-bar">
                  <span></span>
                </div>
              </button>
            ))}
          </div>
        </section>

        {/* =================================================
            STAKEHOLDER SELECTOR
        ================================================= */}
        <section className="stakeholder-panel">
          <div className="destination-header">
            <div className="destination-text">
              <span className="section-kicker">{t("personalizedGuidance")}</span>
              <h2>{t("whoAreYou")}</h2>
              <p>{t("selectRole")}</p>
            </div>
          </div>
          <div className="select-wrapper">
            <span className="select-icon">👤</span>
            <select value={selectedStakeholder} onChange={(event) => setSelectedStakeholder(event.target.value)}>
              <option value="RESIDENT">{t("resident")}</option>
              <option value="NGO">{t("ngoVolunteer")}</option>
              <option value="FARMER">{t("farmer")}</option>
              <option value="AUTHORITY">{t("localAuthority")}</option>
            </select>
            <span className="select-arrow">⌄</span>
          </div>
        </section>

        {/* =================================================
            DESTINATION SELECTOR
        ================================================= */}
        <section className="destination-panel">
          <div className="destination-header">
            <div className="destination-text">
              <span className="section-kicker">{t("locationSearch")}</span>
              <h2>{t("whereAreYouGoing")}</h2>
              <p>{t("selectDestinationDescription")}</p>
            </div>
            <div className={`location-status ${locationLoading ? "detecting" : locationError ? "unavailable" : "detected"}`}>
              <span></span>
              {locationLoading ? t("detectingLocation") : locationError ? t("locationUnavailable") : t("currentLocationDetected")}
            </div>
          </div>
          <div className="select-wrapper">
            <span className="select-icon">📍</span>
            <select value={selectedDestination?.name || ""} onChange={handleDestinationChange}>
              <option value="">{t("selectPuneArea")}</option>
              {PMC_DESTINATIONS.map((destination) => (
                <option key={destination.name} value={destination.name}>
                  {destination.name}
                </option>
              ))}
            </select>
            <span className="select-arrow">⌄</span>
          </div>
        </section>

        {/* =================================================
            MAP + LOCATION RISK
        ================================================= */}
        <section className="main-dashboard-grid">
          {/* =================================================
              MAP
          ================================================= */}
          <div className="map-panel dashboard-panel">
            <div className="panel-header">
              <div>
                <div className="panel-kicker">{t("geospatialView")}</div>
                <h2>{t("hyperlocalRiskMap")}</h2>
                <p>
                  {activeRiskFilter === "ALL"
                    ? t("livePredictedRisk")
                    : t("showingRiskLocations", { risk: t(`${activeRiskFilter.toLowerCase()}Risk`) })}
                </p>
              </div>
              <div className="map-live-status">
                <span className="live-pulse"></span>
                {t("live")}
              </div>
            </div>

            {/* FILTER CHIPS */}
            <div className="map-filter-bar">
              {["ALL", "LOW", "MODERATE", "HIGH", "EXTREME"].map((filter) => (
                <button
                  key={filter}
                  className={`map-filter ${activeRiskFilter === filter ? `selected ${filter.toLowerCase()}` : ""}`}
                  onClick={() => handleRiskFilter(filter)}
                >
                  <span className="filter-dot"></span>
                  {filter === "ALL" ? t("allLocations") : t(`${filter.toLowerCase()}Risk`)}
                </button>
              ))}
            </div>

            <div className="map-wrapper">
              <MapContainer center={[DEFAULT_LOCATION.lat, DEFAULT_LOCATION.lng]} zoom={14} scrollWheelZoom={true} className="risk-map">
                <MapUpdater target={mapTarget} />
                <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

                {/* =================================================
                    DEVICE LOCATION
                ================================================= */}
                {deviceLocation && (
                  <CircleMarker
                    center={[deviceLocation.lat, deviceLocation.lng]}
                    radius={9}
                    pathOptions={{ color: "#ffffff", fillColor: "#2563eb", fillOpacity: 1, weight: 3 }}
                  >
                    <Popup>
                      <div className="map-popup">
                        <h3>{t("yourCurrentLocation")}</h3>
                        {currentLocationRisk ? (
                          <>
                            <div className="popup-row">
                              <span>{t("nearbyArea")}</span>
                              <strong>{getAreaName(currentLocationRisk.point)}</strong>
                            </div>
                            <div className="popup-row">
                              <span>{t("risk")}</span>
                              <strong style={{ color: getRiskColor(currentLocationRisk.level) }}>
                                {t(`${currentLocationRisk.level.toLowerCase()}Risk`)}
                              </strong>
                            </div>
                            <div className="popup-row">
                              <span>{t("score")}</span>
                            </div>
                          </>
                        ) : (
                          <div>{t("riskDataUnavailable")}</div>
                        )}
                      </div>
                    </Popup>
                  </CircleMarker>
                )}

                {/* =================================================
                    DESTINATION MARKER
                ================================================= */}
                {selectedDestination && (
                  <CircleMarker
                    center={[selectedDestination.lat, selectedDestination.lng]}
                    radius={11}
                    pathOptions={{ color: "#ffffff", fillColor: "#dc2626", fillOpacity: 1, weight: 3 }}
                  >
                    <Popup>
                      <div className="map-popup">
                        <h3>{selectedDestination.name}</h3>
                        <div className="popup-row">
                          <span>{t("type")}</span>
                          <strong>{t("destination")}</strong>
                        </div>
                        {destinationRisk && (
                          <>
                            <div className="popup-row">
                              <span>{t("risk")}</span>
                              <strong style={{ color: getRiskColor(destinationRisk.level) }}>
                                {t(`${destinationRisk.level.toLowerCase()}Risk`)}
                              </strong>
                            </div>
                            <div className="popup-row">
                              <span>{t("score")}</span>
                            </div>
                          </>
                        )}
                      </div>
                    </Popup>
                  </CircleMarker>
                )}

                {/* =================================================
                    RISK POINTS
                ================================================= */}
                {visiblePoints.map((point, index) => {
                  const level = getPointRiskLevel(point);
                  const color = getRiskColor(level);
                  const lat = Number(point.Latitude ?? point.latitude ?? point.lat);
                  const lng = Number(point.Longitude ?? point.longitude ?? point.lng);

                  if (Number.isNaN(lat) || Number.isNaN(lng)) return null;

                  const riskScore = getPointRiskScore(point);

                  return (
                    <CircleMarker
                      key={`${getAreaName(point)}-${getPointId(point)}-${index}`}
                      center={[lat, lng]}
                      radius={activeRiskFilter !== "ALL" ? 7 : 5}
                      pathOptions={{
                        color: color,
                        fillColor: color,
                        fillOpacity: activeRiskFilter !== "ALL" ? 0.95 : 0.82,
                        weight: activeRiskFilter !== "ALL" ? 2 : 1,
                      }}
                    >
                      <Popup>
                        <div className="map-popup">
                          <div className="popup-risk-indicator">
                            <span style={{ background: color }}></span>
                            {t(`${level.toLowerCase()}Risk`)}
                          </div>
                          <h3>{getAreaName(point)}</h3>
                          {getPointId(point) && (
                            <div className="popup-subtitle">
                              {t("samplingPoint")}: {getPointId(point)}
                            </div>
                          )}
                          <div className="popup-score">
                            <span>{t("riskScore")}</span>
                            <strong>{riskScore.toFixed(2)}</strong>
                          </div>
                        </div>
                      </Popup>
                    </CircleMarker>
                  );
                })}
              </MapContainer>

              {/* =================================================
                  MAP LEGEND
              ================================================= */}
              <div className="map-legend">
                <div className="legend-title">{t("riskLevel")}</div>
                <div className="legend-items">
                  <div>
                    <i className="legend-dot low-dot"></i>
                    {t("lowRisk")}
                  </div>
                  <div>
                    <i className="legend-dot moderate-dot"></i>
                    {t("moderateRisk")}
                  </div>
                  <div>
                    <i className="legend-dot high-dot"></i>
                    {t("highRisk")}
                  </div>
                  <div>
                    <i className="legend-dot extreme-dot"></i>
                    {t("extremeRisk")}
                  </div>
                </div>
                <div className="legend-divider"></div>
                <div className="legend-special">
                  <i className="legend-location"></i>
                  {t("yourLocation")}
                </div>
                {selectedDestination && (
                  <div className="legend-special">
                    <i className="legend-destination"></i>
                    {t("destination")}
                  </div>
                )}
              </div>

              {/* MAP POINT COUNT */}
              <div className="map-counter">
                {t("showing")} <strong>{visiblePoints.length}</strong> {t("of")} <strong>{points.length}</strong> {t("locationsLabel")}
              </div>
            </div>
          </div>

          {/* =================================================
              RISK PANEL
          ================================================= */}
          <div className="risk-side-panel">
            {/* CURRENT LOCATION */}
            <div className="risk-card current-location-card">
              <div className="risk-card-top">
                <div>
                  <span className="panel-kicker">{t("yourLocationPanel")}</span>
                </div>
              </div>
              {currentLocationRisk ? (
                <>
                  <div className="location-name">{getAreaName(currentLocationRisk.point)}</div>
                  <div className={`risk-display ${getRiskClass(currentLocationRisk.level)}`}>
                    <span>{t(`${currentLocationRisk.level.toLowerCase()}Risk`)}</span>
                  </div>
                  <RiskGuidance level={currentLocationRisk.level} stakeholder={selectedStakeholder} />
                </>
              ) : (
                <div className="risk-unavailable">{t("detectingCurrentRisk")}</div>
              )}
            </div>

            {/* DESTINATION */}
            <div className="risk-card destination-risk-card">
              <div className="risk-card-top">
                <div>
                  <span className="panel-kicker">{t("destinationPanel")}</span>
                </div>
              </div>
              {!selectedDestination ? (
                <div className="empty-destination">
                  <div className="empty-destination-icon">📍</div>
                  <h3>{t("selectDestination")}</h3>
                  <p>{t("chooseAreaDescription")}</p>
                </div>
              ) : destinationRisk ? (
                <>
                  <div className="location-name">{selectedDestination.name}</div>
                  <div className={`risk-display ${getRiskClass(destinationRisk.level)}`}>
                    <span>{t(`${destinationRisk.level.toLowerCase()}Risk`)}</span>
                  </div>
                  <RiskGuidance level={destinationRisk.level} stakeholder={selectedStakeholder} />
                </>
              ) : (
                <div className="risk-unavailable">{t("riskDataUnavailable")}</div>
              )}
            </div>
          </div>
        </section>

        {/* =================================================
            HOW IT WORKS
        ================================================= */}
        <section className="how-it-works">
          <button className="how-it-works-header" onClick={() => setShowHowItWorks(!showHowItWorks)}>
            <div>
              <span className="section-kicker">{t("systemInformation")}</span>
              <h2>{t("howSystemWorks")}</h2>
            </div>
            <span className={`how-arrow ${showHowItWorks ? "open" : ""}`}>↓</span>
          </button>

          {showHowItWorks && (
            <div className="how-it-works-content">
              <div className="process-card">
                <div className="process-number">01</div>
                <div className="process-icon">🌧️</div>
                <h3>{t("weatherRainfall")}</h3>
                <p>{t("weatherRainfallDescription")}</p>
              </div>
              <div className="process-card">
                <div className="process-number">02</div>
                <div className="process-icon">🗺️</div>
                <h3>{t("locationConditions")}</h3>
                <p>{t("locationConditionsDescription")}</p>
              </div>
              <div className="process-card">
                <div className="process-number">03</div>
                <div className="process-icon">🤖</div>
                <h3>{t("aiRiskPrediction")}</h3>
                <p>{t("aiRiskPredictionDescription")}</p>
              </div>
              <div className="process-card">
                <div className="process-number">04</div>
                <div className="process-icon">🚦</div>
                <h3>{t("riskGuidance")}</h3>
                <p>{t("riskGuidanceDescription")}</p>
              </div>
            </div>
          )}
        </section>

        {/* =================================================
            FOOTER
        ================================================= */}
        <footer className="main-footer">
          <div className="footer-brand">{t("footerTitle")}</div>
          <span>{t("footerTechnology")}</span>
        </footer>
      </main>
    </div>
  );
}

export default App;