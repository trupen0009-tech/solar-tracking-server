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
    # 2. Real-time current time
    # -----------------------------
    current_time = pd.Timestamp.now(tz="Asia/Kolkata")
    times = pd.DatetimeIndex([current_time])

    # -----------------------------
    # 3. Solar position from pvlib
    # -----------------------------
    solar_position = location.get_solarposition(times)

    zenith = float(solar_position["apparent_zenith"].iloc[0])
    azimuth = float(solar_position["azimuth"].iloc[0])

    # Elevation = sun height above horizon
    elevation = 90 - zenith

    # -----------------------------
    # 4. Sun visibility logic
    # -----------------------------
    # zenith <= 88 means sun is clearly above horizon
    sun_visible = zenith <= 88

    # Real sunrise/sunset is not always exactly 90° and 270°
    # So we allow a wider useful direction range.
    direction_valid = 60 <= azimuth <= 300

    tracking_allowed = sun_visible and direction_valid

    # -----------------------------
    # 5. Convert pvlib azimuth to our tracker angle
    # -----------------------------
    if tracking_allowed:

        # pvlib:
        # East  = 90°
        # South = 180°
        # West  = 270°
        #
        # Our tracker:
        # East  = 0°
        # South = 90°
        # West  = 180°
        track_angle = azimuth - 90
        track_angle = clamp(track_angle, 0, 180)

        # Panel tilt from horizontal = zenith
        # Sun overhead → zenith small → panel flatter
        # Sun low → zenith large → panel more vertical
        tilt = clamp(zenith, 0, 90)

    else:
        # Night / invalid direction mode
        # Panel returns to home position
        track_angle = 0
        tilt = 0

    # -----------------------------
    # 6. Send response to ESP32
    # -----------------------------
    return jsonify({
        "time": str(current_time),

        "sun_visible": bool(sun_visible),
        "direction_valid": bool(direction_valid),
        "tracking_allowed": bool(tracking_allowed),

        "pvlib_azimuth": azimuth,
        "zenith": zenith,
        "elevation": elevation,

        "track_angle": float(track_angle),
        "tilt": float(tilt)
    })


if __name__ == "__main__":
    app.run()
