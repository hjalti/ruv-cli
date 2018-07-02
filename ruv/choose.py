import curses

import logging
logging.basicConfig(filename='output.log',level=logging.DEBUG,filemode='w')

DOWN_KEYS = (curses.KEY_DOWN, ord('j'))
UP_KEYS = (curses.KEY_UP, ord('k'))
QUIT_KEYS = (27, ord('q'))
PAGE_STEP = 15

class Line:
    def __init__(self, win, text):
        self.text = text
        self.lines = text.splitlines()
        self.size = len(self.lines)
        self.win = win

    def display(self, index, selected, width):
        color = normalText
        if selected:
            color = highlightText

        for line in self.lines:
            self.win.addstr(index, 2, line.ljust(width - 4), color)
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

    def display(self, width):
        display_index = 1
        for ind, line in enumerate(self.lines):
            display_index = line.display(display_index, ind == self.index, width)


class ListDisplay:
    def __init__(self, items):
        if not items:
            raise ValueError('List cannot be empty')
        self.index = 0
        self.page = 0
        self.setup()
        self.lines = [Line(self.box, it) for it in items]
        self.paginate()

    def current_page(self):
        return self.pages[self.page]

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
        global highlightText, normalText
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        self.screen.keypad(1)
        curses.curs_set(0)
        self.update_size()

        curses.init_pair(1,curses.COLOR_BLACK, curses.COLOR_CYAN)
        highlightText = curses.color_pair(1)
        normalText = curses.A_NORMAL

        self.box = curses.newwin(self.rows, self.cols, 1, 1)
        self.box.box()

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
        self.box.resize(self.rows, self.cols)
        self.screen.erase()
        self.paginate()
        self._find_current_page()

    def _display_page_number(self):
        index = self.rows - 1
        self.box.addstr(index, 2, f' Page {self.page + 1} / {len(self.pages)} ', normalText)

    def _display_page(self):
        self.current_page().display(self.cols)
        self._display_page_number()

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
        if not self.current_page().up():
            self.page -= 1
            self.current_page().last()

    def down(self):
        if self.index == len(self.lines) - 1:
            return
        self.index += 1
        if not self.current_page().down():
            self.page += 1
            self.current_page().first()

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
        if x == ord('g'):
            self.first()
        if x == ord('G'):
            self.last()
        if x == ord('\n'):
            return False
        return True

    def display(self):
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
        except:
            logging.exception('Something bad happened')
            logging.debug('Dict: %s', self.__dict__)


def choose(choices, display=None):
    formatted = choices
    if display is not None:
        formatted = [display(ch) for ch in choices]
    list_display = ListDisplay(formatted)
    list_display.display()
    selected = list_display.index
    if selected is None:
        return None
    return choices[selected]

