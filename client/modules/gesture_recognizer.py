import cv2
import numpy as np
import time
import openface
import time
from thinning import apply_thinning

class GestureRecognizer:

    def __init__(self):
        # Starting with 100's to prevent error while masking
        self.threshold = 2.5
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.start_videocapture()
        self.align = openface.AlignDlib('face_recognizer/shape_predictor_68_face_landmarks.dat')
        self.net = openface.TorchNeuralNet('face_recognizer/nn4.small2.v1.t7', 96)

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
            for i in range(5):
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
                self.light = True
                print(self.light)
            else:
                self.light = False

        self.cap.release()
        cv2.destroyAllWindows()

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
                        if dist > 8000 and y < (1.5 * (maxX - minX)):
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
    recog = GestureRecognizer()
    recog.recognize_continuously()
