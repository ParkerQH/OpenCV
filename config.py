import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate("./serviceAccountKey.json")
firebase_admin.initialize_app(
    cred, {"databaseURL": "https://capstone-ce8e9-default-rtdb.firebaseio.com/"}
    )
