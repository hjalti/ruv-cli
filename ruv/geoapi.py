import requests

CHANNEL_STREAM_URL = 'https://geo.spilari.ruv.is/channel/{}'

def get_channel_stream(chan):
    res = requests.get(CHANNEL_STREAM_URL.format(chan))
    return res.json()
