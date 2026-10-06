import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000";

const API = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000,
});


// ============================================================
// NORMALIZE POINT
// ============================================================

const normalizePoint = (point) => ({
  ...point,

  Ward:
    point.Ward ??
    point.Ward_Name ??
    point.ward ??
    "",

  Point:
    point.Point ??
    point.Point_ID ??
    point.point ??
    "",

  Location_ID:
    point.Location_ID ??
    point.location_id ??
    "",

  Latitude:
    Number(point.Latitude ?? point.latitude ?? 0),

  Longitude:
    Number(point.Longitude ?? point.longitude ?? 0),

  DateTime:
    point.DateTime ??
    point.datetime ??
    point.timestamp ??
    "",

  risk_level:
    point.risk_level ??
    point.Risk_Level ??
    "UNKNOWN",

  risk_score:
    Number(
      point.risk_score ??
      point["Risk Score"] ??
      0
    ),

  // Current-hour rainfall
  "Rainfall Today":
    Number(
      point["Rainfall Today"] ??
      point.Rainfall_Today ??
      0
    ),

  // Hourly weather
  Temperature:
    Number(
      point.Temperature ??
      point.Average_Temperature ??
      0
    ),

  Humidity:
    Number(
      point.Humidity ??
      point.Average_Humidity ??
      0
    ),

  "Wind Speed":
    Number(
      point["Wind Speed"] ??
      point.Maximum_Wind_Speed ??
      0
    ),

  // Rainfall persistence
  "Rain Last 3h":
    Number(
      point["Rain Last 3h"] ??
      point.Rain_Last_3h ??
      0
    ),

  "Rain Last 24h":
    Number(
      point["Rain Last 24h"] ??
      point.Rain_Last_24h ??
      0
    ),

  "Rain Last 72h":
    Number(
      point["Rain Last 72h"] ??
      point.Rain_Last_72h ??
      0
    ),
});


// ============================================================
// NORMALIZE WARD
// ============================================================

const normalizeWard = (ward) => ({
  ...ward,

  Ward:
    ward.Ward ??
    ward.Ward_Name ??
    "",

  avg_risk:
    Number(
      ward.avg_risk ??
      ward.average_risk ??
      0
    ),

  max_risk:
    Number(
      ward.max_risk ??
      ward.maximum_risk ??
      0
    ),

  high_risk_points:
    Number(
      ward.high_risk_points ??
      ward.high_or_extreme_points ??
      0
    ),
});


// ============================================================
// LIVE CURRENT RISK
// ============================================================

export const getCurrentRisk = async () => {

  const response = await API.get(
    "/api/risk/current"
  );

  const data = response.data;

  // Backend currently returns:
  // {
  //   timestamp,
  //   count,
  //   data: [...]
  // }

  const rawPoints =
    Array.isArray(data?.data)
      ? data.data
      : [];

  // Normalize all 482 locations
  const points =
    rawPoints.map(normalizePoint);

  // ----------------------------------------------------------
  // RISK COUNTS
  // ----------------------------------------------------------

  const riskCounts = {
    LOW: 0,
    MODERATE: 0,
    HIGH: 0,
    EXTREME: 0,
  };

  points.forEach((point) => {

    const level =
      String(
        point.risk_level || "UNKNOWN"
      ).toUpperCase();

    if (
      Object.prototype.hasOwnProperty.call(
        riskCounts,
        level
      )
    ) {
      riskCounts[level] += 1;
    }

  });


  // ----------------------------------------------------------
  // WARDS
  // ----------------------------------------------------------

  const wardMap = new Map();

  points.forEach((point) => {

    const wardName =
      point.Ward || "Unknown";

    if (!wardMap.has(wardName)) {
      wardMap.set(
        wardName,
        []
      );
    }

    wardMap
      .get(wardName)
      .push(point);

  });


  const wards =
    Array.from(
      wardMap.entries()
    ).map(
      ([wardName, wardPoints]) => {

        const scores =
          wardPoints.map(
            (point) =>
              Number(
                point.risk_score || 0
              )
          );

        const avgRisk =
          scores.length
            ? scores.reduce(
                (sum, value) =>
                  sum + value,
                0
              ) / scores.length
            : 0;

        const maxRisk =
          scores.length
            ? Math.max(...scores)
            : 0;

        const highRiskPoints =
          wardPoints.filter(
            (point) => {

              const level =
                String(
                  point.risk_level ||
                    ""
                ).toUpperCase();

              return (
                level === "HIGH" ||
                level === "EXTREME"
              );

            }
          ).length;

        return {
          Ward: wardName,
          avg_risk: avgRisk,
          max_risk: maxRisk,
          high_risk_points:
            highRiskPoints,
        };

      }
    );


  // ----------------------------------------------------------
  // CURRENT RAINFALL
  // ----------------------------------------------------------

  const rainfallValues =
    points
      .map(
        (point) =>
          Number(
            point["Rainfall Today"] || 0
          )
      )
      .filter(
        (value) =>
          Number.isFinite(value)
      );

  const currentRainfall =
    rainfallValues.length
      ? rainfallValues.reduce(
          (sum, value) =>
            sum + value,
          0
        ) / rainfallValues.length
      : 0;


  // ----------------------------------------------------------
  // STATS
  // ----------------------------------------------------------

  const stats = {

    total_wards:
      wards.length,

    total_points:
      points.length,

    risk_counts:
      riskCounts,

    current_rainfall:
      currentRainfall,

    timestamp:
      data?.timestamp ?? "",

  };


  return {
    stats,
    points,
    wards,
  };

};


// ============================================================
// FORCE REFRESH
// ============================================================

export const refreshRisk = async () => {

  const response = await API.post(
    "/api/risk/refresh"
  );

  return response.data;
};


// ============================================================
// HEALTH
// ============================================================

export const getHealth = async () => {

  const response = await API.get(
    "/api/health"
  );

  return response.data;
};


// ============================================================
// BACKWARD COMPATIBILITY
// ============================================================

export const getStatistics = async () => {

  const data =
    await getCurrentRisk();

  return {
    data: data.stats,
  };
};


export const getPoints = async () => {

  const data =
    await getCurrentRisk();

  return {
    data: data.points,
  };
};


export const getWards = async () => {

  const data =
    await getCurrentRisk();

  return {
    data: data.wards,
  };
};

/* =========================================
   ROUTE RISK
========================================= */

export const checkRouteRisk = async (
  start,
  destination
) => {
  const response = await API.post(
    "/api/route-risk",
    {
      start,
      destination,
    }
  );

  return response.data;
};

export default API;