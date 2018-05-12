import utils
from slackclient import SlackClient
import json
import time
import os


def get_token():
    path = os.path.join('res', 'token_slack.json')
    with open(path) as jsn:
        data = json.load(jsn)
    return data['token']


slack_client = SlackClient(get_token())
starterbot_id = None

# Constants.
RTM_READ_DELAY = 1  # 1 second delay between reading from RTM.
counter = 0


def parse_bot_commands(slack_events):
    for event in slack_events:
        if event["type"] == "message" and "subtype" not in event:
            message = event["text"]
            return message, event["channel"]
    return None, None


def handle_command(command, channel):
    global counter
    backends = ['ibmqx4', 'ibmqx5']
    backend = command
    if backend in backends:
        counter += 1
        response = "Wait a sec ..."
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response
        )
        # Gathering statistics.
        filename = 'tmp/{}_to_send.png'.format(backend)
        utils.create_statistics_image(backend)
        slack_client.api_call(
            'files.upload',
            channels=channel,
            as_user=True,
            filename=backend,
            file=open(filename, 'rb'),
        )
    elif command == 'info':
        response = str(counter)
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response
        )
    else:
        response = "I'm sorry, I don't understand!\n I understand only these messages: *ibmqx4* or *ibmqx5*"
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response
        )


def main():
    if slack_client.rtm_connect(with_team_state=False):
        print("Bot is connected and running!")

        # Read bot's user ID by calling Web API method `auth.test`.
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")


if __name__ == "__main__":
    main()
