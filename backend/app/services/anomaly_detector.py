import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

# Maximum plausible fuel capacity bounds (metric tonnes) by vessel type
MAX_FUEL_CAPACITY = {
    "Container": 15000.0,
    "Tanker": 12000.0,
    "Bulk Carrier": 8000.0,
    "RoRo": 5000.0,
    "Passenger": 4000.0,
    "Other": 10000.0
}

def detect_anomalies(voyage_data: Dict[str, Any], ship_data: Dict[str, Any]) -> Tuple[bool, list[str]]:
    """
    Analyzes voyage data to detect potential fraud, typos, or sensor errors.
    Returns a tuple: (is_anomalous: bool, list_of_reasons: list[str])
    """
    anomalies = []

    fuel_consumed = float(voyage_data.get("fuel_consumed_mt", 0))
    distance = float(voyage_data.get("distance_nm", 0))
    vessel_type = ship_data.get("vessel_type", "Other")

    # 1. Fuel capacity check (Impossible amounts)
    max_capacity = MAX_FUEL_CAPACITY.get(vessel_type, 10000.0)
    if fuel_consumed > max_capacity:
        anomalies.append(f"Fuel consumption ({fuel_consumed} MT) exceeds maximum plausible tank capacity for {vessel_type} ({max_capacity} MT).")

    # 2. Impossible fuel efficiency check (Zero or negative)
    if fuel_consumed <= 0 and distance > 0:
        anomalies.append("Fuel consumption is zero or negative while distance traveled is greater than zero.")

    # 3. Impossible speed check (e.g. crossing oceans in 1 hour)
    if "departure_time" in voyage_data and "arrival_time" in voyage_data:
        try:
            dep = voyage_data["departure_time"]
            arr = voyage_data["arrival_time"]
            hours = (arr - dep).total_seconds() / 3600.0

            if hours > 0 and distance > 0:
                speed_knots = distance / hours
                if speed_knots > 40.0:  # Even the fastest cargo ships rarely exceed 25-30 knots
                    anomalies.append(f"Calculated average speed ({round(speed_knots, 1)} knots) is impossibly high.")
        except Exception as e:
            logger.error(f"Error calculating speed anomaly: {str(e)}")

    # 4. Extreme inefficiency check (e.g. 100 MT per mile)
    if distance > 0:
        efficiency = fuel_consumed / distance
        if efficiency > 2.0:  # 2 MT per nautical mile is absurdly high
            anomalies.append(f"Fuel efficiency ({round(efficiency, 2)} MT/nm) indicates a massive fuel leak or typo.")

    return len(anomalies) > 0, anomalies
