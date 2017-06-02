import re

import requests
from slackbot.bot import Bot, listen_to

STATUS_ENDPOINT = "http://0.0.0.0:8899/api/status"
OCCUPIED_MSG = "The room is occupied. It has been like that since {}."
FREE_MSG = "The room is FREE! Go play some Mario Kart. Last time used was {}."


@listen_to("room status", re.IGNORECASE)
def check_room_status(message):
    room_status = requests.get(STATUS_ENDPOINT).json()

    last_status = room_status['1']
    earlier_status = room_status['2']

    for time, status in last_status.items():
        t1 = time
        s1 = status

    for time, status in earlier_status.items():
        t2 = time
        s2 = status

    if s1 is True:
        msg = OCCUPIED_MSG.format(t1)
    else:
        msg = FREE_MSG.format(t2)

    message.send("> {}".format(msg))


def main():
    bot = Bot()
    bot.run()


if __name__ == "__main__":
    main()
