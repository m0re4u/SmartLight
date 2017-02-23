import urllib.request
import bs4


def light_on(config):

    url = "http://www.kanikeenkortebroekaan.nl"
    content = urllib.request.urlopen(url).read()
    soup = bs4.BeautifulSoup(content, 'lxml')

    ja_nee = soup.find('body')['class'][0]
    if ja_nee == 'nee':
        return False, False, False
    else:
        return True, True, True


if __name__ == '__main__':
    import yaml
    with open('../config.yml') as f:
        config = yaml.load(f)
    print(light_on(config))