import json
import time
import urllib.request
import urllib.parse
from os import environ


def slack(
    header=None,
    text=' ',
    icon_emoji=None,
    thread=None,
    channel=environ.get('SLACK_CHANNEL', 'kamer-213-backend'),
    url=environ.get('SLACK_API_URL', 'https://www.slack.com/api/chat.postMessage'),
    token=environ.get("SLACK_API_TOKEN"),
    sleep=0.25,
):
    """
    Send a message to slack as an installed app using the rest api.

    :param channel: The channel to send the message to.
    :param header: The "header", replaces the app name with this text.
    :param text: The actual body of the message to send.
    :param icon_emoji: Replace the app avatar with this emoji.
    :param thread: When supplied will be sent as a reply to a thread, this is the id of the parent message
    :param url: slack api url
    :param token: api token for the app
    :param sleep: try and rate limit sending this message by sleeping a bit after sending

    :return: Id of the message that was sent.
    """
    body = {'channel': channel, 'text': text, 'token': token}

    if header:
        body['username'] = header
    if icon_emoji:
        body['icon_emoji'] = icon_emoji
    if thread:
        body['thread_ts'] = thread

    data = urllib.parse.urlencode(body).encode()
    request = urllib.request.Request(url, data=data, method='POST')
    response = urllib.request.urlopen(request)
    response_body = json.load(response)

    if not response_body['ok']:
        raise RuntimeError(response_body)

    message_id = response_body['ts']

    if sleep:
        time.sleep(sleep)

    return message_id
