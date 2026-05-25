from src.processing.risk_score import RiskInput, calculate_risk_score, classify_alert, weather_risk_score


def test_risk_score_and_alert_level():
    score, components = calculate_risk_score(
        RiskInput(cases_7d=350, trend_score=80, weather_score=20, disease="Sốt xuất huyết")
    )

    assert score == 91
    assert components["case_component"] == 70
    assert classify_alert(score) == "Đỏ"


def test_weather_score_for_dengue_conditions():
    score = weather_risk_score("Sốt xuất huyết", rainfall_mm=60, humidity_mean=80, temperature_mean=28)

    assert score == 40
