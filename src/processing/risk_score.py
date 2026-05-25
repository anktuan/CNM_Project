from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskInput:
    cases_7d: int = 0
    trend_score: float = 0
    weather_score: float = 0
    humidity_mean: float = 0
    temperature_mean: float = 0
    disease: str = ""


def weather_risk_score(disease: str, rainfall_mm: float | None, humidity_mean: float | None, temperature_mean: float | None) -> float:
    rainfall = float(rainfall_mm or 0)
    humidity = float(humidity_mean or 0)
    temperature = float(temperature_mean or 0)
    disease_key = disease.lower()

    score = 0.0
    if "sốt xuất huyết" in disease_key:
        if rainfall >= 50:
            score += 20
        elif rainfall >= 20:
            score += 12
        if humidity >= 75:
            score += 10
        if 24 <= temperature <= 32:
            score += 10
    elif "tay chân miệng" in disease_key:
        if humidity >= 70:
            score += 12
        if 25 <= temperature <= 34:
            score += 8
    elif "cúm" in disease_key:
        if humidity >= 70:
            score += 8
        if temperature <= 27:
            score += 8
    return min(score, 40)


def case_signal_score(disease: str, cases_7d: int, baseline_cases: float | None = None) -> float:
    disease_key = disease.lower()
    thresholds = {
        "sốt xuất huyết": 350,
        "tay chân miệng": 700,
        "cúm": 500,
        "sốt rét": 50,
        "sởi": 50,
        "thủy đậu": 100,
        "đau mắt đỏ": 300,
    }
    threshold = next((value for key, value in thresholds.items() if key in disease_key), 300)
    if baseline_cases and baseline_cases > 0:
        threshold = max(threshold, baseline_cases * 1.5)
    return min((cases_7d / threshold) * 100, 100)


def calculate_risk_score(inputs: RiskInput, baseline_cases: float | None = None) -> tuple[float, dict[str, float]]:
    case_signal = case_signal_score(inputs.disease, inputs.cases_7d, baseline_cases)
    trend_signal = min(float(inputs.trend_score or 0), 100)
    weather_signal = min((float(inputs.weather_score or 0) / 40) * 100, 100)

    components = {
        "case_component": round(case_signal * 0.70, 2),
        "trend_component": round(trend_signal * 0.20, 2),
        "weather_component": round(weather_signal * 0.10, 2),
        "case_signal": round(case_signal, 2),
        "trend_signal": round(trend_signal, 2),
        "weather_signal": round(weather_signal, 2),
    }
    score = round(min(components["case_component"] + components["trend_component"] + components["weather_component"], 100), 2)
    return score, components


def classify_alert(score: float) -> str:
    if score >= 75:
        return "Đỏ"
    if score >= 50:
        return "Cam"
    if score >= 25:
        return "Vàng"
    return "Xanh"
