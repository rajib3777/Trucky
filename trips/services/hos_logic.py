from trucky.utils.constants import FMCSA_CONSTANTS, AVERAGE_SPEED_MPH


def compute_driving_hours(distance_miles: float) -> float:
    return distance_miles / AVERAGE_SPEED_MPH


def build_daily_log(distance_miles: float, current_cycle_used: float):
    """
    এক দিনের জন্য HOS-compliant log তৈরি করবে।
    Timeline = 0–24 (midnight-to-midnight), তোমার LogSheet.js grid অনুযায়ী।:contentReference[oaicite:3]{index=3}
    """

    driving_hours = compute_driving_hours(distance_miles)

    # Daily driving cap (11h)
    driving_hours = min(driving_hours, FMCSA_CONSTANTS["DAILY_DRIVE_LIMIT"])

    grid = []
    current_time = 0.0

    # 0–6: Off Duty (sleep)
    grid.append({"status": "Off Duty", "start": current_time, "end": 6.0})
    current_time = 6.0

    # 6–7: On Duty (pre-trip, inspection)
    grid.append({"status": "On Duty", "start": 6.0, "end": 7.0})
    current_time = 7.0
    on_duty_hours = 1.0

    # প্রথম driving leg: max 8 hours before required 30min break
    first_leg = min(driving_hours, 8.0)
    grid.append({"status": "Driving", "start": current_time, "end": current_time + first_leg})
    current_time += first_leg
    total_driving = first_leg

    # যদি driving_hours > 8 হয়, তাহলে ৩০ মিনিট break এবং তারপর বাকিটা
    if driving_hours > 8.0:
        # 30-min break
        grid.append({"status": "Off Duty", "start": current_time, "end": current_time + 0.5})
        current_time += 0.5

        remaining_drive = driving_hours - 8.0
        grid.append({"status": "Driving", "start": current_time, "end": current_time + remaining_drive})
        current_time += remaining_drive
        total_driving = driving_hours

    # Post-trip inspection: 0.5h
    grid.append({"status": "On Duty", "start": current_time, "end": current_time + 0.5})
    on_duty_hours += 0.5
    current_time += 0.5

    # দিনের বাকি সময় Off Duty
    if current_time < 24.0:
        grid.append({"status": "Off Duty", "start": current_time, "end": 24.0})
        off_duty_hours = (6.0 - 0.0) + (24.0 - current_time)
    else:
        off_duty_hours = (6.0 - 0.0)

    sleeper_hours = 0.0  # sleeper row এখন ফাঁকা রাখা হচ্ছে (future expansion)

    totals = {
        "offDuty": round(off_duty_hours, 2),
        "sleeper": round(sleeper_hours, 2),
        "driving": round(total_driving, 2),
        "onDuty": round(on_duty_hours, 2),
    }

    # Recap calculation
    today_on_duty = total_driving + on_duty_hours
    total_last_7 = current_cycle_used
    total_with_today = min(FMCSA_CONSTANTS["CYCLE_LIMIT"], total_last_7 + today_on_duty)
    hours_available_tomorrow = max(0.0, FMCSA_CONSTANTS["CYCLE_LIMIT"] - total_with_today)

    recap = {
        "totalHoursLast7Days": round(total_last_7, 2),
        "totalHoursAvailableTomorrow": round(hours_available_tomorrow, 2),
    }

    driver_info = {
        "totalMilesDrivingToday": round(distance_miles, 2),
        "totalMileageToday": round(distance_miles, 2),
    }

    return {
        "grid": grid,
        "totals": totals,
        "recap": recap,
        "driverInfo": driver_info,
    }


