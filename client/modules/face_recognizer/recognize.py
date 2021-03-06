#! /usr/bin/python
#
# Example to run classifier on webcam stream.
# Brandon Amos & Vijayenthiran
# 2016/06/21
#
# Copyright 2015-2016 Carnegie Mellon University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Contrib: Vijayenthiran
# This example file shows to run a classifier on webcam stream. You need to
# run the classifier.py to generate classifier with your own dataset.
# To run this file from the openface home dir:
# ./demo/classifier_webcam.py <path-to-your-classifier>

import argparse
import cv2
import os
import pickle

import numpy as np
from sklearn.mixture import GMM
from .loading_bar import print_progress
import openface
np.set_printoptions(precision=2)

home = os.path.expanduser('~')
openFaceDir = os.path.join(home, 'projects', 'openface')
modelDir = os.path.join(openFaceDir, 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')
LOGIN_CUTOFF = 50


def getRep(bgrImg):
    if bgrImg is None:
        raise Exception("Unable to load image/frame")

    rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)

    # Get the largest face bounding box
    # bb = align.getLargestFaceBoundingBox(rgbImg) #Bounding box

    # Get all bounding boxes
    bb = align.getAllFaceBoundingBoxes(rgbImg)

    if bb is None:
        # raise Exception("Unable to find a face: {}".format(imgPath))
        return None

    alignedFaces = []
    for box in bb:
        alignedFaces.append(
            align.align(
                args.imgDim,
                rgbImg,
                box,
                landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE))

    if alignedFaces is None:
        raise Exception("Unable to align the frame")

    reps = []
    for alignedFace in alignedFaces:
        reps.append(net.forward(alignedFace))

    # print reps
    return reps


def infer(img, model):
    with open(model, 'rb') as f:
        # le - label and clf - classifer
        (le, clf) = pickle.load(f, encoding='latin1')

    reps = getRep(img)
    persons = []
    confidences = []
    for rep in reps:
        try:
            rep = rep.reshape(1, -1)
        except e:
            print("No Face detected")
            return (None, None)
        predictions = clf.predict_proba(rep).ravel()
        # print predictions
        maxI = np.argmax(predictions)
        # max2 = np.argsort(predictions)[-3:][::-1][1]
        persons.append(le.inverse_transform(maxI))
        # print str(le.inverse_transform(max2)) + ": "+str( predictions [max2])
        # ^ prints the second prediction
        confidences.append(predictions[maxI])
        if isinstance(clf, GMM):
            dist = np.linalg.norm(rep - clf.means_[maxI])
            print("  + Distance from the mean: {}".format(dist))
            pass
    return (persons, confidences)


def recognize_person(cap_dev, w, h, model, thresh):
    # Capture device. Usually 0 will be webcam and 1 will be usb cam.
    video_capture = cv2.VideoCapture(cap_dev)
    video_capture.set(3, w)
    video_capture.set(4, h)

    confidenceList = []
    login_test = {}
    logged_in = ""
    while logged_in == "":
        ret, frame = video_capture.read()
        persons, confidences = infer(frame, model)
        # If there is more than one person in the image, do not try to log one
        # of them in.
        if len(persons) > 1:
            login_test = {}
        try:
            # append with two floating point precision
            confidenceList.append('%.2f' % confidences[0])
        except IndexError:
            # If there is no face detected, confidences matrix will be empty.
            # We can simply ignore it.
            login_test = {}
            pass

        for i, c in enumerate(confidences):
            if c <= thresh:
                # If we lose confidence in one person, reset the logon counter
                if persons[i] in login_test:
                    login_test[persons[i]] = 0
                    print_progress(0, LOGIN_CUTOFF+1, bar_length=35)
                persons[i] = "_unknown"
            else:
                # If we know the face, update the logon counter
                if persons[i] in login_test:
                    login_test[persons[i]] += 1
                else:
                    login_test[persons[i]] = 0

        # Print the person name and confidence value on the frame
        cv2.putText(
            frame, "P: {} C: {}".format(persons, confidences), (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
        )
        cv2.imshow('', frame)

        # print(login_test)
        for k, v in login_test.items():
            print_progress(v, LOGIN_CUTOFF+1, bar_length=35)
            if v > LOGIN_CUTOFF:
                print("{} logged in!".format(k.decode('ascii')))
                logged_in = k

        # quit the program on the press of key 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # When everything is done, release the capture
    video_capture.release()
    cv2.destroyAllWindows()
    return logged_in


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--dlibFacePredictor',
        type=str,
        help="Path to dlib's face predictor.",
        default=os.path.join(
            dlibModelDir,
            "shape_predictor_68_face_landmarks.dat"))
    parser.add_argument(
        '--networkModel',
        type=str,
        help="Path to Torch network model.",
        default=os.path.join(
            openfaceModelDir,
            'nn4.small2.v1.t7'))
    parser.add_argument('--imgDim', type=int,
                        help="Default image dimension.", default=96)
    parser.add_argument(
        '--captureDevice',
        type=int,
        default=0,
        help='Capture device. 0 for latop webcam and 1 for usb webcam')
    parser.add_argument('--width', type=int, default=320)
    parser.add_argument('--height', type=int, default=240)
    parser.add_argument('--threshold', type=float, default=0.5)
    parser.add_argument('--cuda', action='store_true')
    parser.add_argument('--verbose', action='store_true')
    parser.add_argument(
        'classifierModel',
        type=str,
        help='The Python pickle representing the classifier. This is NOT the '
        'Torch network model, which can be set with --networkModel.')

    args = parser.parse_args()

    align = openface.AlignDlib(args.dlibFacePredictor)
    net = openface.TorchNeuralNet(
        args.networkModel,
        imgDim=args.imgDim,
        cuda=args.cuda
    )
    person = recognize_person(args.captureDevice, args.width, args.height,
                              args.classifierModel, args.threshold)
    print("Recognized: {}".format(person))
