from os import system as command
from platform import system as os_name


def light_on(config):

    # this line largely taken from
    # http://stackoverflow.com/questions/2953462/pinging-servers-in-python
    parameters = '-n 1 ' if os_name().lower() == 'windows' else '-c 1 '

    null_outstream = ' > NUL' if os_name().lower() == 'windows'\
        else ' > /dev/null'

    result = command(
        'ping ' + parameters + config['ping_address'] + null_outstream)
    return (not result,)*3


if __name__ == '__main__':
    import yaml
    with open('../config.yml') as f:
        config = yaml.load(f)
    print(light_on(config))
