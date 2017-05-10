import argparse
import re
import requests
import subprocess
import pydoc

from bs4 import BeautifulSoup

RUV_URL = 'http://ruv.is/'
DEFAULT_PLAYER = '/usr/bin/mpv'
RUV_LIVE_URL = 'http://ruvruv-live.hls.adaptive.level3.net/ruv/ruv/index.m3u8'

def url(path):
    return RUV_URL + path

def play_stream(args, url):
    subprocess.call([args.video_player, url])

def get_playable_url(url):
    resp = requests.get(url)
    return re.search('video\.src = "(.*)";', resp.text).group(1)

def play(args):
    url = get_playable_url(args.url)
    play_stream(args, url)

def live(args):
    play_stream(args, RUV_LIVE_URL)

def paginate_show_list(lis):
    pydoc.pager('\n'.join(x[1] for x in lis))

def episode_list(path):
    import pdb; pdb.set_trace()
    req = requests.get(url(path))
    soup = BeautifulSoup(req.text, "html.parser")
    episodes_path = soup.find('a', text='Fleiri þættir')
    if episodes_path is not None:
        episodes_path = episodes_path['href']
        req = requests.get(url(episodes_path))
        soup = BeautifulSoup(req.text, "html.parser")
        episodes = soup(class_='views-row')[1:]
        most_recent_date = soup.find('div', class_='pane-spilari-panel-pane-4').find('div', class_='border-bottom').find(class_='fl').text.split(maxsplit=2)[-1]
        episodes = [ (episodes_path, most_recent_date) ] + [ (x.h3.a['href'], x.find(class_='col3').text.splitlines()[0].split()[-1]) for x in episodes ]
        return episodes
    return None

def shows(args):
    req = requests.get(url('thaettir/ruv'))
    soup = BeautifulSoup(req.text, "html.parser")
    show_list = [ (x.strong.a.text, x.strong.a['href']) for x in soup('div', class_='views-row') ]
    if args.query is None:
        paginate_show_list(show_list)
    else:
        results = [ (show, url) for show, url in show_list if args.query.lower() in show.lower() ]
        if len(results) == 0:
            print('No shows matched query')
        elif len(results) == 1:
            show, path = results[0]
            print('Chosen show is: %s' % show)
            elist = episode_list(path)
            if args.play:
                if args.offset < len(elist):
                    print('Offset out of range, playing latest')
                    args.offset = 0
                epath, date = elist[args.offset]
                print('Playing episode published: %s', date)
                play_stream(args, get_playable_url(url(epath)))
            else:
                print('Episode list:')
                print('\n'.join( '%s: %s' % (i, x[0]) for i, x in enumerate(elist)) )
        else:
            paginate_show_list(results)

def main():
    parser = argparse.ArgumentParser(description='A command line interface for RUV', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-p', '--video-player', metavar='PLAYER', help='The video player used to play the stream', default=DEFAULT_PLAYER)

    subparsers = parser.add_subparsers()

    play_parser = subparsers.add_parser('play', help='Play')
    play_parser.add_argument('url', metavar='URL', help='URL of the page containing the stream')
    play_parser.set_defaults(func=play)

    live_parser = subparsers.add_parser('live', help='Watch RUV live')
    live_parser.set_defaults(func=live)

    show_parser = subparsers.add_parser('shows', help='List and watch RUV shows')
    show_parser.add_argument('query', metavar='QUERY', help='Search shows matching this query', nargs='?', default=None)
    show_parser.add_argument('-p', '--play', help='If query matches exactly one show, the latest episode will be played.', action='store_true')
    show_parser.add_argument('-o', '--offset', help='Offset when playing an episode. An offset of 1 means the second latest episode will be played, 2 the third latest, etc.',
            default=0, type=int, metavar='OFFSET')
    show_parser.set_defaults(func=shows)

    args = parser.parse_args()
    if not hasattr(args, 'func'):
        parser.print_help()
    else:
        args.func(args)

if __name__ == '__main__':
    main()
