import argparse
import re
import requests
import subprocess
from pydoc import pager
from datetime import timedelta, date
from choose import choose

import api

RUV_URL = 'http://ruv.is/'
DEFAULT_PLAYER = '/usr/bin/mpv'
RUV_BASE_URL = 'http://ruvruv-live.hls.adaptive.level3.net/ruv/%s/index.m3u8'
RUV_RADIO_BASE_URL = 'http://sip-live.hds.adaptive.level3.net/hls-live/ruv-%s/_definst_/live.m3u8'
CHANNELS = {
        'ruv': RUV_BASE_URL % 'ruv',
        'ruv2': RUV_BASE_URL % 'ruv2',
}
CHANNEL_NAMES = list(CHANNELS.keys())

RADIO = {
        'ras1': RUV_RADIO_BASE_URL % 'ras1',
        'ras2': RUV_RADIO_BASE_URL % 'ras2',
        'rondo': RUV_RADIO_BASE_URL % 'ras3',
}
RADIO_NAMES = list(RADIO.keys())


def url(path):
    return RUV_URL + path

def play_stream(video_player, url):
    subprocess.call([video_player, url])

def get_playable_url(url):
    resp = requests.get(url)
    return re.search('video\.src = "(.*)";', resp.text).group(1)

def play(args):
    url = get_playable_url(args.url)
    play_stream(args, url)

def live(args):
    play_stream(args.video_player, CHANNELS[args.channel])

def live2(args):
    play_stream(args.video_player, 'ruv2')

def radio(args):
    play_stream(args.video_player, RADIO[args.channel])

def search(args):
    results = api.search(args.query)
    if results.empty():
        print('No shows matched query')
        return
    if args.play:
        program = results.programs[0]
        print('Chosen show is: %s' % program.title)
        episodes = program.episodes
        if episodes:
            if args.offset:
                details = api.program_details(program.id)
                episodes = details.episodes
            if args.offset >= len(episodes):
                print('Offset out of range, playing oldest')
                args.offset = -1
            episode = episodes[args.offset]
            print(f"Playing:")
            if program.multiple_episodes:
                print(episode.display())
            else:
                print(program.display())
            play_stream(args.video_player, episode.file)
        else:
            print('No episodes available')
    else:
        print('Search results:')
        pager(results.display())

def featured(args):
    feat = api.featured()
    while True:
        panel = choose(feat.panels, lambda x: x.title)
        if panel is None:
            return
        program = choose(panel.programs, lambda x: x.display())
        if program is None:
            continue
        play_stream(args.video_player, program.episodes[0].file)
        break


def schedule(args):
    day = date.today() + timedelta(days=args.day)
    schedule = api.schedule(args.channel, day)
    choice = choose(schedule.events, lambda x: x.display())
    if choice:
        if not choice.program or not choice.web_accessible:
            print('This event cannot be played')
        else:
            play_stream(args.video_player, choice.program.episodes[0].file)

def main():
    parser = argparse.ArgumentParser(description='A command line interface for RUV', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-p', '--video-player', metavar='PLAYER', help='The video player used to play the stream', default=DEFAULT_PLAYER)

    subparsers = parser.add_subparsers()

    play_parser = subparsers.add_parser('play', help='Play a program from a URL')
    play_parser.add_argument('url', metavar='URL', help='URL of the page containing the stream')
    play_parser.set_defaults(func=play)

    live_parser = subparsers.add_parser('live', help='Watch RUV live')
    live_parser.add_argument('channel', metavar='CHANNEL', help=f'Channel to stream. Choose from: {", ".join(CHANNEL_NAMES)}', default='ruv', nargs='?', choices=CHANNEL_NAMES)
    live_parser.set_defaults(func=live)

    radio_parser = subparsers.add_parser('radio', help='Listen to live radio')
    radio_parser.add_argument('channel', metavar='CHANNEL', help=f'Radio channel to stream. Choose from: {", ".join(RADIO_NAMES)}', default='ras2', nargs='?', choices=RADIO_NAMES)
    radio_parser.set_defaults(func=radio)

    show_parser = subparsers.add_parser('search', help='List and watch RUV shows')
    show_parser.add_argument('query', metavar='QUERY', help='Search shows matching this query')
    show_parser.add_argument('-p', '--play', help='If query matches any program, the latest episode of the first program will be played.', action='store_true')
    show_parser.add_argument('-o', '--offset', help='Offset when playing an episode. An offset of 1 means the second latest episode will be played, 2 the third latest, etc.',
            default=0, type=int, metavar='OFFSET')
    show_parser.set_defaults(func=search)

    featured_parser = subparsers.add_parser('featured', help='List features programs')
    featured_parser.set_defaults(func=featured)

    schedule_parser = subparsers.add_parser('schedule', help='List and watch RUV shows')
    schedule_parser.add_argument('-c', '--channel', metavar='CHANNEL', help=f'Channel to stream. Choose from: {", ".join(CHANNEL_NAMES)}. Default: %(default)s', default='ruv')
    schedule_parser.add_argument('day', metavar='DAY', help=f'', nargs='?', default=0, type=int)
    schedule_parser.set_defaults(func=schedule)


    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
    else:
        args.func(args)

if __name__ == '__main__':
    main()
