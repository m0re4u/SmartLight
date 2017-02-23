#! /usr/bin/python
import cv2
import os
import argparse


def main(person_name):
    camera_port = 0
    data_dir = 'raw_data/{}'.format(person_name)
    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    n = len(os.listdir(data_dir))
    # Now we can initialize the camera capture object with the cv2.VideoCapture
    # class. All it needs is the index to a camera port.
    camera = cv2.VideoCapture(camera_port)
    while True:
        ret, im = camera.read()
        cv2.imshow('image', im)
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            # Exit
            break
        elif key & 0xFF == ord('b'):
            # Take a picture
            dest = '{}/{}_{}.png'.format(data_dir, person_name, n)
            cv2.imwrite(dest, im)
            print("Saved image to {}".format(dest))
            n += 1

    # When everything done, release the capture
    camera.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        "Take images from your default webcam!"
    )
    parser.add_argument(
        "person_name",
        help="Name of the person who is in the image"
    )
    args = parser.parse_args()
    main(args.person_name)
