import os
import cv2
import pickle
import openface
import argparse
import numpy as np
from sklearn.mixture import GMM
from .loading_bar import print_progress

# This is here for testing purposes. openFaceDir has to be set to our
# OpenFace repository
home = os.path.expanduser('~')
openFaceDir = os.path.join(home, 'projects', 'openface')
modelDir = os.path.join(openFaceDir, 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')
LOGIN_CUTOFF = 20


class FaceDetector():
    """
    FaceDetector will log in a user based on a recognised person.
    Uses OpenFace as underlying software
    """
    def __init__(self, args):
        self.align = openface.AlignDlib(args['dlibFacePredictor'])
        self.net = openface.TorchNeuralNet(
            args['networkModel'],
            imgDim=args['imgDim'],
            cuda=args['cuda']
        )
        self.args = args

    def getRep(self, bgrImg):
        if bgrImg is None:
            raise Exception("Unable to load image/frame")
        rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)
        # Get all bounding boxes
        bb = self.align.getAllFaceBoundingBoxes(rgbImg)

        if bb is None:
            return None

        alignedFaces = []
        for box in bb:
            alignedFaces.append(
                self.align.align(
                    self.args['imgDim'], rgbImg, box,
                    landmarkIndices=openface.AlignDlib.OUTER_EYES_AND_NOSE))

        if alignedFaces is None:
            raise Exception("Unable to align the frame")

        reps = []
        for alignedFace in alignedFaces:
            reps.append(self.net.forward(alignedFace))
        return reps

    def infer(self, img, model):
        with open(model, 'rb') as f:
            # le - label and clf - classifer
            (le, clf) = pickle.load(f, encoding='latin1')

        reps = self.getRep(img)
        persons = []
        confidences = []
        for rep in reps:
            try:
                rep = rep.reshape(1, -1)
            except e:
                print("No Face detected")
                return (None, None)
            predictions = clf.predict_proba(rep).ravel()
            maxI = np.argmax(predictions)
            persons.append(le.inverse_transform(maxI))
            confidences.append(predictions[maxI])
            if isinstance(clf, GMM):
                dist = np.linalg.norm(rep - clf.means_[maxI])
                print("  + Distance from the mean: {}".format(dist))
                pass
        return (persons, confidences)

    def recognize_person(self, cap_dev, w, h, model, thresh):
        # Capture device. Usually 0 will be webcam and 1 will be usb cam.
        video_capture = cv2.VideoCapture(cap_dev)
        video_capture.set(3, w)
        video_capture.set(4, h)

        confidenceList = []
        login_test = {}
        logged_in = b""
        while logged_in == b"":
            ret, frame = video_capture.read()
            persons, confidences = self.infer(frame, model)
            # If there is more than one person in the image, do not try to
            # log one of them in.
            if len(persons) > 1:
                login_test = {}
            try:
                # append with two floating point precision
                confidenceList.append('%.2f' % confidences[0])
            except IndexError:
                # If there is no face detected, confidences matrix will be
                # empty. We can simply ignore it.
                login_test = {}
                pass

            for i, c in enumerate(confidences):
                if c <= thresh:
                    # If we lose confidence in one person, reset the logon
                    # counter
                    if persons[i] in login_test:
                        login_test[persons[i]] = 0
                        print_progress(0, LOGIN_CUTOFF+1, bar_length=35)
                    persons[i] = b"_unknown"
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
                    logged_in = k

            # quit the program on the press of key 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        # When everything is done, release the capture and destroy all the
        # windows. This is a workaround, as a single destroyAllWindows() call
        # doesn't actually close the window
        cv2.destroyAllWindows()
        cv2.imshow('', np.array(0))
        cv2.destroyAllWindows()
        video_capture.release()
        return logged_in.decode('ascii')


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
    argdict = vars(args)
    print(argdict)
    detec = FaceDetector(argdict)
    person = detec.recognize_person(args.captureDevice, args.width,
                                    args.height, args.classifierModel,
                                    args.threshold)
    print("Recognized: {}".format(person))
