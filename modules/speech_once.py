#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class

import speech_recognition as sr
import editdistance

def recognize_command(candidates, on_command, off_command, lights, status):

    on_command, light_on, conf_on = find_command(candidates, on_command, lights)
    off_command, light_off, conf_off = find_command(candidates, off_command, lights)
    if conf_on > 0:
        print("On %s with confidence %s" % (light_on, conf_on))
        print(on_command)
        status = lightswitch(1, int(light_on), status)
    elif conf_off > 0:
        print("Off %s with confidence %s" % (light_off, conf_off))
        print(off_command)
        status = lightswitch(0, int(light_off), stats)
    else:
        print("No command found.")
    return status

def lightswitch(on, n, status):
    if on:
        status[n*3-3] = True
        status[n*3-3+1] = True
        status[n*3-3+2] = True
    else:
        status[n*3-3] = False
        status[n*3-3+1] = False
        status[n*3-3+2] = False
    return status

def find_command(candidates, commands, lights):
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
                for light in lights:
                    if light in candidate_text:
                        right_light = light
                        conf = candidate['confidence']
                        correct_command = candidate_text

        return (candidate_text, right_light, conf)

def light_on(config):

    on_command = [["turn","on"],["turn","on","light"]]
    off_command = [["turn","off"],["turn","off","light"]]
    lights = ["1","2","3","4"]

    status = []
    for i in range(4*3):
        status.append(False)

    # obtain audio from the microphone
    r = sr.Recognizer()
    r.pause_threshold = 0.6
    with sr.Microphone() as source:

        print("Say something!")
        audio = r.listen(source, phrase_time_limit=5)
        speech_to_text = r.recognize_google(audio, show_all=True)
        if speech_to_text:
            candidates = speech_to_text['alternative']
            status = recognize_command(candidates, on_command, off_command, lights, status)
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

    print(status)
    return tuple(status)

if __name__ == '__main__':
    light_on([])

