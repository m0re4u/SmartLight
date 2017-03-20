import yaml
import twitter
from afinn import Afinn

def light_on(yml_path=".api_key"): #TODO: work something out for yml path
    with open(yml_path) as f:
        config = yaml.load(f)

    api = twitter.Api(consumer_key=config['apikey'],
                      consumer_secret=config['apisecret'],
                      access_token_key=config['accesstoken'],
                      access_token_secret=config['tokensecret'])

    statuses = api.GetUserTimeline(screen_name=config['user'])

    # Get sentiment from newest tweet
    afinn = Afinn()
    score = afinn.score(statuses[0].text)

    if score > 0:
        return False, True, False
    elif score < 0:
        return True, False, False
    else:
        return True, True, True


if __name__ == '__main__':
    print(light_on())
