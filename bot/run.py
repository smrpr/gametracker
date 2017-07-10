import random
import re

import requests
from slackbot.bot import Bot, listen_to

from bot.slackbot_settings import STATUS_ENDPOINT, OCCUPIED_MSGS_LIST, FREE_MSGS_LIST


@listen_to("room status", re.IGNORECASE)
@listen_to("is free", re.IGNORECASE)
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
        msg = random.choice(OCCUPIED_MSGS_LIST).format(t1)
    else:
        msg = random.choice(FREE_MSGS_LIST).format(t2)

    message.send("{}".format(msg))


def main():
    bot = Bot()
    bot.run()


if __name__ == "__main__":
    main()
