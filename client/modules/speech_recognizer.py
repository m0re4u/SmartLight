#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class
import logging

import speech_recognition as sr
from threading import Thread, Event

logger = logging.getLogger(__name__)


class SpeechRecogniser(object):
    def __init__(self, config):
        # Read in config
        self.n_lights = config['speech']['nlights']
        self.commands = config['speech']['commands']

        # Split the text of the commands
        for description in self.commands:
            description['text'] = [
                frozenset(string.lower().split()) for string in description['text']
            ]

        self.pause_threshold = config['speech']['pause_threshold']
        self.phrase_time_limit = config['speech']['phrase_time_limit']
        self.lights_status = [False for _ in range(self.n_lights*3)]

        # Threading infrastructure
        self.stop_recognising = Event()
        self.thread = Thread(
            name="Speech Recognising Thread",
            target=self.recognize_continuously
        )

    def recognize_command(self, candidates):
        """
        Find the command with the highest confidence in the candidates
        """
        for can in candidates:
            can['transcript'] = set(can['transcript'].lower().split())

        commands = [
            (description['values'],) + self.find_command(
                    candidates,
                    description['text']
            )
            for description in self.commands
        ]
        commands = [c for c in commands if c[2] > 0]
        if commands:
            values, lights, confidence = max(commands, key=lambda c: c[2])
            self.lightswitch(values, lights)
            logger.debug("Executed command: {}, {}, {}".format(
                values, lights, confidence
            ))
        else:
            logger.debug("No command found.")

    def lightswitch(self, values, lights):
        for n in lights:
            self.lights_status[n*3:(n+1)*3] = values
        logger.debug(self.lights_status)

    def light_on(self, config):
        if not self.thread.is_alive():
            raise Exception("The listening thread died!")
        return tuple(self.lights_status)

    def find_command(self, candidates, texts):
        """
        Discover whether the command represented by a set of strings is
        present in the candidate transcriptions.
        Return the confidence and the lights present in the most confident
        candidate.
        """
        # Find correct candidates
        correct_candidates = [
            can for can in candidates
            if any(com <= can['transcript'] for com in texts)
        ]

        # Find the candidate with the highest confidence and
        # find all the lights mentioned in the command
        lights = [
            (
                [light for light in range(self.n_lights)
                 if str(light + 1) in can['transcript']],
                can['confidence']
            )
            for can in correct_candidates
        ]
        lights = [l for l in lights if l[0]]
        return max(lights, key=lambda c: c[1]) \
            if lights else (None, float('-Inf'))

    def start(self):
        """Start listening and recognising"""
        self.stop_recognising.clear()
        self.thread.start()

    def stop(self):
        """
        Stop listening and recognising. Wait for all threads to terminate.
        """
        self.stop_recognising.set()
        self.thread.join()

    def recognize_continuously(self):
        # obtain audio from the microphone
        r = sr.Recognizer()
        r.pause_threshold = self.pause_threshold

        with sr.Microphone() as source:
            while not self.stop_recognising.is_set():
                # print("Say something!")
                audio = r.listen(
                    source,
                    phrase_time_limit=self.phrase_time_limit
                )
                    # recognize speech using Google Speech Recognition
                try:
                    speech_to_text = r.recognize_google(audio, show_all=True)
                    # for testing purposes, we're just using the default API
                    # key to use another API key, use
                    # `r.recognize_google(
                    #     audio,
                    #     key="GOOGLE_SPEECH_RECOGNITION_API_KEY"
                    # )`
                    # instead of `r.recognize_google(audio)`
                    # print("Google Speech Recognition thinks you said ")
                except sr.UnknownValueError:
                    logger.error(
                        "Google Speech Recognition could not understand audio"
                    )
                except sr.RequestError as e:
                    logger.error(
                        "Could not request results from Google Speech"
                        " Recognition service; {0}".format(e)
                    )
                else:
                    if speech_to_text:
                        candidates = speech_to_text['alternative']
                        self.recognize_command(candidates)
                        logger.debug("Candidates: ")
                        for can in candidates:
                            logger.debug(can)
        # print("Stopped recognising.")


global speech_recogniser
speech_recogniser = None


def start(config):
    global speech_recogniser
    if speech_recogniser is None:
        speech_recogniser = SpeechRecogniser(config)
    speech_recogniser.start()


def stop(config):
    global speech_recogniser
    speech_recogniser.stop()


def light_on(config):
    global speech_recogniser
    return speech_recogniser.light_on(config)
    # return (False,) * 12


if __name__ == "__main__":
    import yaml
    # from time import sleep
    logging.basicConfig(level='DEBUG')

    with open('../config.yml') as f:
        config = yaml.load(f)

    speech_recogniser = SpeechRecogniser(config)
    speech_recogniser.recognize_continuously()
    # start(config)

    # sleep(1)

    # try:
    #     while True:
    #         print(light_on(config))
    #         sleep(1)
    # except KeyboardInterrupt:
    #     print("bye!")
    # finally:
    #     stop(config)
