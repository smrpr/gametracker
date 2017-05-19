import datetime
import logging
import time

import cv2
import imutils
import requests
from imutils.video import WebcamVideoStream

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MotionTracker")


def build_json_payload(flag):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {timestamp: flag}


def send_data(conf, there_is_movement_flag):
    endpoint = conf["server"]["url"]
    json = build_json_payload(there_is_movement_flag)
    headers = {'content-type': 'application/json'}
    try:
        requests.post(endpoint, json=json, headers=headers)
        logger.info("POST status '%s' to %s", there_is_movement_flag, endpoint)
    except:
        logger.critical("Looks like the server is not online. Nothing has been sent.")


def read_camera_output(conf, args):
    camera = WebcamVideoStream(src=args["video_input"]).start()
    logger.info("warming up...")
    time.sleep(conf["camera"]["camera_warmup_time"])

    avg = None
    last_movement_timestamp = None
    there_is_movement_flag = False
    time_threshold = None
    last_post_status = None

    while True:
        frame = camera.read()
        timestamp = datetime.datetime.now()

        frame = imutils.resize(frame, width=500)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if avg is None:
            logger.info("starting background model...")
            avg = gray.copy().astype("float")
            continue

        cv2.accumulateWeighted(gray, avg, 0.5)
        frame_delta = cv2.absdiff(gray, cv2.convertScaleAbs(avg))

        thresh = cv2.threshold(frame_delta, conf["camera"]["delta_thresh"], 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        (image, contours, hierarchy) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for c in contours:
            if cv2.contourArea(c) < conf["camera"]["min_area"]:
                continue

            (x, y, w, h) = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 1)
            last_movement_timestamp = datetime.datetime.now()

        if last_movement_timestamp is not None:
            time_threshold = int((timestamp - last_movement_timestamp).total_seconds()) >= conf["camera"][
                'minimum_time_delta']

        if last_movement_timestamp is None:
            pass
        elif time_threshold:
            there_is_movement_flag = False
        else:
            there_is_movement_flag = True

        if last_post_status is None or last_post_status is not there_is_movement_flag:
            send_data(conf, there_is_movement_flag)
            last_post_status = there_is_movement_flag

        # time.sleep(0.5)

        if conf["camera"]["show_video"]:
            ts = timestamp.strftime("%A %d %B %Y %I:%M:%S%p")
            cv2.putText(frame, "Movement detected: {}".format(there_is_movement_flag), (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            cv2.putText(frame, ts, (10, frame.shape[0] - 30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.35, (0, 0, 255), 1)
            cv2.putText(frame, "Last movement detected at: {}".format(last_movement_timestamp),
                        (10, frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # display the security feed
            cv2.imshow("Security Feed", frame)
            cv2.imshow('Threshold', thresh)
            key = cv2.waitKey(1) & 0xFF

            # if the `q` key is pressed, break from the lop
            if key == ord("q"):
                break
