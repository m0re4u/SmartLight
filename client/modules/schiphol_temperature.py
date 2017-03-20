import urllib.request
import bs4


def light_on(config):
    measuring_location = config['temperature_measurement_location']
    temperature_threshold = config['temperature_threshold']


    url = 'http://www.knmi.nl/nederland-nu/weer/waarnemingen'
    content = urllib.request.urlopen(url).read()
    soup = bs4.BeautifulSoup(content, 'html.parser')

    measurements = soup.find('tbody').find_all('tr')

    correct_place = -1
    for measurement in measurements:
        if measurement.find('td').string==measuring_location:
            correct_place = measurement

    if correct_place == -1:
        print('Measuring location could not be found on the KNMI website.')
        return False, False, False

    if float(correct_place.find_all('td')[2].string) >= temperature_threshold:
        return True, True, True
    else:
        return False, False, False


if __name__ == '__main__':
    import yaml
    with open('../config.yml') as f:
        config = yaml.load(f)
    print(light_on(config))
