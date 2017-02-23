import yaml
import traceback
import logging
import socket
from coder import encode
from functools import wraps
from importlib import import_module
from time import sleep

logger = logging.getLogger(__name__)


def iter_func(attr):
    """
    Create a wrapper that executes the wrapped function for every element
    in getattr(self, attr).
    """
    def wrapper(func):
        @wraps(func)
        def inner(self, *args, **kwargs):
            for mod in getattr(self, attr):
                func(self, mod, *args, **kwargs)
        return inner
    return wrapper


class Client(object):
    def __init__(self, config):
        self.config = config
        self.clear_modules()
        for name in self.config['modules']:
            self.register_module(name)

    def clear_modules(self):
        """Clear all registered modules"""
        self.modules_with_start = []
        self.modules_with_stop = []
        self.modules = []

    def register_module(self, module_name):
        """
        Register a module.

        A module must define a `light_on` function.

        A module may define a `stop` function. This will be called when
        shutting down, after `light_on` is called for the last time.

        A module may define a `start` function only when it also defines a
        `stop` function. This will be called when initialising, before
        `light_on` is called for the first time.
        """
        run_name = self.config['run_name']
        start_name = self.config['start_name']
        stop_name = self.config['stop_name']
        try:
            module = import_module(module_name)
        except ImportError:
            logger.error(traceback.format_exc())
        else:
            # Check whether the module is usable
            if not hasattr(module, run_name):
                raise ImportError(
                    "{} must have a {} function".format(
                        module.__name__,
                        run_name
                    )
                )
            self.modules.append(module)

            # Check whether the module has a `stop` function
            if hasattr(module, stop_name):
                self.modules_with_stop.append(module)

            # Check whether the module has a `start` function
            # and verify it can be stopped.
            if hasattr(module, start_name):
                if not self.modules_with_stop[-1] == module:
                    raise ImportError(
                        "A module with a {} function must also have a {}"
                        " function ({})".format(
                            start_name,
                            stop_name,
                            module.__name__
                        )
                    )
                self.modules_with_start.append(module)

    def run(self):
        """
        Keep checking the value of the lights until KeyboardInterrupt
        """
        try:
            self.start_modules()
            while True:
                self.lights_on()
                sleep(self.config['sleep_seconds'])
        except KeyboardInterrupt:
            logger.info("Bye!")
        except:
            logger.error("THERE WAS AN ERROR")
            logger.error(traceback.format_exc())
        finally:
            # self.send_msg((0, 0), (32, 16), (0, 0, 0))
            # THIS IS A HOTFIX
            self.send_msg((0, 0), (31, 15), (0, 0, 0))
            self.stop_modules()

    @iter_func('modules_with_start')
    def start_modules(self, mod):
        """
        Run the `start` functions of the modules that have it
        """
        logger.debug("Starting: " + mod.__name__)
        getattr(mod, self.config['start'])()

    @iter_func('modules_with_stop')
    def stop_modules(self, mod):
        """
        Run the `stop` functions of the modules that have it
        """
        # Accept errors at stopping, because an erroneous module should not
        # stop other modules from stopping
        logger.debug("Stopping: " + mod.__name__)
        try:
            getattr(mod, self.config['stop'])()
            logger.debug("Stopped {}".format(mod.__name__))
        except:
            logger.error(traceback.format_exc())
            logger.warning("{} wasn't stopped!".format(mod.__name__))

    @iter_func('modules')
    def lights_on(self, mod):
        lights = mod.light_on(self.config)
        logger.info('{}: {}'.format(mod.__name__, lights))
        self.send_lights(mod.__name__, lights)

    def send_lights(self, module_name, light_values):
        """
        Send the value of some lights
        """
        # get the signal
        module_config = self.config['modules'][module_name]
        pos = module_config['pos']
        size = module_config['size']

        # send the signal
        self.send_msg(pos, size, light_values)

    def send_msg(self, pos, size, light_values):
        signal = encode(*pos, *size, *light_values)
        # print(repr(self.config['testing']))
        if self.config['testing']:
            logger.debug("Sending: {}".format(signal))
            return

        ip = self.config['server_ip']
        port = self.config['server_port']

        # AF_INET >> IPv4
        # SOCK_STREAM >> TCP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        message = signal.to_bytes(4, byteorder='big')
        s.send(message)

        # Receive a message (as part of TCP?) (and discard it)
        s.recv(1000)
        s.close()


if __name__ == '__main__':
    from argparse import ArgumentParser, FileType

    parser = ArgumentParser()
    parser.add_argument(
        '-c',
        '--config_file',
        type=FileType('r'),
        default='config.yml'
    )
    parser.add_argument(
        '-l',
        '--log_level',
        default='INFO'
    )

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    config = yaml.load(args.config_file)
    args.config_file.close()

    client = Client(config)
    client.run()
