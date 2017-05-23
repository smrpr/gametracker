import re

import requests
from slackbot.bot import Bot, listen_to


STATUS_ENDPOINT = "http://0.0.0.0:8899/api/status"

@listen_to("room status", re.IGNORECASE)
def check_room_status(message):
    room_status = requests.get(STATUS_ENDPOINT)
    print(room_status)
    room_status['1'].value()

    message.send("> ", room_status['1'].value())

    if message._client.users.get(message.body["user"])["name"] == '' and randomizer:
        message.react("+1")

def main():
    bot = Bot()
    bot.run()

if __name__ == "__main__":
    main()
