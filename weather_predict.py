import yr_weather
import json

def get_weather():
    headers = {
        "User-agent": "acmeweathersite.com support@acmeweathersite.com"
    }
    location = (49.3931, 15.1775)

    client = yr_weather.Locationforecast(headers=headers)
    weather = client.get_forecast(*location)._timeseries

    future = []
    for w in range(16):
        weather_object = [
            {
                'time': weather[w]['time'],
                'aktualni_data': {
                    'aktualni_teplota': weather[w]['data']['instant']['details'].get('air_temperature'),
                    'celkova_oblacnost': weather[w]['data']['instant']['details'].get('cloud_area_fraction'),
                    'relativni_vlhkost': weather[w]['data']['instant']['details'].get('relative_humidity'),
                    'rychlost_vetru': weather[w]['data']['instant']['details'].get('wind_speed'),
                    'smer_vetru': weather[w]['data']['instant']['details'].get('wind_from_direction'),
                },
                'predpoved': {
                    'dest_za_1h': weather[w]['data']['next_1_hours']['details'].get('precipitation_amount'),
                    'dest_za_6h': weather[w]['data']['next_6_hours']['details'].get('precipitation_amount'),
                    'dest_za_12': weather[w]['data']['next_6_hours']['details'].get('precipitation_amount')
                }
            }
        ]
        future.append(weather_object)

    return future

def average_temp(future):
    total_temperature = 0
    for i in future:
        total_temperature += i[0]['aktualni_data'].get('aktualni_teplota')
    return round(total_temperature/len(future), 1)

def get_clouds(future):
    total_clouds = 0
    for i in future:
        total_clouds += i[0]['aktualni_data'].get('celkova_oblacnost')
    return total_clouds/len(future)

def get_max_temp(future):
    max_temp = 0
    time = ''
    for i in future:
        t = i[0]['aktualni_data'].get('aktualni_teplota')
        if t > max_temp:
            max_temp = t
            time = i[0]['time']
    return max_temp, time

def get_min_temp(future):
    min_temp = 99
    time = ''
    for i in future:
        t = i[0]['aktualni_data'].get('aktualni_teplota')
        if t < min_temp:
            min_temp = t
            time = i[0]['time']
    return min_temp, time

def main():
    # future = get_weather()
    with open('out.json', 'r') as f:
        future = json.load(f)

    print(json.dumps(future, indent=4))

if __name__ == "__main__":
    main()
