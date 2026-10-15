import pytest
from app.services.emissions_calculator import calculate_voyage_emissions
from app.services.anomaly_detector import detect_anomalies

def test_calculate_voyage_emissions():
    res = calculate_voyage_emissions(
        fuel_type="HFO",
        fuel_consumed_mt=100.0,
        distance_nm=1000.0,
        cargo_mt=5000.0
    )
    assert "co2_tonnes" in res
    assert "co2_equivalent_tonnes" in res
    assert res["co2_tonnes"] > 0
    assert res["sox_tonnes"] > 0

def test_detect_anomalies_normal():
    voyage = {"fuel_consumed_mt": 100.0, "distance_nm": 1000.0, "cargo_mt": 5000.0}
    ship = {"vessel_type": "Bulk Carrier", "dwt": 50000.0}
    is_anomalous, reasons = detect_anomalies(voyage, ship)
    assert is_anomalous is False
    assert len(reasons) == 0

def test_detect_anomalies_flagged():
    voyage = {"fuel_consumed_mt": 5000.0, "distance_nm": 10.0, "cargo_mt": 500000.0}
    ship = {"vessel_type": "Bulk Carrier", "dwt": 10000.0}
    is_anomalous, reasons = detect_anomalies(voyage, ship)
    assert is_anomalous is True
    assert len(reasons) > 0
