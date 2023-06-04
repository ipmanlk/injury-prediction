from flask import Flask, jsonify, request
import pickle
import pandas as pd
from pathlib import Path
from database import check_user_data, initialize_database, store_user_data, get_user_data
from generate_model import generate_user_model, generate_default_model

# paths
MODELS_DIR = Path(__file__).parent / "models"

# Initialize database
initialize_database()

# Initialize default model
generate_default_model()

# Load general model
with open(MODELS_DIR / 'model.pkl', 'rb') as file:
    loaded_model = pickle.load(file)

app = Flask(__name__)

ongoing_alerts = {
    "123" : {
        "created_time": ""
    }
}

user_status = {
    "456" : {
        "heartRate": 78,
        "oxygenSaturation": 90,
        "temperature": 37,
        "systolicBloodPressure": 120,
        "diastolicBloodPressure": 80,
        "longitude": 10.123,
        "latitude": 15.123,
        "status": "normal",
        "policeLati": 123,
        "policeLong": 234,
        "ambuLati": 123,
        "ambuLong": 234,
    },
}

user_locations = {
    "123" : {
        "longitude": 0,
        "latitude": 0,
    },
    "456" : {
        "longitude": 0,
        "latitude": 0,
    },
    "789": {
        "longitude": 0,
        "latitude": 0,
    }
}


def get_blood_pressure(heart_rate, age=24, sex="male", weight=90, height=180, position="stand up"):
    R = 18.5  # Average R = 18.31; // Vascular resistance // Very hard to calculate from person to person
    Q = 5 if sex.lower() in ["male", "m"] else 4.5  # Liters per minute of blood through heart
    ejection_time = 386 - 1.64 * heart_rate if position.lower() != "laying down" else 364.5 - 1.23 * heart_rate
    body_surface_area = 0.007184 * (weight ** 0.425) * (height ** 0.725)
    stroke_volume = -6.6 + 0.25 * (ejection_time - 35) - 0.62 * heart_rate + 40.4 * body_surface_area - 0.51 * age
    pulse_pressure = abs(stroke_volume / ((0.013 * weight - 0.007 * age - 0.004 * heart_rate) + 1.307))
    mean_pulse_pressure = Q * R

    systolic_pressure = int(mean_pulse_pressure + 4.5 / 3 * pulse_pressure)
    diastolic_pressure = int(mean_pulse_pressure - pulse_pressure / 3)

    return systolic_pressure, diastolic_pressure

# POST request
@app.route('/process-sensor-data', methods=['POST'])
def setSensorData():
    data = request.get_json()

    uid = data['uid']
    heartRate = float(data['heartRate'])
    oxygenSaturation = float(data['oxygenSaturation'])
    temperature = float(data['temperature'])
    systolicBloodPressure, diastolicBloodPressure = get_blood_pressure(heartRate)

    new_data = pd.DataFrame({'heartRate': [heartRate], 'oxygenSaturation': [oxygenSaturation], 'temperature': [temperature], 'systolicBloodPressure': [systolicBloodPressure], 'diastolicBloodPressure': [diastolicBloodPressure]})


    user_model_path = Path(__file__).parent / "models" / f"{uid}.pkl"

    predictions = None

    # check if user model exists load it. otherwise load default model
    if user_model_path.exists(): 
        print("Using personalized model")
        with open(user_model_path, 'rb') as file:
            user_model = pickle.load(file)
       
        predictions = user_model.predict(new_data)

    else:
        print("Using default model")
        predictions = loaded_model.predict(new_data)

    # save data
    user_status[uid] = {
        "heartRate": heartRate,
        "oxygenSaturation": oxygenSaturation,
        "temperature": temperature,
        "systolicBloodPressure": systolicBloodPressure,
        "diastolicBloodPressure": diastolicBloodPressure,
        "status": predictions[0],
        "isEmergencyButtonPressed" : data["isEmergencyButtonPressed"]
    }

    has_enough_data = check_user_data(uid)

    # Save data in the database
    store_user_data(uid, user_status[uid])

    if has_enough_data:
        generate_user_model(uid)

    return user_status[uid]

# GET request
@app.route('/fetch-user-status', methods=['GET'])
def fetchData():
    uid = int(request.args.get('uid'))
    return {"userData":user_status[uid]}


# DELETE request
@app.route('/alert-status', methods=['DELETE'])
def setAlert():
    uid = request.args.get('uid')
    if uid in ongoing_alerts:
        del ongoing_alerts[uid]
        return jsonify({'result': True})


# endpoint for storing user location
@app.route('/store-user-location', methods=['POST'])
def storeUserLocation():
    data = request.get_json()

    uid = data['uid']
    longitude = data['longitude']
    latitude = data['latitude']

    user_locations[uid] = {
        "longitude": longitude,
        "latitude": latitude,
    }

    # return all user locations after json stringifying
    return {"userLocations":user_locations}


# endpoint for fetching user location
@app.route('/fetch-user-location', methods=['GET'])
def fetchUserLocation():
    uid = request.args.get('uid')
    return {"userLocation":user_locations[uid]}

app.run(debug=True)