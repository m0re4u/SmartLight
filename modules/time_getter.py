import json
import requests
from datetime import datetime


def light_on(config):
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
    else:
        raise requests.HTTPError('Could not connect to server, HTTP status code: {}'.format(r.status_code))


if __name__ == '__main__':
    import yaml
    with open('../config.yml') as f:
        config = yaml.load(f)
    print(light_on(config))
