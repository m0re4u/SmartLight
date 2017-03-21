import os
import yaml
import traceback
import logging
import socket
from coder import encode
from functools import wraps
from importlib import import_module
from time import sleep

RUN_NAME = 'light_on'
START_NAME = 'start'
STOP_NAME = 'stop'
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
        try:
            module = import_module(module_name)
        except ImportError:
            logger.error(traceback.format_exc())
        else:
            # Check whether the module is usable
            if not hasattr(module, RUN_NAME):
                raise ImportError(
                    "{} must have a {} function".format(
                        module.__name__,
                        RUN_NAME
                    )
                )
            self.modules.append(module)

            # Check whether the module has a `stop` function
            if hasattr(module, STOP_NAME):
                self.modules_with_stop.append(module)

            # Check whether the module has a `start` function
            # and verify it can be stopped.
            if hasattr(module, START_NAME):
                if not self.modules_with_stop[-1] == module:
                    raise ImportError(
                        "A module with a {} function must also have a {}"
                        " function ({})".format(
                            START_NAME,
                            STOP_NAME,
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
            self.stop_modules()
            # self.send_msg((0, 0), (32, 16), (0, 0, 0))
            # THIS IS A HOTFIX, (32, 16) results in some weird bug with the
            # edge of the board
            self.send_msg((0, 0), (31, 15), (0, 0, 0))

    @iter_func('modules_with_start')
    def start_modules(self, mod):
        """
        Run the `start` functions of the modules that have it
        """
        logger.debug("Starting: " + mod.__name__)
        getattr(mod, START_NAME)(self.config)

    @iter_func('modules_with_stop')
    def stop_modules(self, mod):
        """
        Run the `stop` functions of the modules that have it
        """
        # Accept errors at stopping, because an erroneous module should not
        # stop other modules from stopping
        logger.info("Stopping: " + mod.__name__)
        try:
            getattr(mod, STOP_NAME)(self.config)
            logger.info("Stopped {}".format(mod.__name__))
        except:
            logger.error(traceback.format_exc())
            logger.warning("{} wasn't stopped!".format(mod.__name__))

    @iter_func('modules')
    def lights_on(self, mod):
        lights = mod.light_on(self.config)
        logger.debug('{}: {}'.format(mod.__name__, lights))
        self.send_lights(mod.__name__, lights)

    def send_lights(self, module_name, light_values):
        """
        Send the value of some lights
        """
        # get the signal
        module_config = self.config['modules'][module_name]
        if len(light_values) == 3:
            pos = module_config['pos']
            size = module_config['size']
            self.send_msg(pos, size, light_values)
        # send the signal
        elif len(light_values) % 3 == 0:
            for i in range(0, len(light_values), 3):
                pos = module_config[i // 3]['pos']
                size = module_config[i // 3]['size']
                self.send_msg(pos, size, light_values[i*3:(i+1)*3])
        else:
            logger.error(
                "The tuple returned by {} does not have a length of a multiple"
                " of 3".format(module_name)
                )

    def send_msg(self, pos, size, light_values, timeout=3):
        signal = encode(*pos, *size, *light_values)
        # print(repr(self.config['testing']))
        if self.config['testing']:
            logger.debug("Sending: {}".format(signal))
            return

        ip = self.config['server_ip']
        port = self.config['server_port']

        # AF_INET: IPv4
        # SOCK_STREAM: TCP
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
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
        help="Provide a configuration file that will be used to load in "
        "settings for the lights. If omitted, it will use face detection"
    )
    parser.add_argument(
        '-l',
        '--log_level',
        default='INFO'
    )

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    if args.config_file is None:
        # Use OpenFace to choose a configuration file
        from modules.face_recognizer import FaceDetector as fr

        argument_dict = {
            'captureDevice': 0, 'height': 240, 'cuda': False, 'width': 320,
            'threshold': 0.5, 'imgDim': 96,
            'classifierModel': 'features/classifier.pkl',
            'networkModel': '/home/m0re/projects/openface/models/openface/nn4.small2.v1.t7',
            'verbose': False, 'dlibFacePredictor': '/home/m0re/projects/openface/models/dlib/shape_predictor_68_face_landmarks.dat'}
        detec = fr.FaceDetector(argument_dict)
        person = detec.recognize_person(
            0, 320, 240, 'modules/face_recognizer/features/classifier.pkl',
            0.7)
        config_name = "{}.yml".format(person)
        if person != "" and os.path.exists(config_name):
            logger.info("{} logged in!".format(person))
            with open(config_name) as f:
                config = yaml.load(f)
        else:
            logger.info("Failed to log in, falling back on default config:"
                        " \'config.yml\'")
            with open("config.yml") as f:
                config = yaml.load(f)
    else:
        config = yaml.load(args.config_file)
        args.config_file.close()

    client = Client(config)
    client.run()
