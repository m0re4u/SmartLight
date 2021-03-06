import cv2
import numpy as np
import time
import openface
import time
# import socket
import subprocess
import logging
logger = logging.getLogger(__name__)

class GestureRecognizer(object):

    def __init__(self, config):
        # Starting with 100's to prevent error while masking
        self.config = config
        self.threshold = 2.5
        self.high_threshold = 3.5
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.start_videocapture()
        self.align = openface.AlignDlib('/home/verna/openface/models/dlib/shape_predictor_68_face_landmarks.dat')
        self.net = openface.TorchNeuralNet('/home/verna/openface/models/openface/nn4.small2.v1.t7', 96)
        self.pos = config["modules"]["modules.gesture_recognizer"]["pos"]
        print(self.pos)
        self.size = config["modules"]["modules.gesture_recognizer"]["size"]

    def start_videocapture(self):
        self.fingers = 0
        self.light = False

        # Open Camera object
        self.cap = cv2.VideoCapture(0)

        # Decrease frame size
        self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 700)
        self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 500)

    def light_on(self, config):
        if self.light is True:
            return (True, True, True)
        else:
            return (False, False, False)

    def recognize_continuously(self):
        done = False
        while(self.cap.isOpened() and not done):
            # time.sleep(0.5)
            finger_queue = []

            # Do 20 videocaptures before changing the light switch
            for i in range(10):
                self.recognize_once()
                finger_queue.append(self.fingers)
                # Close the output video by pressing 'ESC'
                k = cv2.waitKey(5) & 0xFF
                if k == 27:
                    done = True
                    break

            # Change light if average number of fingers is higher than
            # threshold
            if finger_queue and np.mean(finger_queue) > self.threshold:
            #     self.light = not self.light

            # if self.light:
                self.send_msg(self.pos, self.size, (True, False, False))
            else:
                self.send_msg(self.pos, self.size, (False, False, False))

        self.cap.release()
        cv2.destroyAllWindows()

    def send_msg(self, pos, size, light_values, timeout=10):
        args = list(pos) + list(size) + list(light_values)
        print(args)
        signal = self.encode(*args)
        # message = bytes(signal)
        # print(repr(self.config['testing']))
        if self.config['testing']:
            logger.debug("Sending: {:0>32b}".format(signal))
            return

        ip = self.config['server_ip']
        port = self.config['server_port']

        # AF_INET: IPv4
        # SOCK_STREAM: TCP
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.settimeout(timeout)
        # s.connect((ip, port))
        # # message = signal.to_bytes(4, byteorder='big')
        # s.send(message)

        # # Receive a message (as part of TCP?) (and discard it)
        # s.recv(1000)
        # s.close()
        subprocess.call(['python3', 'send.py', str(signal)])

    @staticmethod
    def encode_color(color, n_bits):
        """
        If color is given as boolean, interpret it as maximally on or totally off.
        Otherwise check whether it fits within the number of bits.
        """
        if isinstance(color, bool):
            return (2 ** n_bits - 1) * color
        elif 0 <= color < 2 ** n_bits:
            return color
        else:
            raise ValueError(
                "`color` should be a boolean or be between 0 and 2 ** n_bits - 1"
            )

    def encode(self, xpos, ypos, width, height, red=True, green=True, blue=True,
           color_bits=4):
        """
        Given the position and color of the leds, encodes this information in an
        int of 3 bytes, which can be decoded using decode

        0 <= xpos <= 31: 5 bits
        0 <= ypos <= 15: 4 bits
        """

        # input validation first
        if not 0 <= xpos <= 31:
            print(xpos)
            raise ValueError('The x-position has to be between 0 and 31 inclusive'
                             'to fit the size of the board')
        elif not 0 <= ypos <= 15:
            raise ValueError('The y-position has to be between 0 and 15 inclusive'
                             'to fit the size of the board')
        elif width < 1:
            raise ValueError('The width value has to be higher than 0')
        elif height < 1:
            raise ValueError('The height value has to be higher than 0')
        elif width + xpos > 32:
            raise ValueError('The width and the x-position combined should not'
                             'go over the edge of the board')
        elif height + ypos > 16:
            raise ValueError('The height and the y-position combined should not'
                             'go over the edge of the board')


        width -= 1
        height -= 1
        signal = 0
        signal += xpos
        signal <<= 4    # size of ypos
        signal += ypos
        signal <<= 5    # size of width
        signal += width
        signal <<= 4    # size of height
        signal += height

        signal <<= color_bits    # size of colour bits
        signal += self.encode_color(red, color_bits)
        signal <<= color_bits    # size of colour bits
        signal += self.encode_color(green, color_bits)
        signal <<= color_bits    # size of colour bits
        signal += self.encode_color(blue, color_bits)

        return signal

    def recognize(self):
        self.recognize_once()
        self.cap.release()
        cv2.destroyAllWindows()

    def recognize_once(self):
        # Capture frames from the camera
        self.fingers = 0
        ret, frame = self.cap.read()

        # cv2.imwrite('img.png',frame)

        # Blur the image
        blur = cv2.blur(frame, (3, 3))

        # Convert to HSV color space
        hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
        mask2 = cv2.inRange(hsv, np.array([0, 50, 50]),
                np.array([15, 255, 255]))



        # Cr > 150 && Cr < 200 && Cb > 100 && Cb < 150.

        # Create a binary image with where white will be skin colors and rest
        # is black


        # Kernel matrices for morphological transformation
        kernel_square = np.ones((11, 11), np.uint8)
        kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # Perform morphological transformations to filter out the background
        # noise
        # Dilation increase skin color area
        # Erosion increase skin color area
        dilation = cv2.dilate(mask2, kernel_ellipse, iterations=1)
        erosion = cv2.erode(dilation, kernel_square, iterations=1)
        dilation2 = cv2.dilate(erosion, kernel_ellipse, iterations=1)
        filtered = cv2.medianBlur(dilation2, 5)
        kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (8, 8))
        dilation2 = cv2.dilate(filtered, kernel_ellipse, iterations=1)
        kernel_ellipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        dilation3 = cv2.dilate(filtered, kernel_ellipse, iterations=1)
        median = cv2.medianBlur(dilation2, 5)
        ret, thresh = cv2.threshold(median, 127, 255, 0)

        # Find contours of the filtered frame
        contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        poly = []

        if len(contours) > 0:
            # Find Max contour area (Assume that hand is in the frame)
            max_area = 100
            ci = 0
            cnts = []

            for i in range(len(contours)):
                cnt = contours[i]
                area = cv2.contourArea(cnt)

                # Find largest hand candidate that does not contain a face
                if(area > max_area and not self.check_for_face(cnt, frame)):
                    max_area = area
                    cnts = cnt

            #cnts = self.find_hand_contours(contours,frame)

            if len(cnts) > 0:

                X = [coordinates[0] for item in cnts for coordinates in item]
                Y = [coordinates[1] for item in cnts for coordinates in item]
                minY = min(Y)
                maxY = max(Y)
                minX = min(X)
                maxX = max(X)
                # hand = median[minY:maxY,minX:maxX]
                # cv2.imwrite('boe.png',hand)
                # apply_thinning(hand)

                # Contour approximation with Douglas-Peucker algorithm
                poly = cv2.approxPolyDP(cnts, 0.1, True)

                # Find convex hull and defects
                hull = cv2.convexHull(cnts)
                hull2 = cv2.convexHull(cnts, returnPoints=False)
                defects = cv2.convexityDefects(cnts, hull2)


                fingers = 0
                FarDefect = []
                if not defects is None:
                    # Get defect points and draw them in the original image
                    for i in range(defects.shape[0]):
                        s, e, f, d = defects[i, 0]
                        start = tuple(cnts[s][0])
                        end = tuple(cnts[e][0])

                        x, y = end
                        far = tuple(cnts[f][0])
                        dist = d
                        FarDefect.append(far)
                        hordist = maxX - minX
                        if dist > 30 * hordist and y < (1.5 * hordist):
                            fingers += 1
                            cv2.line(frame, start, end, [0, 255, 0], 1)
                            cv2.circle(frame, far, 10, [100, 255, 255], 3)

                if fingers > 5:
                    fingers = 5
                self.fingers = fingers

                # Print bounding rectangle
                x, y, w, h = cv2.boundingRect(cnts)
                img = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            else:
                self.fingers = 0


            # # Find moments of the largest contour
            # moments = cv2.moments(cnts)

            # Central mass of first order moments
            # if moments['m00'] != 0:
            #     cx = int(moments['m10']/moments['m00'])  # cx = M10/M00
            #     cy = int(moments['m01']/moments['m00'])  # cy = M01/M00
            # centerMass = (cx, cy)

            # # Draw center mass
            # cv2.circle(frame, centerMass, 7, [100, 0, 255], 2)

            # cv2.putText(frame, 'Center', tuple(centerMass),
            #             self.font, 2, (255, 255, 255), 2)

            # Distance from each finger defect(finger webbing) to the center
            # mass
            # distanceBetweenDefectsToCenter = []
            # for i in range(0, len(FarDefect)):
            #     x = np.array(FarDefect[i])
            #     centerMass = np.array(centerMass)
            #     distance = np.sqrt(
            #         np.power(x[0]-centerMass[0], 2) +
            #         np.power(x[1]-centerMass[1], 2))
            #     distanceBetweenDefectsToCenter.append(distance)

            # # Get an average of three shortest distances from finger webbing
            # # to center mass
            # sortedDefectsDistances = sorted(distanceBetweenDefectsToCenter)
            # AverageDefectDistance = np.mean(sortedDefectsDistances[0:2])

            # # Get fingertip points from contour hull
            # # If points are in proximity of 80 pixels, consider as a single
            # # point in the group
            # finger = []
            # proximity = 1.6 * AverageDefectDistance
            # for i in range(0, len(hull)-1):
            #     if (np.absolute(hull[i][0][0] - hull[i+1][0][0]) > proximity) \
            #     or (np.absolute(hull[i][0][1] - hull[i+1][0][1]) > proximity):
            #         if hull[i][0][1] < 500:
            #             finger.append(hull[i][0])

            # # The fingertip points are 5 hull points with largest y coordinates
            # finger = sorted(finger, key=lambda x: x[1])
            # fingers = finger[0:5]

            # Calculate distance of each finger tip to the center mass
            # fingerDistance = []
            # for i in range(0, len(fingers)):
            #     distance = np.sqrt(
            #         np.power(fingers[i][0]-centerMass[0], 2) +
            #         np.power(fingers[i][1]-centerMass[0], 2))
            #     fingerDistance.append(distance)

            # # Finger is pointed/raised if the distance of between fingertip to
            # # the center mass is larger than the distance of average finger
            # # webbing to center mass by 130 pixels
            # result = 0
            # for i in range(0, len(fingers)):
            #     if fingerDistance[i] > AverageDefectDistance + 130:
            #         result = result + 1
            #         cv2.putText(
            #             frame, 'finger', tuple(finger[i]), self.font, 2,
            #             (255, 255, 255), 2)

            # self.fingers = result


            if len(poly) > 0:
                cv2.drawContours(frame, [poly], -1, (255, 255, 255), 2)

            # Print number of pointed fingers
            cv2.putText(frame, str(self.fingers)+" fingers", (100, 100),
                        self.font, 2, (255, 255, 255), 2)
            cv2.imshow('Dilation', frame)

    def check_for_face(self, contours, frame):
        faces = []
        bb = False

        # Extract the x and y coordinates from the contours of possible hand
        X = [coordinates[0] for item in contours for coordinates in item]
        Y = [coordinates[1] for item in contours for coordinates in item]
        img = frame[min(Y):max(Y),min(X):max(X)]
        cv2.imwrite('face.png',img)

        # Look for faces in nonempty image
        if not len(img) == 0:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            bb = self.align.getLargestFaceBoundingBox(rgbImg)
            # cv2.imwrite('face.png',img)

        return (not bb is None)

    # def find_hand_contours(self, contours, frame):
    #     largest = []
    #     largest_index = 0
    #     max_area = 100
    #     for i, current in enumerate(contours):
    #         area = cv2.contourArea(current)

    #         # Find largest hand candidate that does not contain a face
    #         if(area > max_area):
    #             max_area = area
    #             largest = current
    #             largest_index = i

    #     isface = self.check_for_face(largest,frame)
    #     if isface:
    #         del contours[largest_index]
    #         return self.find_hand_contours(contours,frame)
    #     else:
    #         return largest

if __name__ == "__main__":
    import yaml
    with open('../config.yml') as f:
        config = yaml.load(f)
    recog = GestureRecognizer(config)
    recog.recognize_continuously()
