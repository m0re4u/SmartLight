import yaml
import twitter
from afinn import Afinn

def light_on(yml_path=".api_key"):
    with open(yml_path) as f:
        config = yaml.load(f)


    api = twitter.Api(consumer_key=config['apikey'],
                      consumer_secret=config['apisecret'],
                      access_token_key=config['accesstoken'],
                      access_token_secret=config['tokensecret'])

    statuses = api.GetUserTimeline(screen_name=config['user'])

    afinn = Afinn()
    for tweet in statuses:
        print(tweet.text)
        print("SCORE:", afinn.score(tweet.text))
        print("")


    return True, True, True


if __name__ == '__main__':
    print(light_on())
