import pandas as pd
import requests
import json

class birdScrapper:
    def __init__(self, guid, email):
        self.guid = guid
        self.email = email

    def authenticate(self):
        url = "https://api-auth.prod.birdapp.com/api/v1/auth/email"

        headers = {
            "User-Agent": "Bird/4.119.0(co.bird.Ride; build:3; iOS 14.3.0) Alamofire/5.2.2",
            "Device-Id": self.guid,
            "Platform": "ios",
            "App-Version": "4.119.0",
            "Content-Type": "application/json"
        }

        payload = {
            "email": self.email
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            return response.json()  # Assuming the API returns JSON
        else:
            return f"Failed to authenticate. Status code: {response.status_code}, Response: {response.text}"

    def