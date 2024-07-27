import pandas as pd
import requests
import json
import logging
from geopy.distance import distance
from datetime import datetime

MAX_SCOOTERS_PER_CALL = 250

class BirdScrapper:
    def __init__(self, email, guid, access_token, refresh_token):
        self.guid = guid
        self.email = email
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.logger = logging.getLogger(__name__)

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

    def use_magic_link(self, token):
        url = "https://api-auth.prod.birdapp.com/api/v1/auth/magic-link/use"

        headers = {
            "User-Agent": "Bird/4.119.0(co.bird.Ride; build:3; iOS 14.3.0) Alamofire/5.2.2",
            "Device-Id": self.guid,
            "Platform": "ios",
            "App-Version": "4.119.0",
            "Content-Type": "application/json"
        }

        payload = {
            "token": token
        }

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            return data  # Assuming the API returns JSON with 'access' and 'refresh' keys
        else:
            return f"Failed to use magic link. Status code: {response.status_code}, Response: {response.text}"

    def get_new_token(self):
        """
        This function only perform the refresh, it does not update the object, for this, use `update_token`
        :return: dict with the new tokens
        """
        url = "https://api-auth.prod.birdapp.com/api/v1/auth/refresh/token"

        headers = {
            "User-Agent": "Bird/4.119.0(co.bird.Ride; build:3; iOS 14.3.0) Alamofire/5.2.2",
            "Device-Id": self.guid,
            "Platform": "ios",
            "App-Version": "4.119.0",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.refresh_token}"
        }

        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            return data  # Assuming the API returns JSON with 'access' and 'refresh' keys
        else:
            self.logger.warning(f"Failed to use magic link. Status code: "
                                f"{response.status_code}, Response: {response.text}")
            return f"Failed to use magic link. Status code: {response.status_code}, Response: {response.text}"

    def update_token(self, token_dict: dict):
        self.access_token = token_dict['access']
        self.refresh_token = token_dict['refresh']

    def request_scooter_locations(self, lat, long, radius=1000):
        url = "https://api-bird.prod.birdapp.com/bird/nearby"
        params = {
            "latitude": lat,
            "longitude": long,
            "radius": radius
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": "Bird/4.119.0(co.bird.Ride; build:3; iOS 14.3.0) Alamofire/5.2.2",
            "legacyrequest": "false",
            "Device-Id": self.guid,
            "App-Version": "4.119.0",
            "App-Name": "bird",  # was missing
            "Location": json.dumps(
                {"latitude": lat, "longitude": long, "altitude": 500, "accuracy": 65, "speed": -1, "heading": -1})
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(response.text)
            self.logger.warning(f"Failed to retrieve scooter locations. Status code: {response.status_code}, Response: {response.text}")

    def get_city_scooters(self, location_list, radius) -> pd.DataFrame:
        """
        get all the scooters in the area defined by the grid location_list
        :param location_list: a list of locations in a tuple format (lon, lat)
        :param radius: the radius distance that covers
        :return:
        """
        scooter_locations = []
        for location in location_list:
            new_scooters = self.request_scooter_locations(location[0], location[1], radius)[
                'birds']
            if isinstance(new_scooters, str):
                self.logger.warning("did not receive 200, received:\n" + new_scooters)
                break
            if len(new_scooters) >= MAX_SCOOTERS_PER_CALL:
                self.logger.warning(f"warning, request got saturated: {len(new_scooters)=}")
            if len(new_scooters)>0 and not 'brand_id' in new_scooters[0]:
                print("got here")
                self.logger.warning(f"brand_id problem. aborting.")
                break
            scooter_locations += new_scooters
            print(f'{len(scooter_locations)=}')

        # Initialize an empty DataFrame
        df = pd.DataFrame(
            columns=['id', 'latitude', 'longitude', 'code', 'model', 'brand_id', 'vehicle_class', 'captive',
                     'partner_id', 'battery_level', 'estimated_range', 'area_key', 'has_helmet', 'bounty_id'])


        # Insert unique scooters into DataFrame
        for scooter in scooter_locations:
            scooter_flat = self.flatten_location(scooter)
            if scooter_flat['id'] not in df['id'].values:
                df = pd.concat([df, pd.DataFrame([scooter_flat])], ignore_index=True)

        df['time'] = datetime.now()

        return df

    @staticmethod
    def create_grid(start_lat, start_long, rows, cols, spacing):
        points = []
        for i in range(rows):
            for j in range(cols):
                point = distance(meters=i * spacing).destination((start_lat, start_long), 180)  # South
                point = distance(meters=j * spacing).destination((point.latitude, point.longitude), 90)  # East
                points.append((point.latitude, point.longitude))
        return points

    # Function to flatten the location dictionary
    @staticmethod
    def flatten_location(data):
        flattened_data = data.copy()
        for key, value in data['location'].items():
            flattened_data[key] = value
        del flattened_data['location']
        return flattened_data