#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class

import speech_recognition as sr
from threading import Thread, Event


class SpeechRecogniser(object):
    def __init__(self, config):

        self.on_command = [["turn","on"],["turn","on","light"]]
        self.off_command = [["turn","off"],["turn","off","light"]]
        self.lights = ["1","2","3","4"]
        self.pause_threshold = 0.6
        self.phrase_time_limit = 5
        self.n_lights = len(self.lights)
        self.lights_status = []

        # Threading infrastructure
        self.stop_recognising = Event()
        self.thread = Thread(
            name="Speechrec",
            target=self.recognize_continuously
        )

        for i in range(self.n_lights*3):
            self.lights_status.append(False)

    def recognize_command(self, candidates):

        on_command, light_on, conf_on = self.find_command(candidates, self.on_command)
        off_command, light_off, conf_off = self.find_command(candidates, self.off_command)

        if conf_on > 0:
            print("On %s with confidence %s" % (light_on, conf_on))
            print(on_command)
            self.lightswitch(1, int(light_on))
        elif conf_off > 0:
            print("Off %s with confidence %s" % (light_off, conf_off))
            print(off_command)
            self.lightswitch(0, int(light_off))
        else:
            print("No command found.")

    def lightswitch(self, on, n):
        if on:
            self.lights_status[n*3-3] = True
            self.lights_status[n*3-3+1] = True
            self.lights_status[n*3-3+2] = True
        else:
            self.lights_status[n*3-3] = False
            self.lights_status[n*3-3+1] = False
            self.lights_status[n*3-3+2] = False
        print(self.lights_status)

    def light_on(self, config):
        return tuple(self.lights_status)

    def find_command(self, candidates, commands):
        right_light = 0
        conf = 0
        correct_command = ""

        correct_candidates = []
        for candidate in candidates:
            candidate_text = candidate['transcript'].split()
            if 'confidence' in candidate:
                candidate_conf = candidate['confidence']
            else:
                candidate_conf = 0.5
            command_found = False
            for command in commands:
                is_command = []
                for word in command:
                    if word in candidate_text:
                        is_command.append(True)
                    else:
                        is_command.append(False)
                if False not in is_command:
                    correct_candidates.append(candidate)

        if correct_candidates:
            for candidate in correct_candidates:
                candidate_text = candidate['transcript'].split()
                for light in self.lights:
                    if light in candidate_text:
                        right_light = light
                        conf = candidate['confidence']
                        correct_command = candidate_text

        return (candidate_text, right_light, conf)

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
                print("Say something!")
                audio = r.listen(
                    source,
                    phrase_time_limit=self.phrase_time_limit
                )
                speech_to_text = r.recognize_google(audio, show_all=True)
                if speech_to_text:
                    candidates = speech_to_text['alternative']
                    self.recognize_command(candidates)
                    print(candidates)
                    # recognize speech using Google Speech Recognition
                try:
                    # for testing purposes, we're just using the default API
                    # key to use another API key, use
                    # `r.recognize_google(
                    #     audio,
                    #     key="GOOGLE_SPEECH_RECOGNITION_API_KEY"
                    # )`
                    # instead of `r.recognize_google(audio)`
                    print("Google Speech Recognition thinks you said ")
                except sr.UnknownValueError:
                    print(
                        "Google Speech Recognition could not understand audio"
                    )
                except sr.RequestError as e:
                    print(
                        "Could not request results from Google Speech"
                        " Recognition service; {0}".format(e)
                    )
        print("Stopped recognising.")


global speech_recognisor
speech_recognisor = None


def start(config):
    global speech_recognisor
    if speech_recognisor is None:
        speech_recognisor = SpeechRecogniser(config)
    speech_recognisor.start()


def stop(config):
    global speech_recognisor
    speech_recognisor.stop()


def light_on(config):
    global speech_recognisor
    return speech_recognisor.light_on(config)


if __name__ == "__main__":
    import yaml
    from time import sleep
    with open('../config.yml') as f:
        config = yaml.load(f)

    start(config)

    sleep(1)

    try:
        while True:
            print(light_on(config))
            sleep(1)
    except KeyboardInterrupt:
        print("bye!")
    finally:
        stop(config)
