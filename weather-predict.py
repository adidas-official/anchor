import json
import requests
import yr_weather
from datetime import datetime, timedelta

def get_weather():
    headers = {
        "User-agent": "acmeweathersite.com support@acmeweathersite.com"
    }
    location = (49.3931, 15.1775)

    # client = yr_weather.Locationforecast(headers=headers)
    now = datetime.now()
    next_hour = now + timedelta(hours=1)
    print(next_hour.strftime(format="%Y-%M-%d"))

    # ondrejov_now = client.get_forecast(*location).get_forecast_time(datetime(2026,10,25,14,0,0,0, tzinfo))
    # print(dir(ondrejov_now))

def main():
    get_weather()

if __name__ == "__main__":
    main()
