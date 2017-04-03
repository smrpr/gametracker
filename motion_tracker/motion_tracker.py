import datetime
import imutils
import time
import cv2
import logging

import requests
from imutils.video import WebcamVideoStream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MotionTracker")


def read_camera_output(conf, args):
    # initialize the camera
    camera = WebcamVideoStream(src=args["video_input"]).start()

    # allow the camera to warmup, then initialize the average frame and last movement detection
    logger.info("warming up...")
    time.sleep(conf["camera_warmup_time"])
    avg = None
    last_movement = None
    last_post_status = None
    there_is_movement = None
    time_threshold = None
    last_post_time = datetime.datetime.now()

    # capture frames from the camera
    while True:
        frame = camera.read()
        timestamp = datetime.datetime.now()

        # resize the frame, convert it to grayscale, and blur it
        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        # if the average frame is None, initialize it
        if avg is None:
            logger.info("starting background model...")
            avg = gray.copy().astype("float")
            continue

        # accumulate the weighted average between the current frame and
        # previous frames, then compute the difference between the current
        # frame and running average
        cv2.accumulateWeighted(gray, avg, 0.5)
        frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

        # threshold the delta image, dilate the thresholded image to fill
        # in holes, then find contours on thresholded image
        thresh = cv2.threshold(frame_delta, conf["delta_thresh"], 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        (image, contours, hierarchy) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # loop over the contours
        for c in contours:
            if cv2.contourArea(c) < conf["min_area"]:
                continue

            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
            last_movement = datetime.datetime.now()

        if last_movement is not None:
            time_threshold = int((timestamp - last_movement).total_seconds()) >= conf['minimum_time_delta']

        if last_movement is None:
            pass
        elif time_threshold:
            there_is_movement = False
            post_status = False
        else:
            there_is_movement = True
            post_status = True

        if last_movement is None:
            logger.debug("TS: {} || LAST MVMNT: -------------------------- || DIFF - || THERE IS MOVEMENT: {}".format(
                         timestamp, there_is_movement))
        else:
            logger.debug("TS: {} || LAST MVMNT: {} || DIFF {} || THERE IS MOVEMENT: {}".format(
                         timestamp, last_movement, int((timestamp - last_movement).total_seconds()), there_is_movement))

        # draw the text and timestamp on the frame
        ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
        cv2.putText(frame, "Movement detected: {}".format(there_is_movement), (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        cv2.putText(frame, ts, (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.35, (0, 0, 255), 1)
        cv2.putText(frame, "Last movement detected at: {}".format(last_movement), (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # if datetime.timedelta(timestamp - last_post_time).total_seconds() >= 10 and (last_post_status != post_status):
        #     logger.info("POSTing room status to server. ")
        #     requests.post("http://0.0.0.0:8899/room_tracker/", data=post_status)
        #     last_post_status = post_status
        #     last_post_time = datetime.datetime.now()


        # check to see if the frames should be displayed to screen
        if conf["show_video"]:
            # display the security feed
            cv2.imshow("Security Feed", frame)
            cv2.imshow('Threshold', thresh)
            key = cv2.waitKey(1) & 0xFF

            # if the `q` key is pressed, break from the lop
            if key == ord("q"):
                break

