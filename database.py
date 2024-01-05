import sqlite3
from datetime import datetime

import requests

import config

conn = sqlite3.connect('test.db')

conn.execute('''CREATE TABLE IF NOT EXISTS CHATHISTORY
         (ID INTEGER PRIMARY KEY AUTOINCREMENT,
         QUERY TEXT NOT NULL,
         RESPONSE TEXT NOT NULL,
         SESSIONID TEXT NOT NULL,
         CREATEDAT TEXT NOT NULL);''')


def add_conversation(query: str, response: str, session_id: str) -> None:
    created_at = datetime.now()
    conn.execute(
        f"INSERT INTO CHATHISTORY (QUERY, RESPONSE, SESSIONID, CREATEDAT) \
VALUES ('{query}', '{response}', '{session_id}', '{created_at}');")
    conn.commit()
    print('Conversation added.')

    return None


def get_car_information(brand: str = None, model: str = None, fuel_type: str = None) -> dict:
    payload = {}
    if brand is not None:
        payload.update({'brand': brand})
    if model is not None:
        payload.update({'model': model})
    if fuel_type is not None:
        payload.update({'fuel_type': fuel_type})
    try:
        response = requests.post(
            f'{config.BACKEND_URL}/api/get_filtered_channel_fast', json=payload)
        response = response.json()
        car_data = []
        count = 3
        if response['ok']:
            for _, v in response['data'].items():
                if count == 0:
                    break
                count -= 1
                car_data.append({
                    'brand': v['brand'],
                    'model': v['model'],
                    'price': v['price'],
                    'year': v['year'],
                    'mileage': v['mileage'],
                    'transmission': v['transmission']
                })

        return car_data
    except:
        return []


def get_brand_information() -> dict:
    payload = {}
    try:
        response = requests.get(
            f'{config.BACKEND_URL}/api/autoscout_brands', json=payload)
        brand_data = response.json()

        return brand_data
    except:
        return []


def get_model_information(brand: str) -> dict:
    payload = {}
    try:
        response = requests.get(
            f'{config.BACKEND_URL}/api/autoscout_models?brand={brand}', json=payload)
        model_data = dict(response.json())
        model_data = list(model_data.keys())
        return model_data
    except:
        return []
