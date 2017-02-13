import json
import yaml
import requests
from datetime import datetime


def light_on(yml_path="../config.yml"):
    with open(yml_path) as f:
        config = yaml.load(f)
    r = requests.get(
        "http://api.sunrise-sunset.org/json?lat={}&lng={}&date=today".format(
            config['longitude'], config['latitude'])
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


if __name__ == '__main__':
    print(light_on())
