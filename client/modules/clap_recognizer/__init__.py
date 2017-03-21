import logging
from .clap_detector import AudioListener

logger = logging.getLogger(__name__)
global audio_listener
audio_listener = None


def start(config):
    global audio_listener
    if audio_listener is None:
        audio_listener = AudioListener(**config['clap_detection'])
    audio_listener.start()


def stop(config):
    global audio_listener
    audio_listener.stop()


def light_on(config):
    global audio_listener
    return audio_listener.light_on()


if __name__ == "__main__":
    from time import sleep
    import yaml
    logging.basicConfig(level="INFO")
    with open('../../config.yml') as f:
        config = yaml.load(f)
    # listener = AudioListener()
    # listener.start()
    start(config)
    for i in range(10):
        print(light_on(config))
        sleep(1)
    # listener.stream_start()
    # listener.find_clap_deriv()
    stop(config)
    logger.debug("TEST COMPLETE")
