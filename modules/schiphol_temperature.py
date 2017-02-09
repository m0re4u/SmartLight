import urllib.request
import bs4


def light_on(measuring_location='Schiphol', temperature_threshold=10):
    url = 'http://www.knmi.nl/nederland-nu/weer/waarnemingen'
    content = urllib.request.urlopen(url).read()
    soup = bs4.BeautifulSoup(content, 'lxml')

    measurements = soup.find('tbody').find_all('tr')

    correct_place = -1
    for measurement in measurements:
        if measurement.find('td').string==measuring_location:
            correct_place = measurement

    if correct_place == -1:
        print('Measuring location could not be found on the KNMI website.')
        return False

    if float(correct_place.find_all('td')[2].string) >= temperature_threshold:
        return True
    else:
        return False


if __name__ == '__main__':
    print(light_on())
