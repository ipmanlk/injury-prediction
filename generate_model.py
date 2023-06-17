import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
import pickle
from database import get_user_data
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

DATASET_PATH = Path(__file__).parent / "csv" / "data.csv"
DEFAULT_MODEL_PATH = Path(__file__).parent / "models" / "model.pkl"

def generate_default_model():
  df = pd.read_csv(DATASET_PATH)
  df.columns = df.columns.str.strip()
  
  X = df.drop(['OUTPUT', "systolicBloodPressure", "diastolicBloodPressure"], axis=1)
  y = df['OUTPUT']
  
  X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
  
  model = RandomForestClassifier()
  model.fit(X_train, y_train)
  
  y_pred = model.predict(X_test)
  
  print('Accuracy:', accuracy_score(y_test, y_pred))
  print('Confusion Matrix:', confusion_matrix(y_test, y_pred))

  with open(DEFAULT_MODEL_PATH, 'wb') as file:
    pickle.dump(model, file)


def generate_user_model(uid):
    # Load csv dataset
    df = pd.read_csv(DATASET_PATH)
    df.columns = df.columns.str.strip()

    # Filter abnormal entries
    csv_entries = df[df['OUTPUT'] == 'Abnormal']
    csv_entries = csv_entries.drop(["systolicBloodPressure", "diastolicBloodPressure"], axis=1)

    # Get user data from database
    user_data = get_user_data(uid)

    # Transform the user data into a DataFrame
    user_df = pd.DataFrame(user_data, columns=['id', 'uid', 'created_time', 'heartRate', 'oxygenSaturation', 'temperature', 'systolicBloodPressure', 'diastolicBloodPressure', 'status'])

    user_df_status = user_df['status']
    user_df = user_df.drop(['id', 'uid', 'created_time', "status", "systolicBloodPressure", "diastolicBloodPressure"], axis=1)
    user_df['OUTPUT'] = user_df_status

    # merge the user_df with the user_entries
    csv_entries = pd.concat([csv_entries, user_df])


    # Split the dataset into X and y
    X = csv_entries.drop('OUTPUT', axis=1)
    y = csv_entries['OUTPUT']

    # Split the dataset into train and test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Create the model
    model = RandomForestClassifier()
    model.fit(X_train, y_train)

    # Save the model
    model_path = Path(__file__).parent / "models" / f"{uid}.pkl"
    with open(model_path, 'wb') as file:
        pickle.dump(model, file)        