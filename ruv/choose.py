import curses

import textwrap
import logging
import re
import os

from collections import namedtuple

BULLET = '•'

MIN_HEIGHT = 5

CTRL = 0b1100000
DOWN_KEYS = (curses.KEY_DOWN, ord('j'))
UP_KEYS = (curses.KEY_UP, ord('k'))
START_KEYS = (curses.KEY_HOME, ord('g'))
PAGE_UP_KEYS = (curses.KEY_PPAGE, CTRL ^ ord('u'))
PAGE_DOWN_KEYS = (curses.KEY_NPAGE, CTRL ^ ord('d'))
END_KEYS = (curses.KEY_END, ord('G'))
QUIT_KEYS = (27, ord('q'))
PAGE_STEP = 15

starting_space = re.compile(r'^ +')

# Set shorter delay for Esc key
os.environ.setdefault('ESCDELAY', '25')

class Colors:
    pass

COLORS = Colors()

def wrap(text, width, indent=0, **kwargs):
    try:
        ind = ' ' * indent
        first, *rest = text.splitlines()
        first_wrap = textwrap.wrap(first, width, subsequent_indent=ind, **kwargs)
        rest_wrap = []
        for line in rest:
            match = starting_space.match(line)
            extra_indent = ''
            if match:
                extra_indent = match.group()
            rest_wrap.extend(textwrap.wrap(line, width, subsequent_indent=ind + extra_indent, initial_indent=ind, **kwargs))
        return [*first_wrap, *rest_wrap]
    except ValueError:
        return []

class Line:
    def __init__(self, win, text, width, itemize):
        self.text = text
        self.width = width - 4
        indent = 0
        if itemize:
            text = f'{itemize} {text}'
            indent = len(itemize) + 1
        self.lines = wrap(text, self.width, indent=indent, max_lines=3)
        self.size = len(self.lines)
        self.win = win

    def display(self, index, selected):
        color = COLORS.normal
        if selected:
            color = COLORS.highlight

        for line in self.lines:
            self.win.addstr(index, 2, line.ljust(self.width), color)
            index += 1
        return index


class Page:
    def __init__(self, lines):
        self.lines = lines
        self.index = 0

    def up(self):
        if self.index == 0:
            return False
        self.index -= 1
        return True

    def down(self):
        if self.index == len(self.lines) - 1:
            return False
        self.index += 1
        return True

    def last(self):
        self.index = len(self.lines) - 1

    def first(self):
        self.index = 0

    def display(self):
        display_index = 1
        for ind, line in enumerate(self.lines):
            display_index = line.display(display_index, ind == self.index)

Choice = namedtuple('Choice', ['index', 'item'])

