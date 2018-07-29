import argparse
import subprocess
import re
import sys
from functools import partial
from datetime import timedelta, date
from urllib.parse import urlsplit, parse_qs

from requests.exceptions import HTTPError, ConnectionError

from .choose import choose
from .conf import config_exists, copy_config, CONFIG_PATH, PLAYER, DEFAULT_TERMINAL_COLORS
import ruv.api as api
import ruv.__version__ as about

eprint = partial(print, file=sys.stderr)
choose = partial(choose, default_terminal_colors=DEFAULT_TERMINAL_COLORS)

RUV_URL = 'http://ruv.is/'
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


def graceful(func):
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except HTTPError as e:
            eprint(f'The RUV API responded with an error ({e.response.status_code})')
            eprint(f'URL: {e.request.url}')
        except ConnectionError:
            eprint(f'Error connecting to the RUV API')
    return wrapper


def url(path):
    return RUV_URL + path


def play_stream(args, url):
    if args and args.video_player:
        player = [args.video_player]
    else:
        player = PLAYER
    subprocess.call(player + [url])


def live(args):
    play_stream(args, CHANNELS[args.channel])


def default_live():
    play_stream(None, CHANNELS['ruv'])


def default_live2():
    play_stream(None, CHANNELS['ruv2'])


def radio(args):
    play_stream(args, RADIO[args.channel])


def menu(choices, title, on_chosen, display=lambda x: x.display()):
    choice = None
    while True:
        index = (choice and choice.index) or 0
        choice = choose(
                choices,
                title=title,
                display=display,
                initial_index=index
        )
        if choice is None:
            break
        on_chosen(choice.item)


def program_details_menu(args, program_id):
    details = api.program_details(program_id)
    menu(details.episodes, details.header, lambda ep: play_stream(args, ep.file))


def choose_program_menu(args, programs, title):
    def when_chosen(prog):
        if not prog.multiple_episodes:
            play_stream(args, prog.episodes[0].file)
        else:
            program_details_menu(args, prog.id)
    menu(programs, title, when_chosen)


@graceful
def play(args):
    parsed = urlsplit(args.url)
    parts = parsed.path.split('/')
    prog_id = (parts or '') and parts[-1]
    query = parse_qs(parsed.query)
    if not re.fullmatch('\d+', prog_id) or 'ep' not in query:
        print('Unplayable URL')
        return
    ep_id = (query['ep'] or '') and query['ep'][0]
    details = api.program_details(prog_id)
    eps = [ep for ep in details.episodes if ep.id == ep_id]
    if not eps:
        print('Episode not found')
        return
    play_stream(args, eps[0].file)



@graceful
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
                details = api.program_details_menu(program.id)
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
            play_stream(args, episode.file)
        else:
            print('No episodes available')
    else:
        choose_program_menu(args, results.programs, results.title)


@graceful
def featured(args):
    feat = api.featured()
    menu(feat.panels, 'Featured programs', lambda pan: choose_program_menu(args, pan.programs, pan.title), display=lambda pan: pan.title)


@graceful
def schedule(args):
    def when_selected(event):
        if event.is_playable():
            play_stream(args, event.program.episodes[0].file)

    day = date.today() + timedelta(days=args.day)
    schedule = api.schedule(args.channel, day)
    if not schedule.events:
        print('No schedule for selected day')
        return
    menu(schedule.events, schedule.long_title, when_selected)


def config(args):
    if config_exists():
        inp = input('Config file already exists. Overwrite? [y/N] ')
        if not inp.lower().startswith('y'):
            return
    copy_config()
    print(f"Config copied to '{CONFIG_PATH}'")


def version():
    print(f'{about.__name__} {about.__version__}')
    print(f'License: {about.__license__}')
    print(f'Written by {about.__author__} ({about.__author_email__})')


def main():
    parser = argparse.ArgumentParser(description='A command line interface for RUV', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-p', '--video-player', metavar='PLAYER', help='The video player used to play the stream', default=None)
    parser.add_argument('--version', help='Print the version information and exit', action='store_true')

    subparsers = parser.add_subparsers()

    live_parser = subparsers.add_parser('live', help='Watch RUV live')
    live_parser.add_argument('channel', metavar='CHANNEL', help=f'Channel to stream. Choose from: {", ".join(CHANNEL_NAMES)}', default='ruv', nargs='?', choices=CHANNEL_NAMES)
    live_parser.set_defaults(func=live)

    radio_parser = subparsers.add_parser('radio', help='Listen to live radio')
    radio_parser.add_argument('channel', metavar='CHANNEL', help=f'Radio channel to stream. Choose from: {", ".join(RADIO_NAMES)}', default='ras2', nargs='?', choices=RADIO_NAMES)
    radio_parser.set_defaults(func=radio)

    schedule_parser = subparsers.add_parser('schedule', help='See channel schedules')
    schedule_parser.add_argument('-c', '--channel', metavar='CHANNEL', help=f'Channel to stream. Choose from: {", ".join(CHANNEL_NAMES)}. Default: %(default)s', default='ruv')
    schedule_parser.add_argument('day', metavar='DAY', nargs='?', default=0, type=int, help='Day offset. 0 is today, -n is n days in the past and n is n days in the future.')
    schedule_parser.set_defaults(func=schedule)

    show_parser = subparsers.add_parser('search', help='Search for programs')
    show_parser.add_argument('query', metavar='QUERY', help='Search shows matching this query')
    show_parser.add_argument('-p', '--play', help='If query matches any program, the latest episode of the first program will be played.', action='store_true')
    show_parser.add_argument('-o', '--offset', help='Offset when playing an episode. An offset of 1 means the second latest episode will be played, 2 the third latest, etc.',
            default=0, type=int, metavar='OFFSET')
    show_parser.set_defaults(func=search)

    featured_parser = subparsers.add_parser('featured', help='List features programs')
    featured_parser.set_defaults(func=featured)

    play_parser = subparsers.add_parser('play', help='Play a program from a URL')
    play_parser.add_argument('url', metavar='URL', help='URL of the page containing the stream')
    play_parser.set_defaults(func=play)

    config_parser = subparsers.add_parser('config', help='Copy the default configuration to your home directory for customization')
    config_parser.set_defaults(func=config)

    args = parser.parse_args()
    if args.version:
        version()
        return
    if not hasattr(args, 'func'):
        parser.print_help()
    else:
        args.func(args)

if __name__ == '__main__':
    main()
