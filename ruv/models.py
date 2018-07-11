from pprint import pformat
from datetime import datetime
import textwrap

TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

class ModelBase:
    def __init__(self, dic):
        self.__dict__.update(dic)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return pformat(self.__dict__)

    def _expand_list(self, name, model):
        if hasattr(self, name):
            attr = getattr(self, name)
            if attr:
                setattr(self, name, [model(a) for a in attr])

    def _expand(self, name, model):
        if hasattr(self, name):
            attr = getattr(self, name)
            if attr:
                setattr(self, name, model(attr))

def format(st, indent=0):
    wat = textwrap.indent(
            textwrap.dedent(st.lstrip('\n').rstrip()),
            indent * 4 * ' '
    )
    return wat

def parse_date(date):
    return datetime.strptime(date, TIME_FORMAT)

def format_time(date):
    return datetime.strftime(date, '%H:%M')

class Episode(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self.files = ModelBase(self.files)

    def _short_description(self):
        if self.short_description:
            return self.short_description
        return '[No description]'

    def display(self, indent=0):
        return format(
            f'''
            {self.title} ({self.firstrun})
                {self._short_description()}
            ''',
            indent
        )

class Program(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self._expand_list('episodes', Episode)
        if not self.title:
            self.title = 'unknown'

    def _title(self):
        if self.foreign_title:
            return self.foreign_title
        return self.title

    def display(self, indent=0):
        title = self.title
        if indent == 0:
            title = title.upper()
        return format(
            f'''
            {self._title().strip()} ({'Series' if self.multiple_episodes else 'Movie/Short'})
                {self.short_description.strip()}
            ''',
            indent
        )

class Panel(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self._expand_list('programs', Program)

    def display(self, indent=0):
        programs = '\n'.join(p.display(indent=1) for p in self.programs)
        return '\n'.join([
            f'{self.title.upper()}:',
            programs
        ])

class SearchResults(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self._expand_list('programs', Program)

    def empty(self):
        return self.program_count == 0

    def __bool__(self):
        return not self.empty()

    @property
    def title(self):
        return f'Search results for "{self.search_query}"'


    def display(self):
        programs = '\n'.join(p.display(indent=1) for p in self.programs)
        return '\n'.join([
            f'{self.title}:',
            programs
        ])

class ProgramDetails(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self._expand_list('episodes', Episode)
        self._expand_list('panels', Panel)

    @property
    def long_description(self):
        return '\n'.join(self.description)

    @property
    def header(self):
        return format(
            f'''
            {(self.title or '[no title]').upper()}
            {self.short_description}
            '''
        )

class Overview(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self._expand_list('panels', Panel)

    def display(self, indent=0):
        return '\n'.join(p.display() for p in self.panels)

class Event(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self._expand('program', Program)

    @property
    def start_time_friendly(self):
        return format_time(parse_date(self.start_time))

    @property
    def full_description(self):
        return '\n'.join(self.description)

    def is_available(self):
        return self.web_accessible and self.program is not None

    def has_passed(self):
        return self.program and self.program.episodes

    def is_playable(self):
        return self.has_passed() and self.is_available()

    def _episode_of(self):
        if hasattr(self, 'episode_number'):
            return f' ({self.episode_number} of {self.number_of_episodes})'
        return ''

    def _title(self):
        if self.original_title:
            return f'{self.title} ({self.original_title})'
        return self.title

    def display(self, indent=0):
        availability = ''
        if not self.is_available():
            availability = ' [Not available]'
        elif not self.has_passed():
            availability = ' [Not started]'

        return format(
            f'''
            {self.start_time_friendly}: {self._title()}{self._episode_of()}{availability}
                   {self.full_description}
            ''',
            indent
        )

class Schedule(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self._expand_list('events', Event)

    @property
    def long_title(self):
        return f'{self.title} - {self.selected_date}'

    def display(self):
        events = '\n'.join(p.display(indent=1) for p in self.events)
        return '\n'.join([
            f'{self.title} - {self.selected_date}',
            events
        ])
