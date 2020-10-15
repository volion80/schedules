from Config import config
if config['env'] == 'dev_home':
    import os
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivymd.uix.tab import MDTabsBase, MDTabs
from kivymd.uix.list import MDList, TwoLineRightIconListItem
from kivy.uix.scrollview import ScrollView
from kivymd.uix.toolbar import MDBottomAppBar, MDToolbar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from kivy.properties import NumericProperty, ObjectProperty, StringProperty
from kivy.utils import get_color_from_hex
from kivymd.toast import toast
from kivymd.uix.button import MDIconButton
from kivy.metrics import dp
from kivymd.uix.bottomsheet import MDListBottomSheet
from kivymd.uix.picker import MDTimePicker
from kivymd.uix.label import MDLabel
import uuid
import datetime
from Model import WEEK_DAYS, LANGUAGES, THEME_STYLES, Schedule, Homework
from kivy.core.window import Window
from kivy.lang import Observable
from os.path import join, dirname, realpath
import gettext
from Settings import Settings
from kivymd.color_definitions import colors
from kivymd.uix.selectioncontrol import MDCheckbox
from plyer import notification
from plyer.utils import platform
# from kivy.clock import Clock
# from functools import partial
from osc.osc_app_server import OscAppServer
from service.utils import start_service
from kivymd.uix.bottomsheet import MDGridBottomSheet
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.picker import MDDatePicker
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button

from Util import Util


from kivy.core.text import LabelBase
KIVY_FONTS = [
    {
        "name": "Jura",
        "fn_regular": "fonts/Jura/static/Jura-Medium.ttf",
        "fn_bold": "fonts/Jura/static/Jura-Bold.ttf",
        # "fn_italic": "fonts/Kumbh/Lekton-Italic.ttf",
        # "fn_bolditalic": "fonts/Lekton/Android Italic 400.ttf"
    }
]



class DayTab(BoxLayout, MDTabsBase):
    pass


class LessonsContainer(GridLayout):
    pass


class NotifyTimepicker(MDTimePicker):
    pass


class LessonTimepicker(MDTimePicker):
    lesson_id = ObjectProperty()
    time_mode = ObjectProperty()


class SelectScheduleButton(Button):
    default_text = StringProperty()
    not_found_text = StringProperty()

class SelectLessonButton(Button):
    default_text = StringProperty()
    not_found_text = StringProperty()


class ConfirmDeleteScheduleDialog(MDDialog):
    schedule_id = StringProperty()


class ConfirmDeleteLessonDialog(MDDialog):
    lesson_id = StringProperty()


