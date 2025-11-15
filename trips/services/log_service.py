from .hos_logic import build_daily_log

def generate_log_sheet(distance_miles: float, current_cycle_used: float):
    return build_daily_log(distance_miles, current_cycle_used)
