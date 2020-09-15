from DB import DB


WEEK_DAYS = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
LANGUAGES = {'en': ['English', 'Английский'], 'ru': ['Russian', 'Русский']}
THEME_STYLES = {'light': ['Light', 'Светлая'], 'dark': ['Dark', 'Темная']}


class Schedule(DB):
    def __init__(self, **kwargs):
        super(Schedule, self).__init__(**kwargs)


class Timetable(DB):
    def __init__(self, **kwargs):
        super(Timetable, self).__init__(**kwargs)


class Homework(DB):
    def __init__(self, **kwargs):
        super(Homework, self).__init__(**kwargs)
