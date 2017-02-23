import os
import yaml
import traceback
import logging
from importlib import import_module

logger = logging.getLogger(__name__)
# MODULES_DIRECTORY

# Find, import and register modules.
# blueprints = (os.listdir(MODULES_DIRECTORY) if bp != 'admin')
# for bp_name in blueprints:
#     try:
#         bp = import_module('freevle.blueprints.' + bp_name)
#         app.register_blueprint(bp.bp, url_prefix=bp.URL_PREFIX)
#     except ImportError:
#         raise ImportError("{} blueprint appears to be broken.".format(bp_name))
#     except AttributeError:
#         raise ImportError("{} blueprint doesn't have a blueprint.".format(bp_name))


class Client(object):
    def __init__(self, config):
        self.config = config
        self.clear_modules()
        self.register_modules()

    def clear_modules(self):
        self.modules = []

    @staticmethod
    def list_modules(directory):
        for fileordir in os.listdir(directory):
            if os.path.isdir(fileordir):
                yield fileordir
            elif fileordir[-3:] == '.py':
                yield fileordir[:-3]

    def register_modules(self):
        modules_dir = self.config['modules_directory']
        base_name = modules_dir.replace('/', '.').strip('.')
        logger.debug('Base module: ' + base_name)
        import_module(base_name, __name__)
        for name in self.list_modules(modules_dir):
            self.register_module(name, base_name)

    def register_module(self, module_name, base_name):
        try:
            module = import_module('.' + module_name, base_name)
        except ImportError:
            logger.error(traceback.format_exc())
        else:
            self.modules.append(module)

    def run(self):
        ...


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
