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

    def display(self, indent=0):
        return format(
            f'''
            {self.title} ({self.firstrun})
                {self.short_description}
            ''',
            indent
        )

class Program(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self._expand_list('episodes', Episode)
        if not self.title:
            self.title = 'unknown'

    def display(self, indent=0):
        title = self.title
        if indent == 0:
            title = title.upper()
        return format(
            f'''
            {title.strip()} ({'Series' if self.multiple_episodes else 'Movie/Short'})
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

    def display(self):
        programs = '\n'.join(p.display(indent=1) for p in self.programs)
        return '\n'.join([
            f'Search results for "{self.search_query}":',
            programs
        ])

class ProgramDetails(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self._expand_list('episodes', Episode)
        self._expand_list('panels', Panel)

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

    def display(self, indent=0):
        return format(f'{self.start_time_friendly}: {self.title}', indent)

class Schedule(ModelBase):
    def __init__(self, dic):
        super().__init__(dic)
        self._expand_list('events', Event)

    def display(self):
        events = '\n'.join(p.display(indent=1) for p in self.events)
        return '\n'.join([
            f'{self.title} - {self.selected_date}',
            events
        ])
