from flask import Flask, jsonify
import pvlib
import pandas as pd

app = Flask(__name__)

# -----------------------------
# Helper function
# -----------------------------
def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


@app.route("/")
def home():
    return "Solar Tracking Server is Running 🚀"


@app.route("/sun")
def sun():

    # -----------------------------
    # 1. Location
    # -----------------------------
    location = pvlib.location.Location(
        latitude=23.0225,
        longitude=72.5714,
        tz="Asia/Kolkata"
    )

    # -----------------------------
    # 2. Current real-time
    # -----------------------------
    current_time = pd.Timestamp.now(tz="Asia/Kolkata")

    # -----------------------------
    # 3. Current solar position
    # -----------------------------
    current_times = pd.DatetimeIndex([current_time])
    solar_position = location.get_solarposition(current_times)

    zenith = float(solar_position["apparent_zenith"].iloc[0])
    azimuth = float(solar_position["azimuth"].iloc[0])

    elevation = 90 - zenith

    # -----------------------------
    # 4. Calculate today's sunrise/sunset time
    # -----------------------------
    today = current_time.normalize()
    day_index = pd.DatetimeIndex([today])

    sun_times = location.get_sun_rise_set_transit(day_index)

    sunrise_time = sun_times["sunrise"].iloc[0]
    sunset_time = sun_times["sunset"].iloc[0]

    # -----------------------------
    # 5. Calculate sunrise/sunset azimuth
    # -----------------------------
    sunrise_pos = location.get_solarposition(pd.DatetimeIndex([sunrise_time]))
    sunset_pos = location.get_solarposition(pd.DatetimeIndex([sunset_time]))

    sunrise_azimuth = float(sunrise_pos["azimuth"].iloc[0])
    sunset_azimuth = float(sunset_pos["azimuth"].iloc[0])

    # -----------------------------
    # 6. Day/night visibility logic
    # -----------------------------
    time_visible = sunrise_time <= current_time <= sunset_time

    # 88° instead of 90° avoids weak horizon tracking
    height_visible = zenith <= 88

    sun_visible = time_visible and height_visible

    # -----------------------------
    # 7. Dynamic seasonal mapping
    # -----------------------------
    if sun_visible and sunset_azimuth != sunrise_azimuth:

        # Formula:
        # current position between today's sunrise and sunset
        progress = (azimuth - sunrise_azimuth) / (sunset_azimuth - sunrise_azimuth)

        # Convert progress into motor range 0° to 180°
        track_angle = progress * 180

        # Safety limit for servo
        track_angle = clamp(track_angle, 0, 180)

        # Panel tilt from horizontal = zenith
        tilt = clamp(zenith, 0, 90)

        tracking_allowed = True

    else:
        # Night / weak sun / invalid condition
        track_angle = 0
        tilt = 0
        tracking_allowed = False

    # -----------------------------
    # 8. Send response to ESP32
    # -----------------------------
    return jsonify({
        "time": str(current_time),

        "sunrise_time": str(sunrise_time),
        "sunset_time": str(sunset_time),

        "sun_visible": bool(sun_visible),
        "tracking_allowed": bool(tracking_allowed),

        "pvlib_azimuth": azimuth,
        "zenith": zenith,
        "elevation": elevation,

        "sunrise_azimuth": sunrise_azimuth,
        "sunset_azimuth": sunset_azimuth,

        "track_angle": float(track_angle),
        "tilt": float(tilt)
    })


if __name__ == "__main__":
    app.run()
