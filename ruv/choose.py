import curses

from collections import namedtuple
import textwrap
import logging
import re

BULLET = '•'

MIN_HEIGHT = 5

DOWN_KEYS = (curses.KEY_DOWN, ord('j'))
UP_KEYS = (curses.KEY_UP, ord('k'))
START_KEYS = (curses.KEY_HOME, ord('g'))
END_KEYS = (curses.KEY_END, ord('G'))
QUIT_KEYS = (27, ord('q'))
PAGE_STEP = 15

starting_space = re.compile(r'^ +')

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
        color = curses.A_NORMAL
        if selected:
            color = highlightText

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
    def __init__(self, items, title=None, display=str, itemize=None, initial_index=0):
        if not items:
            raise ValueError('List cannot be empty')
        if initial_index >= len(items):
            raise ValueError('Initial index too large')

        self.index = initial_index
        self.page = 0
        self.title = title
        self.setup()
        self.items = items
        self.display = display
        self.itemize = itemize

        self._update_lines()
        self.paginate()
        self._find_current_page()

    @property
    def current_page(self):
        return self.pages[self.page]

    @property
    def title_height(self):
        if self.title is None or not self.title_lines:
            return 0
        return len(self.title_lines)

    def paginate(self):
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

    def update_size(self):
        y, x = self.screen.getmaxyx()
        self.rows = y - 2
        self.cols = x - 2

    def setup(self):
        global highlightText
        self.screen = curses.initscr()
        self.screen.erase()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        self.screen.keypad(1)
        curses.curs_set(0)
        self.update_size()

        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        highlightText = curses.color_pair(1)

        self._setup_title()
        self.box = curses.newwin(self.rows, self.cols, self.title_height + 1, 1)
        self.box.box()

    def _update_lines(self):
        self.lines = [Line(self.box, self.display(it), self.cols, self.itemize) for it in self.items]

    def _setup_title(self):
        if self.title is None:
            self.title_lines = []
            return
        self.title_lines = wrap(self.title, self.cols - 2, max_lines=5)
        self.rows -= len(self.title_lines)

    def _display_title(self):
        stuff = curses.color_pair(2)
        for index, line in enumerate(self.title_lines):
            self.screen.addstr(index + 1, 2, line, stuff | curses.A_BOLD)

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
        self.update_size()
        if self.rows < MIN_HEIGHT:
            return
        self._setup_title()
        logging.debug('Title height: %s', self.title_height)
        logging.debug('Calling move(%s, %s)', self.title_height + 1, 1)
        self.box = curses.newwin(self.rows, self.cols, self.title_height + 1, 1)
        self._update_lines()
        self.screen.erase()
        self.box.erase()
        self.paginate()
        self._find_current_page()

    def _display_page_number(self):
        index = self.rows - 1
        page_text = f' Page {self.page + 1} / {len(self.pages)} '[:self.cols-2]
        position = max(self.cols - len(page_text) - 2, 1)
        self.box.addstr(index, position, page_text, curses.A_NORMAL)

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

    def _handle_keypress(self, x):
        if x in UP_KEYS:
            self.up()
        if x in DOWN_KEYS:
            self.down()
        if x == curses.KEY_PPAGE or curses.keyname(x) == b'^U':
            self.page_up()
        if x == curses.KEY_NPAGE or curses.keyname(x) == b'^D':
            self.page_down()
        if x == curses.KEY_RESIZE:
            self._resize()
        if x in START_KEYS:
            self.first()
        if x in END_KEYS:
            self.last()
        if x == ord('\n'):
            return False
        return True

    def choose(self):
        try:
            self._display_page()

            x = self.screen.getch()
            while x not in QUIT_KEYS:
                logging.debug('key pressed %s (%s), keyname: %s', x, bin(x), curses.keyname(x))
                if not self._handle_keypress(x):
                    break
                logging.debug('Index: %s, Page: %s', self.index, self.page)

                self.box.erase()
                self.box.border(0)

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


def choose(choices, title=None, display=None, index=True, itemize=None, bullet=False, initial_index=0):
    extra_args = {'itemize': itemize}
    if bullet:
        extra_args['itemize'] = BULLET
    list_display = ListDisplay(
            choices,
            title,
            display=display,
            initial_index=initial_index,
            **extra_args
    )
    return list_display.choose()
