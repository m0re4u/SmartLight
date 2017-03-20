import logging
from modules.face_recognizer import FaceDetector as fr

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    from argparse import ArgumentParser, FileType

    parser = ArgumentParser()
    parser.add_argument(
        '-l',
        '--log_level',
        default='INFO'
    )

    args = parser.parse_args()
    logging.basicConfig(level=args.log_level)
    argument_dict = {
        'captureDevice': 0, 'height': 240, 'cuda': False, 'width': 320,
        'threshold': 0.5, 'imgDim': 96,
        'classifierModel': 'features/classifier.pkl',
        'networkModel': '/home/m0re/projects/openface/models/openface/nn4.small2.v1.t7',
        'verbose': False, 'dlibFacePredictor': '/home/m0re/projects/openface/models/dlib/shape_predictor_68_face_landmarks.dat'}
    detec = fr.FaceDetector(argument_dict)

    results = []
    while True:
        person = detec.recognize_person(
            0, 320, 240, 'modules/face_recognizer/features/classifier.pkl',
            0.7)
        print("Detected: {}".format(person))
        cmd = input("Is this correct? (y/n/q)")
        if cmd == 'q':
            print(results)
            break
        elif cmd == 'y':
            results.append(1)
        elif cmd == 'n':
            results.append(0)
        else:
            print("Eh?")
