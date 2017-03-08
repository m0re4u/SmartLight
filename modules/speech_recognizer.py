#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class

import speech_recognition as sr
import editdistance

class SpeechRecogniser:

    def __init__(self, config):

        self.on_command = [["turn","on"],["turn","on","light"]]
        self.off_command = [["turn","off"],["turn","off","light"]]
        self.lights = ["1","2","3","4"]
        self.pause_threshold = 0.6
        self.phrase_time_limit = 5
        self.n_lights = len(self.lights)
        self.lights_status = []

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
                if not False in is_command:
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

    def recognize_continuously(self):
        # obtain audio from the microphone
        r = sr.Recognizer()
        r.pause_threshold = self.pause_threshold

        with sr.Microphone() as source:
            while(True):
                print("Say something!")
                audio = r.listen(source, phrase_time_limit=self.phrase_time_limit)
                speech_to_text = r.recognize_google(audio, show_all=True)
                if speech_to_text:
                    candidates = speech_to_text['alternative']
                    self.recognize_command(candidates)
                    print(candidates)
                    # recognize speech using Google Speech Recognition
                try:
                    # for testing purposes, we're just using the default API key
                    # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
                    # instead of `r.recognize_google(audio)`
                    print("Google Speech Recognition thinks you said ")
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    print("Could not request results from Google Speech Recognition service; {0}".format(e))



if __name__ == "__main__":
    recog = SpeechRecogniser([])
    recog.recognize_continuously()