class ScheduleGridBottomSheet(MDGridBottomSheet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sheet_list.ids.box_sheet_list.padding = (dp(16), 0, dp(16), dp(16))


class Lang(Observable):
    observers = []
    lang = None

    def __init__(self, defaultlang):
        super(Lang, self).__init__()
        self.ugettext = None
        self.lang = defaultlang
        self.switch_lang(self.lang)

    def _(self, text):
        return self.ugettext(text)

    def fbind(self, name, func, args, **kwargs):
        if name == "_":
            self.observers.append((func, args, kwargs))
        else:
            return super(Lang, self).fbind(name, func, *args, **kwargs)

    def funbind(self, name, func, args, **kwargs):
        if name == "_":
            key = (func, args, kwargs)
            if key in self.observers:
                self.observers.remove(key)
        else:
            return super(Lang, self).funbind(name, func, *args, **kwargs)

    def switch_lang(self, lang):
        # get the right locales directory, and instanciate a gettext
        user_dir = dirname(__file__)
        locale_dir = join(user_dir, 'data', 'locales')
        locales = gettext.translation('mainapp', locale_dir, languages=[lang])
        self.ugettext = locales.gettext

        # update all the kv rules attached to this text
        for func, largs, kwargs in self.observers:
            func(largs, None, None)


class MainApp(MDApp):

    _interval = NumericProperty()
    my_snackbar = ObjectProperty(None, allownone=True)
    lang = StringProperty()

    def __init__(self, **kwargs):
        self.Settings = None
        self.Schedule = None
        self.Homework = None
        self.current_schedule_id = None
        self.current_week_num = None
        self.current_year = None
        self.previous_screen= None
        self.cfg = config
        self.init_lang_chip_color = True
        self.init_theme_chip_color = True
        self.sch_dropdown = None
        self.schedule_select_btn = None
        self.lesson_dropdown = None
        self.lesson_select_btn = None
        super(MainApp, self).__init__(**kwargs)
        print("User data dir: %s" % self.user_data_dir)
        Window.bind(on_keyboard=self.on_key)

    def build(self):
        super(MainApp, self).build()

        self.Schedule = Schedule(table='schedules')
        self.Homework = Homework(table='homeworks')
        self.Settings = Settings()

        self.init_add_homework_controls()

        self.set_theme()
        self.set_fonts()

        self.create_demo_schedules()

        self.start_services()

        return self.root

    @staticmethod
    def start_services():
        """
        Starts both schedules service and OSC service.
        The schedules service is getting the OSC server connection
        parameters so it can communicate to it.
        """
        app = MDApp.get_running_app()
        osc_server, sockname = OscAppServer.get_or_create(app)
        server_address, server_port = sockname
        print(sockname)
        arguments = {
            'osc_server_address': server_address,
            'osc_server_port': server_port,
        }
        start_service(arguments)

    def on_lang(self, instance, lang):
        tr.switch_lang(lang)

    def get_config_item(self, key):
        return self.cfg[key]

    def on_start(self):
        self.load_start_screen()

    def on_pause(self):
        return True

    def on_key(self, window, key, *args):
        if key == 27:
            if self.root.current == 'start':
                return True
            elif self.root.current in ['add_schedule', 'add_homework', 'schedule', 'settings']:
                self.back_to_main()
                return True
            elif self.root.current in ['add_lesson']:
                self.switch_screen('schedule')
                return True
            elif self.root.current == 'add_lesson_homework':
                if self.previous_screen is not None:
                    self.switch_screen(self.previous_screen)
                else:
                    self.switch_screen('schedule')
                return True

    def change_lang(self, chip, lang_name):
        if lang_name in LANGUAGES['en']:
            self.lang = 'en'
        elif lang_name in LANGUAGES['ru']:
            self.lang = 'ru'
        self.Settings.save('user', lang=self.lang)
        self.init_settings_lang_chip()

    def change_theme(self, chip, theme):
        theme = theme.lower()
        self.set_theme(theme)
        self.Settings.save('theme', style=theme)
        self.init_settings_theme_chip()
        self.init_settings_lang_chip()

    def switch_screen(self, screen, previous_screen=None):
        self.root.current = screen
        self.previous_screen = previous_screen

    def create_demo_schedules(self):
        self.Schedule.clear()
        self.Homework.clear()

        schedule_key = str(uuid.uuid4())
        self.Schedule.save(schedule_key, name='School schedule',
                       lessons=[
                           {'id': str(uuid.uuid4()), 'name': 'Math', 'day': 0, 'time_start': '07:00', 'time_end': '07:30'},
                           {'id': str(uuid.uuid4()), 'name': 'Literature', 'day': 0, 'time_start': '08:30', 'time_end': '09:00'},
                           {'id': str(uuid.uuid4()), 'name': 'Geography', 'day': 0, 'time_start': '', 'time_end': ''},
                           {'id': str(uuid.uuid4()), 'name': 'Literature', 'day': 0, 'time_start': '', 'time_end': ''},
                           {'id': str(uuid.uuid4()), 'name': 'Reading', 'day': 0, 'time_start': '07:45', 'time_end': '08:15'},
                           {'id': str(uuid.uuid4()), 'name': 'Physics', 'day': 1, 'time_start': '07:00', 'time_end': '07:30'},
                           {'id': str(uuid.uuid4()), 'name': 'Music', 'day': 1, 'time_start': '07:45', 'time_end': '08:15'},
                           {'id': str(uuid.uuid4()), 'name': 'History', 'day': 1, 'time_start': '08:30', 'time_end': '09:00'},
                           {'id': str(uuid.uuid4()), 'name': 'Writing', 'day': 2, 'time_start': '07:00', 'time_end': '07:30'},
                           {'id': str(uuid.uuid4()), 'name': 'Math', 'day': 2, 'time_start': '07:45', 'time_end': '08:15'},
                           {'id': str(uuid.uuid4()), 'name': 'Math', 'day': 4, 'time_start': '07:00', 'time_end': '07:30'},
                           {'id': str(uuid.uuid4()), 'name': 'English', 'day': 4, 'time_start': '07:45', 'time_end': '08:15'},
                           {'id': str(uuid.uuid4()), 'name': 'Nature', 'day': 4, 'time_start': '08:30', 'time_end': '09:00'},
                           {'id': str(uuid.uuid4()), 'name': 'Music', 'day': 5, 'time_start': '07:00', 'time_end': '07:30'},
                       ])

        schedule_key = str(uuid.uuid4())
        self.Schedule.save(schedule_key, name='Art school schedule',
                       lessons=[
                           {'id': str(uuid.uuid4()), 'name': 'Painting', 'day': 0, 'time_start': '07:00', 'time_end': '07:30'},
                           {'id': str(uuid.uuid4()), 'name': 'Art History', 'day': 0, 'time_start': '07:45', 'time_end': '08:15'},
                           {'id': str(uuid.uuid4()), 'name': 'Graphics', 'day': 1, 'time_start': '07:00', 'time_end': '07:30'}
                       ])

    def load_start_screen(self):
        start_tab_panel = self.root.ids.start_tabs
        start_tab_panel.background_color = self.get_tabs_color()

        self.load_schedules()
        self.load_homeworks()

    def on_screen_pre_enter(self, screen):
        if screen.name == 'start':
            self.root.ids.start_tabs.background_color = self.get_tabs_color()

    def load_schedules(self):
        schedule_list = self.root.ids.schedule_list
        Util.clear_list_items(schedule_list)
        schedules = self.Schedule.all()
        for schedule_id in schedules:
            schedule = self.Schedule.get(schedule_id)
            schedule_item = OneLineListItem(
                id=schedule_id,
                text=schedule['name'],
                divider='Inset',
                on_release=self.show_schedule_item_options)
            schedule_list.add_widget(schedule_item)

    def load_homeworks(self):
        homework_list = self.root.ids.homework_list
        Util.clear_list_items(homework_list)
        homeworks = self.Homework.all()
        schedules = self.Schedule.all()

        week_now = Util.calc_week_num()
        year_now = Util.calc_year()
        day_now = Util.calc_day_num()

        hws = []
        for homework_id in homeworks:
            homework = self.Homework.get(homework_id)
            if homework['year'] < year_now or homework['week_num'] < week_now:
                continue
            for schedule_id in schedules:
                lesson = self.get_lesson(schedule_id, homework['lesson_id'])
                if lesson is not None:
                    if homework['week_num'] == week_now and lesson['day'] < day_now:
                        continue
                    schedule = self.Schedule.get(schedule_id)
                    hw = {
                        'description': homework['desc'],
                        'week_num': homework['week_num'],
                        'year': homework['year'],
                        'notified': homework['notified'],
                        'homework_id': homework_id,
                        'schedule_id': schedule_id,
                        'schedule_name': schedule['name'],
                        'day': lesson['day'],
                        'lesson_name': lesson['name'],
                        'lesson_time_start': lesson['time_start'],
                        'homework_date': Util.get_date(homework['year'], homework['week_num'], lesson['day'])
                    }

                    hws.append(hw)

        hws = self.sort_homeworks(hws)
        for home_work in hws:
            homework_item = ThreeLineListItem(
                id=home_work['homework_id'],
                text=f'{home_work["lesson_name"]} ({home_work["schedule_name"]}) {home_work["lesson_time_start"]}',
                font_style='Body1',
                secondary_text=home_work['homework_date'].strftime("%a %d %b, %Y"),
                secondary_theme_text_color='Custom',
                secondary_text_color=get_color_from_hex(colors[self.theme_cls.primary_palette]['800']),
                secondary_font_style='Subtitle1',
                tertiary_text=home_work['description'],
                tertiary_font_style='Subtitle2',
                divider='Inset',
                on_release=self.show_homework_item_options)
            homework_list.add_widget(homework_item)

    def callback_for_schedule_menu_items(self, **kwargs):
        action = kwargs['action']
        schedule_id = kwargs['schedule_id']
        if action == 'open':
            day = Util.calc_day_num()
            week_num = Util.calc_week_num()
            year = Util.calc_year()
            self.open_schedule(schedule_id, day, week_num, year)
        elif action == 'edit':
            self.add_schedule(schedule_id)
        elif action == 'delete':
            if self.schedule_has_future_homeworks(schedule_id):
                self.show_confirm_del_schedule_dialog(schedule_id)
            else:
                self.delete_schedule(schedule_id)

    def callback_for_homework_menu_items(self, **kwargs):
        action = kwargs['action']
        homework_id = kwargs['homework_id']
        if action == 'edit':
            homework = self.Homework.get(homework_id)
            schedule = None
            schedules = self.Schedule.all()
            for schedule_id in schedules:
                toast('check')


            toast('todo: edit homework')
        elif action == 'delete':
            toast('todo: delete homework')

    def schedule_has_future_homeworks(self, schedule_id):
        has_homeworks = False
        schedule = self.get_schedule(schedule_id)
        lessons = schedule['lessons']
        homeworks = self.Homework.all()
        year_now = Util.calc_year()
        week_now = Util.calc_week_num()
        for lesson in lessons:
            future_homeworks = list(x for x in list(homeworks.find(lesson_id=lesson['id'])) if x[1]['year'] >= year_now and x[1]['week_num'] >= week_now)
            if len(future_homeworks) > 0:
                has_homeworks = True
                break
        return has_homeworks

    def lesson_has_future_homeworks(self, lesson_id):
        schedule_id = self.get_active_schedule_id()
        lesson = self.get_lesson(schedule_id, lesson_id)
        homeworks = self.Homework.all()
        year_now = Util.calc_year()
        week_now = Util.calc_week_num()
        future_homeworks = list(x for x in list(homeworks.find(lesson_id=lesson['id'])) if x[1]['year'] >= year_now and x[1]['week_num'] >= week_now)
        return len(future_homeworks) > 0

    def show_schedule_item_options(self, instance):
        schedule_menu = ScheduleGridBottomSheet()
        schedule_menu.add_item(
            tr._('Open'),
            lambda x: self.callback_for_schedule_menu_items(
                schedule_id=instance.id,
                action='open'
            ),
            icon_src='open-in-app',
        )
        schedule_menu.add_item(
            tr._('Edit'),
            lambda x: self.callback_for_schedule_menu_items(
                schedule_id=instance.id,
                action='edit'
            ),
            icon_src='pencil',
        )
        schedule_menu.add_item(
            tr._('Delete'),
            lambda x: self.callback_for_schedule_menu_items(
                schedule_id=instance.id,
                action='delete'
            ),
            icon_src='delete',
        )
        schedule_menu.open()

    def show_homework_item_options(self, instance):
        homework_menu = ScheduleGridBottomSheet()
        homework_menu.add_item(
            tr._('Edit'),
            lambda x: self.callback_for_homework_menu_items(
                homework_id=instance.id,
                action='edit'
            ),
            icon_src='pencil',
        )
        homework_menu.add_item(
            tr._('Delete'),
            lambda x: self.callback_for_homework_menu_items(
                homework_id=instance.id,
                action='delete'
            ),
            icon_src='delete',
        )
        homework_menu.open()

    def open_schedule(self, schedule_id, day_index=0, week_num=None, year=None):
        if week_num is None:
            week_num = Util.calc_week_num(0)
        if year is None:
            year = Util.calc_year(0)
        self.set_active_schedule_id(schedule_id)
        self.set_active_week_num(week_num)
        self.set_active_year(year)

        schedule_tab_panel = self.root.ids.schedule_tabs
        schedule_tab_panel.background_color = self.get_tabs_color()

        schedule = self.get_schedule(schedule_id)
        schedule_lessons = schedule['lessons']

        for i in range(len(WEEK_DAYS)):
            day_lessons = list(filter(lambda d: d['day'] == i, schedule_lessons))
            day_lessons = self.sort_lessons(day_lessons)
            tab_list = schedule_tab_panel.get_tab_list()
            tab = tab_list[(len(tab_list) - 1) - i]
            tab.text = WEEK_DAYS[i]
            lesson_list = self.root.ids[f'lesson_list_day_{i}']
            Util.clear_list_items(lesson_list)

            for lesson in day_lessons:
                time_start = lesson['time_start'] if lesson['time_start'] != '' else '..'
                time_end = lesson['time_end'] if lesson['time_end'] != '' else '..'
                second_text = f'{time_start} - {time_end}'

                homework = self.get_homework(lesson['id'], week_num, year)
                if homework is None:
                    hw_desc = None
                elif homework is False:
                    hw_desc = None
                    toast(f'warning: duplicated homeworks found. lesson_id: {lesson["id"]}, week_num: {week_num}, year: {year}')
                else:
                    hw_desc = homework[1]['desc']
                if hw_desc is not None:
                    lesson_item = ThreeLineListItem(
                        tertiary_text=hw_desc,
                        on_release=self.show_lesson_item_options)
                else:
                    lesson_item = TwoLineListItem(
                        on_release=self.show_lesson_item_options)
                lesson_item.id = lesson['id']
                lesson_item.text = lesson['name']
                lesson_item.secondary_text = second_text

                lesson_list.add_widget(lesson_item)

        schedule_tab_panel.ids.carousel.index = day_index

        date_range = self.get_week_date_range(week_num=week_num, year=year)
        self.root.ids.schedule_toolbar.title = f'{schedule["name"]} [{Util.get_date_str(year, week_num, day_index)}]'
        self.root.ids.bottom_schedule_toolbar.title = date_range
        self.switch_screen('schedule')

    def callback_for_lesson_menu_items(self, **kwargs):
        action = kwargs['action']
        lesson_id = kwargs['lesson_id']
        if action == 'edit':
            self.add_lesson(lesson_id)
        elif action == 'delete':
            if self.lesson_has_future_homeworks(lesson_id):
                self.show_confirm_del_lesson_dialog(lesson_id)
            else:
                self.delete_lesson(lesson_id)
        elif action == 'add_homework':
            self.add_lesson_homework(lesson_id)
        elif action == 'clear_homework':
            self.clear_homework(lesson_id)
        elif action == 'set_start_time':
            self.set_lesson_time(lesson_id, 'time_start')
        elif action == 'set_end_time':
            self.set_lesson_time(lesson_id, 'time_end')
        else:
            toast(f'Action {action} Not implemented')

    def show_lesson_item_options(self, instance):
        lesson_menu = ScheduleGridBottomSheet()
        week_num = self.get_active_week_num()
        year = self.get_active_year()
        homework_exists = False
        homework = self.get_homework(instance.id, week_num, year)
        if homework is None:
            hw_action_name = 'Add'
        elif homework is False:
            toast(f'warning: duplicated homeworks found. lesson_id: {instance.id}, week_num: {week_num}, year: {year}')
            hw_action_name = 'Add'
        else:
            hw_action_name = 'Edit'
            homework_exists = True

        lesson_menu.add_item(
            f'{hw_action_name} Homework',
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='add_homework'
            ),
            icon_src='home-plus',
        )
        if homework_exists:
            lesson_menu.add_item(
                'Clear Homework',
                lambda x: self.callback_for_lesson_menu_items(
                    lesson_id=instance.id,
                    action='clear_homework'
                ),
                icon_src='home-minus',
            )

        lesson_menu.add_item(
            'Edit',
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='edit'
            ),
            icon_src='pencil',
        )

        lesson_menu.add_item(
            'Delete',
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='delete'
            ),
            icon_src='delete',
        )
        lesson_menu.add_item(
            'Set Time Start',
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='set_start_time'
            ),
            icon_src='clock-in',
        )
        lesson_menu.add_item(
            'Set Time End',
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='set_end_time'
            ),
            icon_src='clock-out',
        )
        lesson_menu.open()

    def schedule_bottom_bar_exists(self):
        exists = False
        for child in self.root.ids.schedule_screen_layout.children:
            if type(child).__name__ == 'MDBottomAppBar':
                exists = True
        return exists

    @staticmethod
    def sort_lessons(lessons):
        return sorted(lessons, key=lambda i: datetime.datetime.strptime((i['time_start'] if i['time_start'] != '' else '23:59'), '%H:%M'))

    @staticmethod
    def sort_homeworks(homeworks):
        return sorted(homeworks, key=lambda i: (i['homework_date'], datetime.datetime.strptime((i['lesson_time_start'] if i['lesson_time_start'] != '' else '23:59'), '%H:%M')))

    def back_to_main(self, tab_index = 0):
        self.reset_active_schedule_id()
        self.reset_active_week_num()
        self.reset_active_year()
        self.root.ids.start_tabs.ids.carousel.index = tab_index
        self.switch_screen('start')

    def get_active_week_num(self):
        return self.current_week_num

    def set_active_week_num(self, week_num):
        self.current_week_num = week_num

    def reset_active_week_num(self):
        self.current_week_num = None

    def get_active_year(self):
        return self.current_year

    def set_active_year(self, year):
        self.current_year = year

    def reset_active_year(self):
        self.current_year = None

    def get_active_schedule_id(self):
        return self.current_schedule_id

    def set_active_schedule_id(self, schedule_id):
        self.current_schedule_id = schedule_id

    def reset_active_schedule_id(self):
        self.current_schedule_id = None

    def get_schedule(self, schedule_id):
        return self.Schedule.get(schedule_id)

    def save_schedule(self, **kwargs):
        title_field = self.root.ids.add_schedule_title
        schedule_id = kwargs['schedule_id']
        title = kwargs['title']
        is_new = schedule_id is None

        title_limit = self.get_config_item('schedule_title_max_len')
        title = title[:title_limit]

        if title.strip() == '':
            title_field.text = ''
            self.show_error(text='Title cannot be empty!')
        else:
            if not is_new:
                schedule = self.get_schedule(schedule_id)
                lessons = schedule['lessons']
            else:
                schedule_id = str(uuid.uuid4())
                lessons = []

            self.Schedule.save(schedule_id, name=title, lessons=lessons)
            self.load_schedules()
            self.back_to_main()
            toast(f'Schedule {"added" if is_new else "updated"}')

    def save_lesson(self, **kwargs):
        title_field = self.root.ids.add_lesson_title
        lesson_id = kwargs['lesson_id']
        schedule_id = kwargs['schedule_id']
        day = kwargs['day']
        title = kwargs['title']
        del_homeworks = kwargs['del_homeworks']
        week_num = self.get_active_week_num()
        year = self.get_active_year()
        is_new = lesson_id is None

        title_limit = self.get_config_item('lesson_title_max_len')
        title = title[:title_limit]

        if title.strip() == '':
            title_field.text = ''
            self.show_error(text='Title cannot be empty!')
        else:
            schedule = self.get_schedule(schedule_id)
            lessons = schedule['lessons']
            if not is_new:
                for lesson in lessons:
                    if lesson['id'] == lesson_id:
                        lesson['name'] = title
                        break
            else:
                lessons.append({'id': str(uuid.uuid4()), 'name': title, 'day': day, 'time_start': '', 'time_end': ''})
            self.Schedule.save(schedule_id, name=schedule['name'], lessons=lessons)

            if not is_new and del_homeworks:
                self.delete_homeworks(lesson_id=lesson_id)

            self.open_schedule(schedule_id, day, week_num, year)
            toast(f'Lesson {"added" if is_new else "updated"}')

    def show_confirm_del_schedule_dialog(self, schedule_id):
        schedule = self.get_schedule(schedule_id)
        dialog = ConfirmDeleteScheduleDialog(
            title=f'Delete {schedule["name"]}?',
            size_hint=(0.8, 0.4),
            text_button_ok='Confirm',
            text=f'There are homeworks assigned to lessons for future dates within schedule.\nDelete anyway?',
            text_button_cancel="Cancel",
            events_callback=self.callback_confirm_del_schedule,
            schedule_id=schedule_id
        )
        dialog.open()

    def show_confirm_del_lesson_dialog(self, lesson_id):
        schedule_id = self.get_active_schedule_id()
        lesson = self.get_lesson(schedule_id, lesson_id)
        dialog = ConfirmDeleteLessonDialog(
            title=f'Delete {lesson["name"]}?',
            size_hint=(0.8, 0.4),
            text_button_ok='Confirm',
            text=f'There are homeworks assigned to the lesson for future dates.\nDelete anyway?',
            text_button_cancel="Cancel",
            events_callback=self.callback_confirm_del_lesson,
            lesson_id=lesson_id
        )
        dialog.open()

    def callback_confirm_del_schedule(self, *args):
        schedule_id = args[1].schedule_id
        if args[0] == 'Confirm':
            self.delete_schedule(schedule_id)

    def callback_confirm_del_lesson(self, *args):
        lesson_id = args[1].lesson_id
        if args[0] == 'Confirm':
            self.delete_lesson(lesson_id)

    def delete_schedule(self, schedule_id):
        self.delete_homeworks(schedule_id=schedule_id)
        self.Schedule.delete(schedule_id)
        self.load_schedules()
        toast('Schedule deleted')

    def delete_homeworks(self, **kwargs):
        homeworks = self.Homework.all()
        del_homeworks = []
        if 'schedule_id' in kwargs:
            schedule_id = kwargs['schedule_id']
            schedule = self.get_schedule(schedule_id)
            lessons = schedule['lessons']
            for lesson in lessons:
                lesson_homeworks = list(x for x in list(homeworks.find(lesson_id=lesson['id'])))
                if len(lesson_homeworks) > 0:
                    del_homeworks += lesson_homeworks
        elif 'lesson_id' in kwargs:
            lesson_id = kwargs['lesson_id']
            lesson_homeworks = list(x for x in list(homeworks.find(lesson_id=lesson_id)))
            if len(lesson_homeworks) > 0:
                del_homeworks += lesson_homeworks
        for hw in del_homeworks:
            self.Homework.delete(hw[0])

    def get_lesson(self, schedule_id, lesson_id):
        schedule = self.Schedule.get(schedule_id)
        return next((item for item in schedule['lessons'] if item['id'] == lesson_id), None)

    def delete_lesson(self, lesson_id):
        self.delete_homeworks(lesson_id=lesson_id)

        schedule_id = self.get_active_schedule_id()
        day = self.get_current_tab_index('schedule')
        week_num = self.get_active_week_num()
        year = self.get_active_year()
        schedule = self.get_schedule(schedule_id)
        lessons = schedule['lessons']
        day_lessons = list(filter(lambda d: d['day'] == day, lessons))
        day_lessons = self.sort_lessons(day_lessons)
        current_lesson_index = next((index for (index, d) in enumerate(day_lessons) if d['id'] == lesson_id), None)
        del day_lessons[current_lesson_index]

        del_lesson_index = next((index for (index, d) in enumerate(lessons) if d['id'] == lesson_id), None)
        del lessons[del_lesson_index]

        self.open_schedule(schedule_id, day, week_num, year)
        toast('Lesson deleted')

    def on_start_add_button_release(self):
        tab_index = self.get_current_tab_index('start')
        if tab_index == 0:
            self.add_schedule()
        elif tab_index == 1:
            self.add_homework()

    def add_schedule(self, schedule_id=None):
        title_field = self.root.ids.add_schedule_title
        top_toolbar = self.root.ids.add_schedule_top_toolbar

        schedule = self.get_schedule(schedule_id) if schedule_id is not None else None

        title_field.text = '' if not schedule else schedule['name']
        # hack to fix validation on open
        title_field.focus = True
        title_field.focus = False

        top_toolbar.left_action_items = [['arrow-left', lambda x: self.back_to_main()]]
        top_toolbar.right_action_items = [['check', lambda x: self.save_schedule(schedule_id=schedule_id, title=title_field.text)]]
        top_toolbar.title = f'{"Edit" if schedule is not None else "Add"} Schedule'
        self.switch_screen('add_schedule')

    def init_add_homework_controls(self):
        self.sch_dropdown = DropDown()
        self.schedule_select_btn = self.root.ids.schedule_select_btn
        self.schedule_select_btn.bind(on_release=self.sch_dropdown.open)
        self.sch_dropdown.bind(on_select=self.set_schedules_dropdown_item)

        self.lesson_dropdown = DropDown()
        self.lesson_select_btn = self.root.ids.lesson_select_btn
        self.lesson_select_btn.bind(on_release=self.lesson_dropdown.open)
        self.lesson_dropdown.bind(on_select=self.set_lessons_dropdown_item)

    def add_homework(self):
        top_toolbar = self.root.ids.add_homework_top_toolbar
        hw_date = self.root.ids.add_homework_date
        today = datetime.datetime.today().date()
        hw_date.text = str(today)
        hw_date.font_style = 'Subtitle1'
        hw_date.padding = [5, 0]

        self.load_schedules_dropdown_items(today)

        top_toolbar.left_action_items = [['arrow-left', lambda x: self.back_to_main(1)]]
        top_toolbar.right_action_items = [['arrow-right', lambda x: self.open_add_homework()]]
        self.switch_screen('add_homework')

    def open_add_homework(self):
        str_date = self.root.ids.add_homework_date.text
        date = datetime.datetime.strptime(str_date, '%Y-%m-%d').date()
        schedule_name = self.schedule_select_btn.text
        lesson_name = self.lesson_select_btn.text
        if schedule_name in [self.schedule_select_btn.default_text, self.schedule_select_btn.not_found_text] or lesson_name in [self.lesson_select_btn.default_text, self.lesson_select_btn.not_found_text]:
            toast('Please select Schedule and Lesson')
        else:
            week_num = int(date.strftime("%W"))
            year = date.year
            day = date.weekday()
            schedules = self.Schedule.all()
            schedules_found = list(schedules.find(name=schedule_name))
            if len(schedules_found) == 0:
                toast(f'Cannot find the schedule item: "{schedule_name}"')
                return
            schedule_id = schedules_found[0][0]
            schedule = schedules_found[0][1]
            lessons = list(filter(lambda d: d['day'] == day and d['name'] == lesson_name, schedule['lessons']))
            lesson_id = lessons[0]['id']

            self.add_lesson_homework(lesson_id, schedule_id, week_num, year)

    def set_schedules_dropdown_item(self, dropdown_instance, dropdown_item_text):
        self.schedule_select_btn.text = dropdown_item_text
        toast(f'{dropdown_item_text} selected')
        str_date = self.root.ids.add_homework_date.text
        date = datetime.datetime.strptime(str_date, '%Y-%m-%d').date()
        self.load_lessons_dropdown_items(date, dropdown_item_text)


    def set_lessons_dropdown_item(self, dropdown_instance, dropdown_item_text):
        self.lesson_select_btn.text = dropdown_item_text
        toast(f'{dropdown_item_text} selected')

    def open_add_homework_datepicker(self):
        str_date = self.root.ids.add_homework_date.text
        date = datetime.datetime.strptime(str_date, '%Y-%m-%d').date()
        min_date = date - datetime.timedelta(days=1)
        date_dialog = MDDatePicker(
            callback=self.get_homework_datepicker_date,
            year=date.year,
            month=date.month,
            day=date.day,
            min_date=min_date
        )
        date_dialog.open()

    def get_homework_datepicker_date(self, date):
        self.root.ids.add_homework_date.text = str(date)
        self.load_schedules_dropdown_items(date)

    def load_schedules_dropdown_items(self, date):
        self.sch_dropdown.clear_widgets()
        weekday = date.weekday()
        schedules = self.Schedule.all()
        for schedule_id in schedules:
            schedule = self.get_schedule(schedule_id)
            day_lessons = list(filter(lambda d: d['day'] == weekday, schedule['lessons']))
            if len(day_lessons):
                dropdown_button = Button(
                    text=schedule['name'],
                    size_hint_y=None,
                    height=40,
                    background_color=self.get_theme_color(self.theme_cls.primary_palette, '700'),
                    background_normal='',
                    font_size=16
                )
                dropdown_button.bind(on_release=lambda dropdown_button: self.sch_dropdown.select(dropdown_button.text))
                self.sch_dropdown.add_widget(dropdown_button)

        schedules_exist = len(self.sch_dropdown.container.children) > 0
        self.reset_schedules_select_button(schedules_exist)

        self.lesson_dropdown.clear_widgets()
        self.reset_lessons_select_button(schedules_exist)

    def load_lessons_dropdown_items(self, date, schedule_name):
        self.lesson_dropdown.clear_widgets()
        day = date.weekday()
        schedules = self.Schedule.all()
        schedules_found = list(schedules.find(name=schedule_name))
        if len(schedules_found) == 0:
            toast(f'Cannot find the schedule item: "{schedule_name}"')
            return
        schedule = schedules_found[0][1]
        lessons = list(filter(lambda d: d['day'] == day, schedule['lessons']))
        if len(lessons):
            lessons = self.sort_lessons(lessons)
            for lesson in lessons:
                dropdown_button = Button(
                    text=lesson['name'],
                    size_hint_y=None,
                    height=40,
                    background_color=self.get_theme_color(self.theme_cls.primary_palette, 'A400'),
                    background_normal='',
                    font_size=16
                )
                dropdown_button.bind(on_release=lambda dropdown_button: self.lesson_dropdown.select(dropdown_button.text))
                self.lesson_dropdown.add_widget(dropdown_button)

        lessons_exist = len(lessons) > 0
        self.reset_lessons_select_button(lessons_exist)

    def reset_schedules_select_button(self, is_active):
        self.schedule_select_btn.text = self.schedule_select_btn.default_text if is_active else self.schedule_select_btn.not_found_text
        self.schedule_select_btn.disabled = is_active is False
        self.schedule_select_btn.background_color = self.get_theme_color(self.theme_cls.primary_palette, '600') if is_active else self.get_theme_color(self.theme_cls.primary_palette, '400')

    def reset_lessons_select_button(self, is_active):
        self.lesson_select_btn.text = self.lesson_select_btn.default_text if is_active else self.lesson_select_btn.not_found_text
        self.lesson_select_btn.disabled = is_active is False
        self.lesson_select_btn.background_color = self.get_theme_color(self.theme_cls.primary_palette, 'A700') if is_active else self.get_theme_color(self.theme_cls.primary_palette, '400')

    def add_lesson(self, lesson_id=None):
        title_field = self.root.ids.add_lesson_title
        top_toolbar = self.root.ids.add_lesson_top_toolbar
        grid_layout = self.root.ids.add_lesson_grid_layout

        day = self.get_current_tab_index('schedule')
        schedule_id = self.get_active_schedule_id()
        lesson = self.get_lesson(schedule_id, lesson_id) if lesson_id is not None else None

        title_field.text = '' if not lesson else lesson['name']
        # hack to fix validation on open
        title_field.focus = True
        title_field.focus = False

        for child in grid_layout.children:
            if type(child).__name__ == 'BoxLayout'and child.id == 'add_lesson_del_homeworks_layout':
                grid_layout.remove_widget(child)

        del_chkbx = None
        if lesson is not None:
            del_homeworks_wrapper = BoxLayout(id='add_lesson_del_homeworks_layout')
            del_chkbx = MDCheckbox(
                id='add_lesson_del_homework_checkbox',
                size_hint=[None, None],
                size=['48dp', '48dp'],
                pos_hint={'center_x': .5, 'center_y': .5},
                selected_color=self.theme_cls.text_color,
                color=self.theme_cls.text_color,
                unselected_color=self.theme_cls.text_color
            )
            del_chkbx_lbl = MDLabel(
                text='delete all related homeworks',
                color=self.theme_cls.text_color
            )
            del_homeworks_wrapper.add_widget(del_chkbx)
            del_homeworks_wrapper.add_widget(del_chkbx_lbl)
            grid_layout.add_widget(del_homeworks_wrapper)

        top_toolbar.left_action_items = [['arrow-left', lambda x: self.switch_screen('schedule')]]
        top_toolbar.right_action_items = [['check', lambda x: self.save_lesson(schedule_id=schedule_id, lesson_id=lesson_id, day=day, title=title_field.text, del_homeworks=(del_chkbx.state == 'down' if del_chkbx is not None else False))]]
        top_toolbar.title = f'{"Edit" if lesson is not None else "Add"} Lesson for {WEEK_DAYS[day]}'
        self.switch_screen('add_lesson')

    def get_current_tab_index(self, tabs_name):
        tab_panel = None
        tab_index = 0
        if tabs_name == 'schedule':
            tab_panel = self.root.ids.schedule_tabs
        elif tabs_name == 'start':
            tab_panel = self.root.ids.start_tabs

        if tab_panel is None:
            toast('Unable to get tab index: incorrect tabs_name')
        else:
            tab_index = tab_panel.ids.carousel.index
        return tab_index

    @staticmethod
    def show_error(**kwargs):
        Snackbar(text=kwargs['text']).open()

    def set_lesson_time(self, lesson_id, mode):
        schedule_id = self.get_active_schedule_id()
        time_dialog = LessonTimepicker(lesson_id=lesson_id, time_mode=mode)
        time_dialog.bind(time=self.save_lesson_time)

        lesson_time = ''
        schedule = self.get_schedule(schedule_id)
        lessons = schedule['lessons']
        for lesson in lessons:
            if lesson['id'] == lesson_id:
                lesson_time = lesson[mode]
                break

        if lesson_time != '':
            time = datetime.datetime.strptime(lesson_time, '%H:%M').time()
            try:
                time_dialog.set_time(time)
            except AttributeError:
                pass
        time_dialog.open()

    def save_lesson_time(self, instance, time):
        schedule_id = self.get_active_schedule_id()
        lesson_id = instance.lesson_id
        mode = instance.time_mode
        time_str = time.strftime('%H:%M') if type(time) is datetime.time else time
        day = 0
        week_num = self.get_active_week_num()
        year = self.get_active_year()

        schedule = self.get_schedule(schedule_id)
        lessons = schedule['lessons']
        for lesson in lessons:
            if lesson['id'] == lesson_id:
                lesson[mode] = time_str

                if mode == 'time_start':
                    if lesson['time_end'] == '':
                        lesson['time_end'] = time_str
                    else:
                        if datetime.datetime.strptime(time_str, '%H:%M') > datetime.datetime.strptime(lesson['time_end'], '%H:%M'):
                            lesson['time_end'] = time_str
                elif mode == 'time_end':
                    if lesson['time_start'] == '':
                        lesson['time_start'] = time_str
                    else:
                        if datetime.datetime.strptime(time_str, '%H:%M') < datetime.datetime.strptime(lesson['time_start'], '%H:%M'):
                            lesson['time_end'] = lesson['time_start']

                day = lesson['day']
                break

        self.Schedule.save(schedule_id, name=schedule['name'], lessons=lessons)
        self.open_schedule(schedule_id, day, week_num, year)

    def set_notify_time_setting(self, current):
        time_dialog = NotifyTimepicker()
        time_dialog.bind(time=self.get_notify_timepicker_time)

        time = datetime.datetime.strptime(current, '%H:%M').time()
        try:
            time_dialog.set_time(time)
        except AttributeError:
            pass
        time_dialog.open()

    def get_notify_timepicker_time(self, instance, time):
        self.update_notify_time_setting(time)

    def update_notify_time_setting(self, time):
        time_str = time.strftime('%H:%M') if type(time) is datetime.time else time
        self.Settings.save('notify', homework=time_str)
        self.refresh_settings_notify_homework()

    def add_lesson_homework(self, lesson_id, schedule_id=None, week_num=None, year=None):
        add_mode = 'schedule' if schedule_id is None and week_num is None and year is None else 'homeworks'

        previous_screen = 'add_homework' if add_mode == 'homeworks' else None

        if schedule_id is None:
            schedule_id = self.get_active_schedule_id()
        lesson = self.get_lesson(schedule_id, lesson_id)
        desc_field = self.root.ids.add_lesson_homework_desc_text
        top_toolbar = self.root.ids.add_lesson_homework_top_toolbar
        subtitle = self.root.ids.add_lesson_homework_subtitle

        if week_num is None:
            week_num = self.get_active_week_num()
        if year is None:
            year = self.get_active_year()
        homework = self.get_homework(lesson_id, week_num, year)
        if homework is None:
            desc = ''
        elif homework is False:
            toast(f'warning: duplicated homeworks found. lesson_id: {lesson_id}, week_num: {week_num}, year: {year}')
            desc = ''
        else:
            desc = homework[1]['desc']

        desc_field.text = desc

        # hack to fix validation on open
        desc_field.focus = True
        desc_field.focus = False

        homework_id = None if not homework else homework[0]

        day = lesson['day']
        subtitle.text = f'{lesson["name"]} for {Util.get_date_str(year, week_num, day)}'

        top_toolbar.left_action_items = [['arrow-left', lambda x: self.open_schedule(schedule_id, day, week_num, year) if add_mode == 'schedule' else self.switch_screen('add_homework')]]
        top_toolbar.right_action_items = [['check', lambda x: self.save_lesson_homework(id=homework_id, lesson_id=lesson_id, desc=desc_field.text, schedule_id=schedule_id, week_num=week_num, year=year, add_mode=add_mode)]]
        top_toolbar.title = f'Add Homework'

        self.switch_screen('add_lesson_homework', previous_screen)

    def save_lesson_homework(self, **kwargs):
        homework_id = kwargs['id']
        lesson_id = kwargs['lesson_id']
        desc = kwargs['desc']
        schedule_id = kwargs['schedule_id']
        week_num = kwargs['week_num']
        year = kwargs['year']
        lesson = self.get_lesson(schedule_id, lesson_id)
        day = lesson['day']
        notified = 0

        if desc.strip() == '':
            if homework_id is not None and self.Homework.exists(homework_id):
                self.Homework.delete(homework_id)
        else:
            if homework_id is None:
                homework_id = str(uuid.uuid4())

            text_limit = self.get_config_item('homework_desc_max_len')
            desc = desc[:text_limit]
            self.Homework.save(homework_id, lesson_id=lesson_id, desc=desc, week_num=week_num, year=year, notified=notified)
        if 'add_mode' in kwargs and kwargs['add_mode'] == 'homeworks':
            self.load_homeworks()
            self.back_to_main(1)
        else:
            self.open_schedule(schedule_id, day, week_num, year)

    def clear_homework(self, lesson_id):
        schedule_id = self.get_active_schedule_id()
        lesson = self.get_lesson(schedule_id, lesson_id)
        day = lesson['day']
        week_num = self.get_active_week_num()
        year = self.get_active_year()
        homework = self.get_homework(lesson_id, week_num, year)
        if homework is False:
            toast(f'warning: duplicated homeworks found. lesson_id: {lesson_id}, week_num: {week_num}, year: {year}')
        elif homework is not None:
            self.Homework.delete(homework[0])
        self.open_schedule(schedule_id, day, week_num, year)

    def week_back(self):
        schedule_id = self.get_active_schedule_id()
        day = self.get_current_tab_index('schedule')
        week_num = self.get_active_week_num() - 1
        year = self.get_active_year()
        if week_num == -1:
            week_num += 52
            year -= 1
        self.open_schedule(schedule_id, day, week_num, year)

    def week_next(self):
        schedule_id = self.get_active_schedule_id()
        day = self.get_current_tab_index('schedule')
        week_num = self.get_active_week_num() + 1
        year = self.get_active_year()
        if week_num == 52:
            week_num -= 52
            year += 1
        self.open_schedule(schedule_id, day, week_num, year)

    def week_current(self):
        schedule_id = self.get_active_schedule_id()
        cur_day = Util.calc_day_num()
        self.open_schedule(schedule_id, cur_day)

    def get_homework(self, lesson_id, week_num, year):
        homeworks = self.Homework.all()
        hw = list(homeworks.find(week_num=week_num, lesson_id=lesson_id, year=year))
        if len(hw) == 1:
            return hw[0]
        elif len(hw) == 0:
            return None
        else:
            return False

    def get_week_date_range(self, **kwargs):
        year = datetime.datetime.today().year if 'year' not in kwargs else kwargs['year']
        week_num = self.get_active_week_num() if 'week_num' not in kwargs else kwargs['week_num']
        try:
            monday = datetime.datetime.strptime(f'{year}-W{week_num}-1', '%Y-W%W-%w').date()
            sunday = datetime.datetime.strptime(f'{year}-W{week_num}-0', '%Y-W%W-%w').date()
            return f'{monday.strftime("%d %b")} - {sunday.strftime("%d %b")}'
        except ValueError as err:
            toast(f'Oops! Invalid date format: {err}')
            return False

    def open_settings(self):
        self.init_settings_theme_chip()
        self.init_settings_lang_chip()
        self.refresh_settings_notify_homework()
        self.switch_screen('settings')

    def init_settings_lang_chip(self):
        current_lang = self.Settings.get('user')['lang']
        lang_select = self.root.ids.lang_select
        for chip in lang_select.children:
            if chip.label in LANGUAGES[current_lang]:
                chip.color = self.theme_cls.primary_color
            else:
                chip.color = [0.4, 0.4, 0.4, 1]

    def init_settings_theme_chip(self):
        current_theme = self.Settings.get('theme')['style']
        theme_select = self.root.ids.theme_select
        for chip in theme_select.children:
            if chip.label in THEME_STYLES[current_theme]:
                chip.color = self.theme_cls.primary_color
            else:
                chip.color = [0.4, 0.4, 0.4, 1]

    def refresh_settings_notify_homework(self):
        current_value = self.Settings.get('notify')['homework']
        control = self.root.ids.notify_select
        control.text = current_value

    def reset_lang_chip_color(self, selected_lang):
        if self.init_lang_chip_color is True:
            current_lang = self.Settings.get('user')['lang']
            lang_select = self.root.ids.lang_select
            chip_to_reset = next(chip for chip in lang_select.children if chip.label in LANGUAGES[current_lang])
            chip_to_reset.color = [0.4, 0.4, 0.4, 1]
            self.init_lang_chip_color = False

    def reset_theme_chip_color(self, selected_theme):
        if self.init_theme_chip_color is True:
            current_theme = self.Settings.get('theme')['style']
            theme_select = self.root.ids.theme_select
            chip_to_reset = next(chip for chip in theme_select.children if chip.label in THEME_STYLES[current_theme])
            chip_to_reset.color = [0.4, 0.4, 0.4, 1]
            self.init_theme_chip_color = False

    def set_theme(self, theme=None):
        if theme is None:
            theme = self.Settings.get('theme')['style']
        if self.cfg['theme'][theme]['palette']:
            self.theme_cls.primary_palette = self.cfg['theme'][theme]['palette']
        if 'style' in self.cfg['theme'][theme]:
            self.theme_cls.theme_style = self.cfg['theme'][theme]['style']
        if 'accent' in self.cfg['theme'][theme]:
            self.theme_cls.accent_palette = self.cfg['theme'][theme]['accent']

    def set_fonts(self):
        for font in KIVY_FONTS:
            LabelBase.register(**font)

        font_name = 'Jura'
        theme_font_styles.append(font_name)

        self.theme_cls.font_styles["H1"] = [font_name, 96, False, -1.5,]
        self.theme_cls.font_styles["H2"] = [font_name, 60, False, -0.5,]
        self.theme_cls.font_styles["H3"] = [font_name, 48, False, 0,]
        self.theme_cls.font_styles["H4"] = [font_name, 34, False, 0.25,]
        self.theme_cls.font_styles["H5"] = [font_name, 24, False, 0,]
        self.theme_cls.font_styles["H6"] = [font_name, 20, False, 0.15,]
        self.theme_cls.font_styles["Subtitle1"] = [font_name, 16, False, 0.15,]
        self.theme_cls.font_styles["Subtitle2"] = [font_name, 14, False, 0.1,]
        self.theme_cls.font_styles["Body1"] = [font_name, 16, False, 0.5, ]
        self.theme_cls.font_styles["Body2"] = [font_name, 14, False, 0.25, ]
        self.theme_cls.font_styles["Button"] = [font_name, 14, False, 1.25, ]
        self.theme_cls.font_styles["Caption"] = [font_name, 12, False, 0.4, ]
        self.theme_cls.font_styles["Overline"] = [font_name, 10, False, 1.5, ]

        # Toolbar fonts
        toolbars = ['start_top_toolbar', 'settings_toolbar', 'schedule_toolbar', 'bottom_schedule_toolbar', 'add_schedule_top_toolbar', 'add_lesson_top_toolbar', 'add_homework_top_toolbar']
        for tb in toolbars:
            self.root.ids[tb].ids.label_title.font_name = "Jura"
            self.root.ids[tb].ids.label_title.font_size = "20sp"
            self.root.ids[tb].ids.label_title.bold = True

        # Schedule Tabs label fonts
        for i in range(0,7):
            tab_label = self.root.ids[f'tab_{i}'].tab_label
            tab_label.font_name = font_name
            tab_label.font_size = "16sp"
            tab_label.bold = True

        # Start Tabs label fonts
        start_tabs = ['schedules_tab', 'homeworks_tab']
        for st in start_tabs:
            tab_label = self.root.ids[st].tab_label
            tab_label.font_name = font_name
            tab_label.font_size = "16sp"
            tab_label.bold = True

    def get_theme_color(self, palette, hue):
        return get_color_from_hex(colors[palette][hue])

    def get_tabs_color(self):
        return get_color_from_hex(colors[self.theme_cls.primary_palette]['700'])

    def on_schedule_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        schedule_id = self.get_active_schedule_id()
        schedule = self.get_schedule(schedule_id)
        day_index = None
        for index, day in WEEK_DAYS.items():
            if day.lower() == tab_text.lower():
                day_index = index

        week_num = self.get_active_week_num()
        year = self.get_active_year()
        if week_num == 52:
            week_num -= 52
            year += 1
        self.root.ids.schedule_toolbar.title = f'{schedule["name"]} [{Util.get_date_str(year, week_num, day_index)}]'

    def on_start_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        if tab_text == 'Homeworks':
            self.load_homeworks()

    # @staticmethod
    # def do_notify(*args):
    #     keys = ['title', 'message', 'ticker', 'mode']
    #     params = dict(zip(keys, list(args[:-1])))
    #
    #     title = params['title']
    #     message = params['message']
    #     ticker = params['ticker']
    #     mode = params['mode']
    #
    #     kwargs = {'title': title, 'message': message, 'ticker': ticker}
    #
    #     if mode == 'fancy':
    #         kwargs['app_name'] = "Schedules"
    #         if platform == "win":
    #             kwargs['app_icon'] = join(dirname(realpath(__file__)), 'plyer-icon.ico')
    #             kwargs['timeout'] = 5
    #         else:
    #             kwargs['app_icon'] = join(dirname(realpath(__file__)), 'plyer-icon.png')
    #     elif mode == 'toast':
    #         kwargs['toast'] = True
    #     notification.notify(**kwargs)


settings = Settings()
tr = Lang(settings.get('user')['lang'])

MainApp().run()
