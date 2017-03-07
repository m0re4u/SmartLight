def light_on(config):
    return True, True, True


if __name__ == '__main__':
    import yaml
    with open('../config.yml') as f:
        config = yaml.load(f)
    print(light_on(config))
