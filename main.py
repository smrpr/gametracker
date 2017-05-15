import argparse
import json

from motion_tracker.motion_tracker import read_camera_output

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--conf", required=True, help="path to the JSON configuration file")
    ap.add_argument("-v", "--video_input", type=int, default=0, help="video input source")
    args = vars(ap.parse_args())
    conf = json.load(open(args["conf"]))

    read_camera_output(conf, args)
