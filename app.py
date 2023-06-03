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

# POST request
@app.route('/process-sensor-data', methods=['POST'])
def setSensorData():
    data = request.get_json()

    uid = data['uid']
    heartRate = float(data['heartRate'])
    oxygenSaturation = float(data['oxygenSaturation'])
    temperature = float(data['temperature'])
    systolicBloodPressure = float(data['systolicBloodPressure'])
    diastolicBloodPressure = float(data['diastolicBloodPressure'])
    longitude = float(data['longitude'])
    latitude = float(data['latitude'])
    policeLati  = float(data['policeLati'])
    policeLong  = float(data['policeLong'])
    ambuLati  = float(data['ambuLati'])
    ambuLong  = float(data['ambuLong'])

    new_data = pd.DataFrame({'heartRate': [heartRate], 'oxygenSaturation': [oxygenSaturation], 'temperature': [temperature], 'systolicBloodPressure': [systolicBloodPressure], 'diastolicBloodPressure': [diastolicBloodPressure]})


    user_model_path = Path(__file__).parent / "models" / f"{uid}.pkl"

    predictions = None

    # check if user model exists load it. otherwise load default model
    if user_model_path.exists(): 
        print("Using user model")
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
        "longitude": longitude,
        "latitude": latitude,
        "policeLati": policeLati,
        "policeLong": policeLong,
        "ambuLati": ambuLati,
        "ambuLong": ambuLong,
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


app.run(debug=True)