import yaml
import traceback
import logging
from coder import encode
from importlib import import_module

logger = logging.getLogger(__name__)


class Client(object):
    def __init__(self, config):
        self.config = config
        self.clear_modules()
        self.register_modules()

    def clear_modules(self):
        self.modules_with_start = []
        self.modules_with_stop = []
        self.modules = []

    def register_modules(self):
        for dic in self.config['modules']:
            self.register_module(dic['name'])

    def register_module(self, module_name):
        run_name = self.config['run_name']
        start_name = self.config['start_name']
        stop_name = self.config['stop_name']
        try:
            module = import_module(module_name)
            if not hasattr(module, run_name):
                raise ImportError(
                    "{} must have a {} function".format(
                        module.__name__,
                        run_name
                    )
                )
            self.modules.append(module)
            if hasattr(module, stop_name):
                self.modules_with_stop.append(module)
            if hasattr(module, start_name):
                if not self.modules_with_stop[-1] == module:
                    raise ImportError(
                        "A module with a {} function must also have a {}"
                        " function".format(start_name, stop_name)
                    )
                self.modules_with_start.append(module)
        except ImportError:
            logger.error(traceback.format_exc())
        # else:

    def run(self):
        ...

    def start_modules(self):
        """
        Run the `start` functions of the modules that have it
        """

    def stop_modules(self):
        """
        Run the `stop` functions of the modules that have it
        """

    def send_lights(self, light_values, module_name):
        """
        Send the value of some lights
        """
        # get the signal
        module_config = self.config['modules'][module_name]
        pos = module_config['pos']
        size = [module_config]['size']
        signal = encode(*pos, *size, *light_values)

        # send the signal
        send_msg(self, signal)

    def send_msg(self, signal):
        ip = self.config['server_ip']
        port = self.config['server_port']

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        message = signal.to_bytes(4, byteorder='big')
        s.send(message)

        resp = s.recv(1000)
        logger.info(resp)

if __name__ == '__main__':
    from argparse import ArgumentParser, FileType

    parser = ArgumentParser()
    parser.add_argument(
        '-c',
        '--config_file',
        type=FileType('r'),
        default='config.yml'
    )

    args = parser.parse_args()
    config = yaml.load(args.config_file)
    args.config_file.close()

    logging.basicConfig(level='DEBUG')
    client = Client(config)

    for mod in client.modules:
        logger.debug(mod)
