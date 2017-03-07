import os
import json
import requests
from datetime import datetime


class DayTimer():
    def __init__(self):
        pass

    def start(self, config):
        if config['location_provider'] == 'automatic':
            # try automatic location provider
            lng, lat = self.get_location()
            if lng is not False and lat is not False:
                self.lng = lng
                self.lat = lat
                return
        print("Using manual location")
        self.lng = config['longitude']
        self.lat = config['latitude']

    def get_location(self):
        print('Getting location based on ip')
        ipdata = requests.get('http://myexternalip.com/raw')
        if ipdata.status_code == 200:
            ip = ipdata.text.strip()
        r = requests.get("http://freegeoip.net/json/{}".format(ip))
        if r.status_code == 200:
            loc_data = json.loads(r.text)
            return loc_data['longitude'], loc_data['latitude']
        else:
            return False, False

    def light_on(self, config):
        r = requests.get(
            "http://api.sunrise-sunset.org/json"
            "?lat={}&lng={}&date=today".format(self.lat, self.lng)
        )
        if r.status_code == 200:
            now = datetime.now()
            data = json.loads(r.text)
            sunrise = datetime.strptime(
                data['results']['sunrise'], '%I:%M:%S %p').time()
            sunset = datetime.strptime(
                data['results']['sunset'], '%I:%M:%S %p').time()
            if sunrise < now.time() < sunset:
                print("It's {}, and the sun is shining!".format(now.time()))
                return False, False, False
            else:
                print("It's {}, and the light is on!".format(now.time()))
                return True, True, True
        else:
            raise requests.HTTPError('Could not connect to server, HTTP status'
                                     ' code: {}'.format(r.status_code))


if __name__ == '__main__':
    import yaml
    with open('../config.yml') as f:
        config = yaml.load(f)
    day = DayTimer()
    day.start(config)
    print(day.light_on(config))
