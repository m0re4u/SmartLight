import yaml
import traceback
import logging
import socket
from coder import encode
from threading import Thread
from functools import wraps
from importlib import import_module
from time import sleep

logger = logging.getLogger(__name__)
logging.basicConfig(level='DEBUG')


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
        for name in self.config['modules']:
            self.register_module(name)

    def register_module(self, module_name):
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
        logger.debug("I was started!")

        def the_run(self):
            while True:
                self.lights_on()
                sleep(self.config['sleep_seconds'])

        try:
            logger.debug("I'm starting")
            a = self.start_modules()
            logger.debug("Returned: {}".format(a))

            logger.debug("I've started")

            # checking_thread = Thread(target=the_run, args=(self,), daemon=True)
            # checking_thread.start()
            # input("Hit <return> to stop the client.")
            # checking_thread.stop()
            # logger.info("Bye!")

            the_run(self)

        except KeyboardInterrupt:
            logger.info("Bye!")
        except:
            logger.error("THERE WAS AN ERROR")
            logger.error(traceback.format_exc())
        finally:
            self.stop_modules()

    def iter_func(attr):
        """
        Create a wrapper that executes the wrapped function for every element
        in getattr(self, attr).
        """
        logger.debug("I wrapped something with {}".format(attr))

        def wrapper(func):
            logger.debug("I wrapped {}".format(func))

            @wraps(func)
            def inner(self, *args, **kwargs):
                logger.debug("I'm doing something with {}".format(attr))
                for mod in getattr(self, attr):
                    func(self, mod, *args, **kwargs)
            return inner
        return wrapper

    @iter_func('modules')
    def lights_on(self, mod):
        self.send_lights(mod.__name__, mod.light_on(self.config))

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

    def send_lights(self, module_name, light_values):
        """
        Send the value of some lights
        """
        # get the signal
        module_config = self.config['modules'][module_name]
        pos = module_config['pos']
        size = module_config['size']
        # pos = map(int, module_config['pos'])
        # size = map(int, module_config['size'])
        signal = encode(*pos, *size, *light_values)

        # send the signal
        self.send_msg(signal)

    def send_msg(self, signal):
        # print(repr(self.config['testing']))
        if self.config['testing']:
            logger.debug("Sencding: {}".format(signal))
            return

        ip = self.config['server_ip']
        port = int(self.config['server_port'])

        # AF_INET >> IPv4
        # SOCK_STREAM >> TCP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ip, port))
        message = signal.to_bytes(4, byteorder='big')
        s.send(message)

        resp = s.recv(1000)
        s.close()
        # logger.info("Server response: {}".format(resp.decode()))


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

    client = Client(config)

    for mod in client.modules:
        logger.debug(mod)

    client.run()
