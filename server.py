from flask import Flask, jsonify
import pvlib
import pandas as pd

app = Flask(__name__)

@app.route("/")
def home():
    return "Solar Tracking Server is Running 🚀"

@app.route("/sun")
def sun():
    location = pvlib.location.Location(
        latitude=23.0225,
        longitude=72.5714,
        tz='Asia/Kolkata'
    )

    time = pd.Timestamp.now(tz='Asia/Kolkata')
    times = pd.DatetimeIndex([time])

    solar_position = location.get_solarposition(times)

    zenith = solar_position['apparent_zenith'].iloc[0]
    azimuth = solar_position['azimuth'].iloc[0]

    tilt = 90 - zenith

    if tilt < 0:
        tilt = 0
    if tilt > 90:
        tilt = 90

    return jsonify({
        "azimuth": float(azimuth),
        "tilt": float(tilt)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
