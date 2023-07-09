import json
import os
import logging
import sys

import pytz
import requests
from wallbox import Wallbox
import datetime
from datetime import datetime

wallbox_user = os.environ['WALLBOX_USER']
wallbox_pwd = os.environ['WALLBOX_PASSWORD']
wallbox_charger_id = os.environ['WALLBOX_CHARGER_ID']

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger("wallbox-auto-unlocker")


# handler = logging.StreamHandler(sys.stdout)
# handler.setLevel(logging.INFO)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)
# logger.addHandler(handler)


def get_current_hour():
    now = datetime.now(tz=pytz.timezone('Europe/Madrid'))
    logger.info(f"The current date and time is {now}")
    return now.hour


def is_solar_hour(hour):
    return 11 <= hour <= 18


def should_be_unlock(pvcp_prices):
    cheap_hours = filter_cheap_hours(pvcp_prices)
    under_avg_hours = filter_under_avg_hours(pvcp_prices)

    current_hour = get_current_hour()
    return current_hour in cheap_hours or current_hour in under_avg_hours or is_solar_hour(current_hour)


def get_pvcp_prices():
    response = requests.get("https://api.preciodelaluz.org/v1/prices/all?zone=PCB")
    prices = {}
    for k, v in response.json().items():
        hour = int(k.split("-")[0])
        prices[hour] = v
    return prices


def filter_cheap_hours(pvpc_prices):
    cheap_hours = {}
    for k, v in pvpc_prices.items():
        if v['is-cheap']:
            cheap_hours[k] = v
    return cheap_hours


def filter_under_avg_hours(pvpc_prices):
    under_avg_hours = {}
    for k, v in pvpc_prices.items():
        if v['is-under-avg'] and not v['is-cheap']:
            under_avg_hours[k] = v
    return under_avg_hours


def main():
    pvpc_prices = get_pvcp_prices()
    myWallbox = Wallbox(wallbox_user, wallbox_pwd)

    # Authenticate with the credentials above
    myWallbox.authenticate()
    chargerStatus = myWallbox.getChargerStatus(wallbox_charger_id)
    logger.info(f"Charger Status: {json.dumps(chargerStatus, indent=2)}")

    if should_be_unlock(pvpc_prices):
        logger.info("Unlocking charger")
        # myWallbox.unlockCharger(wallbox_charger_id)
    else:
        logger.info("Locking charger")
        # myWallbox.lockCharger(wallbox_charger_id)


if __name__ == '__main__':
    main()
