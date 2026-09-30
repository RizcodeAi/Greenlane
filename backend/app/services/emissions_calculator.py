"""IMO Emissions Calculation Engine for GreenLane Maritime MVP."""

# IMO emission factors (t-CO2 / t-fuel)
IMO_CO2_FACTORS: dict = {
    "HFO": 3.114,
    "MGO": 3.206,
    "LNG": 2.750,
    "Methanol": 1.375,
}

# IMO default factors for other pollutants
IMO_CH4_FACTORS: dict = {"HFO": 0.00005, "MGO": 0.00005, "LNG": 0.0001, "Methanol": 0.00002}
IMO_N2O_FACTORS: dict = {"HFO": 0.00018, "MGO": 0.00018, "LNG": 0.00011, "Methanol": 0.00005}
IMO_SOx_FACTORS: dict = {"HFO": 0.02, "MGO": 0.002, "LNG": 0.0, "Methanol": 0.0}
IMO_NOx_FACTORS: dict = {"HFO": 0.078, "MGO": 0.078, "LNG": 0.015, "Methanol": 0.035}

# Global Warming Potential (GWP100) multipliers
GWP100: dict = {"CO2": 1, "CH4": 28, "N2O": 265}


def calculate_voyage_emissions(
    fuel_type: str,
    fuel_consumed_mt: float,
    distance_nm: float,
    cargo_mt: float = 0.0,
) -> dict:
    """Calculate full voyage emissions based on IMO factors.

    Args:
        fuel_type: One of HFO, MGO, LNG, Methanol
        fuel_consumed_mt: Fuel consumed in metric tonnes
        distance_nm: Distance in nautical miles
        cargo_mt: Cargo mass in metric tonnes (default 0)

    Returns:
        Dictionary with co2_tonnes, ch4_tonnes, n2o_tonnes, sox_tonnes,
        nox_tonnes, co2_equivalent_tonnes, transport_work, eeoi
    """
    fuel_type = fuel_type.upper()
    co2_factor = IMO_CO2_FACTORS[fuel_type]
    ch4_factor = IMO_CH4_FACTORS[fuel_type]
    n2o_factor = IMO_N2O_FACTORS[fuel_type]
    sox_factor = IMO_SOx_FACTORS[fuel_type]
    nox_factor = IMO_NOx_FACTORS[fuel_type]

    co2_tonnes = fuel_consumed_mt * co2_factor
    ch4_tonnes = fuel_consumed_mt * ch4_factor
    n2o_tonnes = fuel_consumed_mt * n2o_factor
    sox_tonnes = fuel_consumed_mt * sox_factor
    nox_tonnes = fuel_consumed_mt * nox_factor

    # GWP-weighted CO2 equivalent
    co2_equivalent_tonnes = (
        co2_tonnes * GWP100["CO2"]
        + ch4_tonnes * GWP100["CH4"]
        + n2o_tonnes * GWP100["N2O"]
    )

    transport_work = distance_nm * cargo_mt  # tonne-miles

    if cargo_mt > 0 and distance_nm > 0:
        eeoi = (co2_tonnes * 1e6) / (cargo_mt * distance_nm)
    else:
        eeoi = None

    return {
        "co2_tonnes": round(co2_tonnes, 6),
        "ch4_tonnes": round(ch4_tonnes, 8),
        "n2o_tonnes": round(n2o_tonnes, 8),
        "sox_tonnes": round(sox_tonnes, 6),
        "nox_tonnes": round(nox_tonnes, 6),
        "co2_equivalent_tonnes": round(co2_equivalent_tonnes, 6),
        "transport_work": round(transport_work, 2),
        "eeoi": round(eeoi, 4) if eeoi is not None else None,
    }
