import math

def calculate_rig_power(rig_data: dict) -> dict:
    """
    Calculates the total power consumption of the rig based on the provided rig data.
    
    Args:
        rig_data (dict): The dictionary containing the rig setup configuration.
        
    Returns:
        dict: A dictionary containing the calculated power metrics or None if no power is used.
              Keys: total_watt, total_kw, apparent_kva, current_1ph, current_3ph, cos_phi, total_power
    """
    if not rig_data:
        rig_data = {}

    def _to_float(value):
        try:
            s = str(value).strip().replace(",", ".")
            return float(s) if s else 0.0
        except Exception:
            return 0.0

    # Calculate total watt from fixture items
    prefixes = ("spots", "washes", "beams", "blinders", "strobes")
    total_watt = 0.0
    for prefix in prefixes:
        items = rig_data.get(f"{prefix}_items")
        if items:
            for it in items:
                w = _to_float(it.get("watt") or 0)
                try:
                    cnt = int((it.get("count") or "0").strip() or 0)
                except Exception:
                    cnt = 0
                total_watt += w * cnt
        else:
            # Fallback for old data structure or direct input
            total_watt += _to_float(rig_data.get(f"watt_{prefix}"))

    # Add custom devices if any
    custom_devices = rig_data.get("custom_devices", [])
    if custom_devices:
        for cd in custom_devices:
            w = _to_float(cd.get("watt") or 0)
            try:
                cnt = int((cd.get("count") or "0").strip() or 0)
            except Exception:
                cnt = 0
            total_watt += w * cnt

    # Sum of manual power entries (Main, Light, Sound, etc.)
    power_fields = ["power_main", "power_light", "power_sound", "power_video", "power_foh", "power_other"]
    total_power = sum(_to_float(rig_data.get(f)) for f in power_fields)

    if total_watt <= 0 and total_power <= 0:
        return None

    result = {
        "total_watt": total_watt if total_watt > 0 else None,
        "total_kw": None,
        "apparent_kva": None,
        "current_1ph": None,
        "current_3ph": None,
        "cos_phi": None,
        "total_power": total_power if total_power > 0 else None,
    }

    if total_watt > 0:
        cos_phi = 0.95  # Assumed power factor
        total_kw = total_watt / 1000.0
        apparent_kva = total_kw / cos_phi
        
        # 1-phase 230V
        current_1ph = total_watt / (230.0 * cos_phi)
        
        # 3-phase 400V symmetric: P = sqrt(3) * U * I * cos phi
        current_3ph = total_watt / (math.sqrt(3.0) * 400.0 * cos_phi)

        result.update({
            "total_kw": total_kw,
            "apparent_kva": apparent_kva,
            "current_1ph": current_1ph,
            "current_3ph": current_3ph,
            "cos_phi": cos_phi
        })

    return result
