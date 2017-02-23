import urllib.request
import bs4


def light_on(config):

    url = "http://nl.quoteweb.com/nl-nl/fonds-detail/koers/?id=12272&title=aex"
    content = urllib.request.urlopen(url).read()
    soup = bs4.BeautifulSoup(content, 'html.parser')

    up_down = soup.find('tbody').find_all('tr')[1].find_all('td')[1]['class'][0]
    if up_down == 'up':
        return False, True, False
    else:
        return True, False, False


if __name__ == '__main__':
    import yaml
    with open('../config.yml') as f:
        config = yaml.load(f)
    print(light_on(config))