class ListDisplay:
    def __init__(self, items, title=None, display=str, itemize=None, initial_index=0, allow_exit=True, default_terminal_colors=False):
        if not items:
            raise ValueError('List cannot be empty')
        if initial_index >= len(items):
            raise ValueError('Initial index too large')

        self.index = initial_index
        self.page = 0
        self.title = title
        self._setup(default_terminal_colors)
        self.items = items
        self.display = display
        self.itemize = itemize
        self.allow_exit = allow_exit

        self._update_lines()
        self._paginate()
        self._find_current_page()

    @property
    def current_page(self):
        return self.pages[self.page]

    @property
    def title_height(self):
        if self.title is None or not self.title_lines:
            return 0
        return len(self.title_lines)

    def _paginate(self):
        self.pages = []
        page_lines = []
        page_height = 0
        for index, line in enumerate(self.lines):
            if page_height + line.size >= self.rows - 1:
                self.pages.append(Page(page_lines))
                page_lines = []
                page_height = 0
            page_lines.append(line)
            page_height += line.size
        self.pages.append(Page(page_lines))

    def _update_size(self):
        y, x = self.screen.getmaxyx()
        self.rows = y - 2
        self.cols = x - 2

    def _setup(self, default_colors):
        self.screen = curses.initscr()
        self.screen.erase()
        curses.noecho()
        curses.cbreak()
        curses.start_color()

        if default_colors:
            curses.use_default_colors()
            COLORS.normal = curses.A_NORMAL
            COLORS.highlight = curses.A_STANDOUT
            COLORS.title = curses.A_BOLD
        else:
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
            COLORS.normal = curses.color_pair(1)
            COLORS.highlight = curses.color_pair(2)
            COLORS.title = curses.color_pair(3) | curses.A_BOLD

        self.screen.keypad(1)
        curses.curs_set(0)
        self._update_size()

        self._setup_title()
        self.box = curses.newwin(self.rows, self.cols, self.title_height + 1, 1)
        self.box.attron(COLORS.normal)
        self.box.box()
        self.box.attroff(COLORS.normal)

    def _update_lines(self):
        self.lines = [Line(self.box, self.display(it), self.cols, self.itemize) for it in self.items]

    def _setup_title(self):
        if self.title is None:
            self.title_lines = []
            return
        self.title_lines = wrap(self.title, self.cols - 2, max_lines=5)
        self.rows -= len(self.title_lines)

    def _display_title(self):
        for index, line in enumerate(self.title_lines):
            self.screen.addstr(index + 1, 2, line, COLORS.title)

    def _find_current_page(self):
        ind = self.index
        for page_ind, page in enumerate(self.pages):
            page_lines = len(page.lines)
            if ind >= page_lines:
                ind -= page_lines
            else:
                self.page = page_ind
                page.index = ind
                return

    def _resize(self):
        self._update_size()
        if self.rows < MIN_HEIGHT:
            return
        self._setup_title()
        logging.debug('Title height: %s', self.title_height)
        logging.debug('Calling move(%s, %s)', self.title_height + 1, 1)
        self.box = curses.newwin(self.rows, self.cols, self.title_height + 1, 1)
        self._update_lines()
        self.screen.erase()
        self.box.erase()
        self._paginate()
        self._find_current_page()

    def _display_page_number(self):
        index = self.rows - 1
        page_text = f' Page {self.page + 1} / {len(self.pages)} '[:self.cols-2]
        position = max(self.cols - len(page_text) - 2, 1)
        self.box.addstr(index, position, page_text, COLORS.normal)

    def _display_page(self):
        if self.rows < MIN_HEIGHT:
            return
        self.current_page.display()
        self._display_page_number()
        self._display_title()

        self.screen.refresh()
        self.box.refresh()

    def page_up(self):
        if self.index < PAGE_STEP:
            self.index = 0
        else:
            self.index -= PAGE_STEP
        self._find_current_page()

    def page_down(self):
        if self.index > len(self.lines) - 1 - PAGE_STEP:
            self.index = len(self.lines) - 1
        else:
            self.index += PAGE_STEP
        self._find_current_page()

    def up(self):
        if self.index == 0:
            return
        self.index -= 1
        if not self.current_page.up():
            self.page -= 1
            self.current_page.last()

    def down(self):
        if self.index == len(self.lines) - 1:
            return
        self.index += 1
        if not self.current_page.down():
            self.page += 1
            self.current_page.first()

    def last(self):
        self.index = len(self.lines) - 1
        self._find_current_page()

    def first(self):
        self.index = 0
        self._find_current_page()

    def handle_keypress(self, x):
        actions = [
            (UP_KEYS, self.up),
            (DOWN_KEYS, self.down),
            (PAGE_UP_KEYS, self.page_up),
            (PAGE_DOWN_KEYS, self.page_down),
            ((curses.KEY_RESIZE,), self._resize),
            (START_KEYS, self.first),
            (END_KEYS, self.last),
        ]
        if x == ord('\n'):
            return False
        for keys, action in actions:
            if x in keys:
                action()
        return True

    def choose(self):
        try:
            self._display_page()

            x = self.screen.getch()
            while x not in QUIT_KEYS or not self.allow_exit:
                logging.debug('key pressed %s (%s), keyname: %s', x, bin(x), curses.keyname(x))
                if not self.handle_keypress(x):
                    break
                logging.debug('Index: %s, Page: %s', self.index, self.page)

                self.box.erase()
                self.box.attron(COLORS.normal)
                self.box.border(0)
                self.box.attroff(COLORS.normal)

                self._display_page()

                x = self.screen.getch()
            else:
                self.index = None

            curses.endwin()

            if self.index is None:
                return None
            return Choice(self.index, self.items[self.index])
        except:
            logging.exception('Something bad happened')


def choose(choices, title=None, display=None, index=True, **args):
    if 'bullet' in args:
        args['itemize'] = BULLET
        del args['bullet']
    list_display = ListDisplay(
            choices,
            title,
            display=display,
            **args
    )
    return list_display.choose()
