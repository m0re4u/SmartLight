import cv2
import numpy as np
import time


class GestureRecognizer:

    def __init__(self):
        # Starting with 100's to prevent error while masking
        self.h, self.s, self.v = 100, 100, 100
        self.threshold = 2
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.start_videocapture()

    def start_videocapture(self):
        self.fingers = 0
        self.light = False

        # Open Camera object
        self.cap = cv2.VideoCapture(0)

        # Decrease frame size
        self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 1000)
        self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 700)

    def light_on(self):
        return self.light

    def recognize_continuously(self):
        done = False
        while(self.cap.isOpened() and not done):
            finger_queue = []

            # Do 20 videocaptures before changing the light switch
            for i in range(20):
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
        ret, frame = self.cap.read()

        # Blur the image
        blur = cv2.blur(frame, (3, 3))

        # Convert to HSV color space
        hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)

        # Create a binary image with where white will be skin colors and rest
        # is black
        mask2 = cv2.inRange(
            hsv, np.array([2, 50, 50]), np.array([15, 255, 255]))

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
            for i in range(len(contours)):
                cnt = contours[i]
                area = cv2.contourArea(cnt)
                if(area > max_area):
                    max_area = area
                    ci = i

            # Largest area contour
            if not len(contours) == 0:
                cnts = contours[ci]

            # Find convex hull
            hull = cv2.convexHull(cnts)

            # Find convex defects
            hull2 = cv2.convexHull(cnts, returnPoints=False)
            defects = cv2.convexityDefects(cnts, hull2)


            FarDefect = []
            if not defects is None:
                # Get defect points and draw them in the original image
                for i in range(defects.shape[0]):
                    s, e, f, d = defects[i, 0]
                    start = tuple(cnts[s][0])
                    end = tuple(cnts[e][0])
                    far = tuple(cnts[f][0])
                    FarDefect.append(far)
                    cv2.line(frame, start, end, [0, 255, 0], 1)
                    cv2.circle(frame, far, 10, [100, 255, 255], 3)

            # Find moments of the largest contour
            moments = cv2.moments(cnts)

            # Central mass of first order moments
            if moments['m00'] != 0:
                cx = int(moments['m10']/moments['m00'])  # cx = M10/M00
                cy = int(moments['m01']/moments['m00'])  # cy = M01/M00
            centerMass = (cx, cy)

            # Draw center mass
            cv2.circle(frame, centerMass, 7, [100, 0, 255], 2)

            cv2.putText(frame, 'Center', tuple(centerMass),
                        self.font, 2, (255, 255, 255), 2)

            # Distance from each finger defect(finger webbing) to the center
            # mass
            distanceBetweenDefectsToCenter = []
            for i in range(0, len(FarDefect)):
                x = np.array(FarDefect[i])
                centerMass = np.array(centerMass)
                distance = np.sqrt(
                    np.power(x[0]-centerMass[0], 2) +
                    np.power(x[1]-centerMass[1], 2))
                distanceBetweenDefectsToCenter.append(distance)

            # Get an average of three shortest distances from finger webbing
            # to center mass
            sortedDefectsDistances = sorted(distanceBetweenDefectsToCenter)
            AverageDefectDistance = np.mean(sortedDefectsDistances[0:2])

            # Get fingertip points from contour hull
            # If points are in proximity of 80 pixels, consider as a single
            # point in the group
            finger = []
            for i in range(0, len(hull)-1):
                if (np.absolute(hull[i][0][0] - hull[i+1][0][0]) > 80) \
                or (np.absolute(hull[i][0][1] - hull[i+1][0][1]) > 80):
                    if hull[i][0][1] < 500:
                        finger.append(hull[i][0])

            # The fingertip points are 5 hull points with largest y coordinates
            finger = sorted(finger, key=lambda x: x[1])
            fingers = finger[0:5]

            # Calculate distance of each finger tip to the center mass
            fingerDistance = []
            for i in range(0, len(fingers)):
                distance = np.sqrt(
                    np.power(fingers[i][0]-centerMass[0], 2) +
                    np.power(fingers[i][1]-centerMass[0], 2))
                fingerDistance.append(distance)

            # Finger is pointed/raised if the distance of between fingertip to
            # the center mass is larger than the distance of average finger
            # webbing to center mass by 130 pixels
            result = 0
            for i in range(0, len(fingers)):
                if fingerDistance[i] > AverageDefectDistance + 130:
                    result = result + 1
                    cv2.putText(
                        frame, 'finger', tuple(finger[i]), self.font, 2,
                        (255, 255, 255), 2)

            self.fingers = result

            # Print bounding rectangle
            x, y, w, h = cv2.boundingRect(cnts)
            img = cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            with open('hull.txt','wb') as f:
                f.write(str(hull))

            cv2.drawContours(frame, [hull], -1, (255, 255, 255), 2)

            # Print number of pointed fingers
            cv2.putText(frame, str(self.fingers), (100, 100),
                        self.font, 2, (255, 255, 255), 2)
            cv2.imshow('Dilation', frame)

if __name__ == "__main__":
    recog = GestureRecognizer()
    recog.recognize_continuously()
