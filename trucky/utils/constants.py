import os

FMCSA_CONSTANTS = {
    "DAILY_DRIVE_LIMIT": float(os.getenv("FMCSA_DAILY_DRIVE_LIMIT", 11)),
    "DAILY_DUTY_LIMIT": float(os.getenv("FMCSA_DAILY_DUTY_LIMIT", 14)),     
    "CYCLE_LIMIT": float(os.getenv("FMCSA_CYCLE_LIMIT", 70)),               
    "REQUIRED_BREAK_HOURS": 0.5,   
    "REST_RESET_HOURS": 10.0,      
}

AVERAGE_SPEED_MPH = float(os.getenv("AVERAGE_SPEED_MPH", 55))
