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
from Model import WEEK_DAYS, LANGUAGES, THEME_STYLES, Schedule, Timetable, Homework
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


class DayTab(BoxLayout, MDTabsBase):
    pass


class LessonsContainer(GridLayout):
    pass


class TimetableTimepicker(MDTimePicker):
    timetable_item_index = ObjectProperty()
    timetable_item_mode = ObjectProperty()


class NotifyTimepicker(MDTimePicker):
    pass


class ConfirmDeleteScheduleDialog(MDDialog):
    schedule_id = StringProperty()


class ConfirmDeleteLessonDialog(MDDialog):
    lesson_id = StringProperty()


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
        self.Timetable = None
        self.Homework = None
        self.current_schedule_id = None
        self.current_week_num = None
        self.current_year = None
        self.cfg = config
        self.init_lang_chip_color = True
        self.init_theme_chip_color = True
        super(MainApp, self).__init__(**kwargs)
        print("User data dir: %s" % self.user_data_dir)
        Window.bind(on_keyboard=self.on_key)

    def build(self):
        super(MainApp, self).build()
        self.Schedule = Schedule(table='schedules')
        self.Timetable = Timetable(table='timetables')
        self.Homework = Homework(table='homeworks')
        self.Settings = Settings()

        self.set_theme()

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
        self.load_schedules()

    def on_pause(self):
        return True

    def on_key(self, window, key, *args):
        if key == 27:
            if self.root.current == 'schedules':
                return True
            elif self.root.current in ['add_schedule', 'schedule', 'schedule_timetable', 'settings']:
                self.back_to_main()
                return True
            elif self.root.current in ['add_lesson', 'add_homework']:
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

    def switch_screen(self, screen):
        self.root.current = screen

    def create_demo_schedules(self):
        self.Schedule.clear()
        self.Timetable.clear()
        self.Homework.clear()

        schedule_key = str(uuid.uuid4())
        self.Schedule.save(schedule_key, name='School schedule',
                       lessons=[
                           {'id': str(uuid.uuid4()), 'name': 'Math', 'day': 0, 'order': 1},
                           {'id': str(uuid.uuid4()), 'name': 'Reading', 'day': 0, 'order': 2},
                           {'id': str(uuid.uuid4()), 'name': 'Literature', 'day': 0, 'order': 0},
                           {'id': str(uuid.uuid4()), 'name': 'Physics', 'day': 1, 'order': 1},
                           {'id': str(uuid.uuid4()), 'name': 'Music', 'day': 1, 'order': 0},
                           {'id': str(uuid.uuid4()), 'name': 'History', 'day': 1, 'order': 2},
                           {'id': str(uuid.uuid4()), 'name': 'Writing', 'day': 2, 'order': 0},
                           {'id': str(uuid.uuid4()), 'name': 'Math', 'day': 2, 'order': 1},
                           {'id': str(uuid.uuid4()), 'name': 'Math', 'day': 4, 'order': 0},
                           {'id': str(uuid.uuid4()), 'name': 'English', 'day': 4, 'order': 1},
                           {'id': str(uuid.uuid4()), 'name': 'Nature', 'day': 4, 'order': 2},
                           {'id': str(uuid.uuid4()), 'name': 'Music', 'day': 5, 'order': 0},
                       ])

        schedule_key = str(uuid.uuid4())
        self.Schedule.save(schedule_key, name='Art school schedule',
                       lessons=[
                           {'id': str(uuid.uuid4()), 'name': 'Painting', 'day': 0, 'order': 0},
                           {'id': str(uuid.uuid4()), 'name': 'Art History', 'day': 0, 'order': 1},
                           {'id': str(uuid.uuid4()), 'name': 'Graphics', 'day': 1, 'order': 0}
                       ])

        for schedule_id in self.Schedule.all():
            self.Timetable.save(schedule_id,
                                 lessons=[
                                     {'time_start': '08:30', 'time_end': '09:35'},
                                     {'time_start': '09:45', 'time_end': '10:25'},
                                     {'time_start': '13:15', 'time_end': '14:35'}
                                 ])

    def load_schedules(self):
        schedule_list = self.root.ids.schedule_list
        schedule_list.clear_widgets()
        schedules = self.Schedule.all()
        for schedule_id in schedules:
            schedule = self.Schedule.get(schedule_id)
            schedule_item = OneLineListItem(id=schedule_id, text=schedule['name'], on_release=self.show_schedule_item_options)
            self.root.ids.schedule_list.add_widget(schedule_item)

    def callback_for_schedule_menu_items(self, **kwargs):
        action = kwargs['action']
        schedule_id = kwargs['schedule_id']
        if action == 'open':
            day = self.calc_day_num()
            week_num = self.calc_week_num()
            year = self.calc_year()
            self.open_schedule(schedule_id, day, week_num, year)
        elif action == 'edit':
            self.add_schedule(schedule_id)
        elif action == 'delete':
            if self.schedule_has_future_homeworks(schedule_id):
                self.show_confirm_del_schedule_dialog(schedule_id)
            else:
                self.delete_schedule(schedule_id)
        elif action == 'time_table':
            self.open_schedule_time_table(schedule_id)

    def schedule_has_future_homeworks(self, schedule_id):
        has_homeworks = False
        schedule = self.get_schedule(schedule_id)
        lessons = schedule['lessons']
        homeworks = self.Homework.all()
        year_now = self.calc_year()
        week_now = self.calc_week_num()
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
        year_now = self.calc_year()
        week_now = self.calc_week_num()
        future_homeworks = list(x for x in list(homeworks.find(lesson_id=lesson['id'])) if x[1]['year'] >= year_now and x[1]['week_num'] >= week_now)
        return len(future_homeworks) > 0

    def show_schedule_item_options(self, instance):
        schedule_menu = MDGridBottomSheet()
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
        schedule_menu.add_item(
            tr._('Time Table'),
            lambda x: self.callback_for_schedule_menu_items(
                schedule_id=instance.id,
                action='time_table'
            ),
            icon_src='timetable',
        )
        schedule_menu.open()

    def open_schedule_time_table(self, schedule_id):
        self.set_active_schedule_id(schedule_id)
        schedule = self.get_schedule(schedule_id)
        timetable = self.get_schedule_timetable(schedule_id)
        timetable_list = self.root.ids.schedule_timetable_list
        timetable_list.clear_widgets()
        for i in range(len(timetable['lessons'])):
            time_start = timetable['lessons'][i]['time_start']
            time_end = timetable['lessons'][i]['time_end']
            text_color = 'Secondary' if time_start == '' and time_end == '' else 'Primary'
            if time_start == '':
                time_start = '..'
            if time_end == '':
                time_end = '..'
            timetable_item = OneLineListItem(text=f'{i + 1}.    {time_start} - {time_end}', theme_text_color=text_color, on_release=self.show_timetable_item_options)
            timetable_list.add_widget(timetable_item)

        self.root.ids.schedule_timetable_toolbar.title = f'{schedule["name"]} Timetable'
        self.switch_screen('schedule_timetable')

    def open_schedule(self, schedule_id, day_index=0, week_num=None, year=None):
        if week_num is None:
            week_num = self.calc_week_num(0)
        if year is None:
            year = self.calc_year(0)
        self.set_active_schedule_id(schedule_id)
        self.set_active_week_num(week_num)
        self.set_active_year(year)
        self.clear_schedule_tabs()
        schedule_tab_panel = MDTabs(
            background_color=get_color_from_hex(colors[self.theme_cls.primary_palette]['700']),
            tab_indicator_anim=True,
            tab_indicator_height='4dp',
            elevation=8
        )
        schedule = self.get_schedule(schedule_id)
        schedule_lessons = schedule['lessons']

        timetable = self.get_schedule_timetable(schedule_id)
        timetable_lessons = timetable['lessons']

        for i in range(len(WEEK_DAYS)):
            day_lessons = list(filter(lambda d: d['day'] == i, schedule_lessons))
            day_lessons = self.sort_lessons(day_lessons)
            tab = DayTab(text=WEEK_DAYS[i])
            day_tab_scrollview = ScrollView()
            lesson_list = MDList()
            for lesson in day_lessons:
                second_text = '.. - ..'
                if len(timetable_lessons) >= (lesson['order'] + 1):
                    time_start = timetable_lessons[lesson['order']]['time_start']
                    if time_start == '':
                        time_start = '..'
                    time_end = timetable_lessons[lesson['order']]['time_end']
                    if time_end == '':
                        time_end = '..'
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

            day_tab_scrollview.add_widget(lesson_list)
            tab.add_widget(day_tab_scrollview)
            schedule_tab_panel.add_widget(tab)

        self.root.ids.schedule_screen_layout.add_widget(schedule_tab_panel)
        schedule_tab_panel.ids.carousel.index = day_index

        date_range = self.get_week_date_range(week_num=week_num, year=year)
        self.root.ids.schedule_toolbar.title = f'{schedule["name"]} [{self.get_date(year, week_num, day_index)}]'
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
        elif action == 'move_up':
            self.move_lesson(lesson_id, 'up')
        elif action == 'move_down':
            self.move_lesson(lesson_id, 'down')
        elif action == 'add_homework':
            self.add_homework(lesson_id)
        elif action == 'clear_homework':
            self.clear_homework(lesson_id)

    def show_lesson_item_options(self, instance):
        lesson_menu = MDGridBottomSheet()
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
            'Move Up',
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='move_up'
            ),
            icon_src='arrow-up-bold',
        )
        lesson_menu.add_item(
            'Move Down',
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='move_down'
            ),
            icon_src='arrow-down-bold',
        )
        lesson_menu.open()

    def clear_schedule_tabs(self):
        for child in self.root.ids.schedule_screen_layout.children:
            if type(child).__name__ == 'MDToolbar' and child.id == 'schedule_bottom_toolbar':
                self.root.ids.schedule_screen_layout.remove_widget(child)
        for child in self.root.ids.schedule_screen_layout.children:
            if type(child).__name__ == 'MDTabs':
                self.root.ids.schedule_screen_layout.remove_widget(child)

    def schedule_bottom_bar_exists(self):
        exists = False
        for child in self.root.ids.schedule_screen_layout.children:
            if type(child).__name__ == 'MDBottomAppBar':
                exists = True
        return exists

    @staticmethod
    def sort_lessons(lessons):
        return sorted(lessons, key=lambda i: i['order'])

    def back_to_main(self):
        self.reset_active_schedule_id()
        self.reset_active_week_num()
        self.reset_active_year()
        self.switch_screen('schedules')

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

    def get_schedule_timetable(self, schedule_id):
        return self.Timetable.get(schedule_id)

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
            if is_new:
                self.Timetable.save(schedule_id, lessons=[])
            self.load_schedules()
            self.back_to_main()
            toast(f'Schedule {"created" if is_new else "updated"}')

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
                day_lessons = list(filter(lambda d: d['day'] == day, lessons))
                day_lessons = self.sort_lessons(day_lessons)
                order = 0 if len(day_lessons) == 0 else day_lessons[-1]['order'] + 1
                lessons.append({'id': str(uuid.uuid4()), 'name': title, 'day': day, 'order': order})
            self.Schedule.save(schedule_id, name=schedule['name'], lessons=lessons)

            if not is_new and del_homeworks:
                self.delete_homeworks(lesson_id=lesson_id)

            self.open_schedule(schedule_id, day, week_num, year)
            toast(f'Lesson {"created" if is_new else "updated"}')

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
        self.Timetable.delete(schedule_id)
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
        return next(item for item in schedule['lessons'] if item['id'] == lesson_id)

    def delete_lesson(self, lesson_id):
        self.delete_homeworks(lesson_id=lesson_id)

        schedule_id = self.get_active_schedule_id()
        day = self.get_current_day_tab_index()
        week_num = self.get_active_week_num()
        year = self.get_active_year()
        schedule = self.get_schedule(schedule_id)
        lessons = schedule['lessons']
        day_lessons = list(filter(lambda d: d['day'] == day, lessons))
        day_lessons = self.sort_lessons(day_lessons)
        current_lesson_index = next((index for (index, d) in enumerate(day_lessons) if d['id'] == lesson_id), None)
        del day_lessons[current_lesson_index]
        for i in range(len(day_lessons)):
            _lesson_index = next((index for (index, d) in enumerate(lessons) if d['id'] == day_lessons[i]['id']), None)
            lessons[_lesson_index]['order'] = i

        del_lesson_index = next((index for (index, d) in enumerate(lessons) if d['id'] == lesson_id), None)
        del lessons[del_lesson_index]

        self.open_schedule(schedule_id, day, week_num, year)
        toast('Lesson deleted')

    def move_lesson(self, current_lesson_id, move_to):
        schedule_id = self.get_active_schedule_id()
        day = self.get_current_day_tab_index()
        week_num = self.get_active_week_num()
        year = self.get_active_year()
        schedule = self.get_schedule(schedule_id)
        lessons = schedule['lessons']
        day_lessons = list(filter(lambda d: d['day'] == day, lessons))
        day_lessons = self.sort_lessons(day_lessons)
        current_lesson_index = next((index for (index, d) in enumerate(day_lessons) if d['id'] == current_lesson_id), None)
        current_lesson_order = day_lessons[current_lesson_index]['order']
        target_lesson_order = None
        target_lesson_id = None
        if current_lesson_index == (len(day_lessons) - 1) and move_to == 'down':
            return
        if current_lesson_index == 0 and move_to == 'up':
            return
        if move_to == 'up':
            target_lesson_order = current_lesson_order - 1
            target_lesson_id = day_lessons[current_lesson_index - 1]['id']
        elif move_to == 'down':
            target_lesson_order = current_lesson_order + 1
            target_lesson_id = day_lessons[current_lesson_index + 1]['id']

        for lesson in lessons:
            if lesson['id'] == current_lesson_id:
                lesson['order'] = target_lesson_order
            elif lesson['id'] == target_lesson_id:
                lesson['order'] = current_lesson_order

        self.Schedule.save(schedule_id, name=schedule['name'], lessons=lessons)
        self.open_schedule(schedule_id, day, week_num, year)

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

    def add_lesson(self, lesson_id=None):
        title_field = self.root.ids.add_lesson_title
        top_toolbar = self.root.ids.add_lesson_top_toolbar
        grid_layout = self.root.ids.add_lesson_grid_layout

        day = self.get_current_day_tab_index()
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

    def get_current_day_tab_index(self):
        for child in self.root.ids.schedule_screen_layout.children:
            if type(child).__name__ == 'MDTabs':
                return child.carousel.index

    @staticmethod
    def show_error(**kwargs):
        Snackbar(text=kwargs['text']).show()

    def add_schedule_timetable_item(self):
        schedule_id = self.get_active_schedule_id()
        self.add_timetable_item(schedule_id)
        self.open_schedule_time_table(schedule_id)

    def show_timetable_item_options(self, instance):
        item_index = None
        for i in range(len(instance.parent.children)):
            if instance == instance.parent.children[i]:
                item_index = i

        item_menu = MDGridBottomSheet()
        item_menu.add_item(
            'Set Start Time',
            lambda x: self.callback_for_timetable_item_menu(
                item_index=item_index,
                action='set_start_time'
            ),
            icon_src='clock-in',
        )
        item_menu.add_item(
            'Set End Time',
            lambda x: self.callback_for_timetable_item_menu(
                item_index=item_index,
                action='set_end_time'
            ),
            icon_src='clock-out',
        )
        item_menu.add_item(
            'Clear Time',
            lambda x: self.callback_for_timetable_item_menu(
                item_index=item_index,
                action='clear_time'
            ),
            icon_src='eraser',
        )
        item_menu.add_item(
            'Remove',
            lambda x: self.callback_for_timetable_item_menu(
                item_index=item_index,
                action='remove'
            ),
            icon_src='delete',
        )
        item_menu.open()

    def callback_for_timetable_item_menu(self, **kwargs):
        action = kwargs['action']
        item_index = kwargs['item_index']
        if action == 'set_start_time':
            self.set_timetable_item_time(item_index, 'time_start')
        if action == 'set_end_time':
            self.set_timetable_item_time(item_index, 'time_end')
        elif action == 'clear_time':
            self.clear_timetable_item_time(item_index)
        elif action == 'remove':
            self.del_timetable_item_time(item_index)

    def set_timetable_item_time(self, item_index, mode):
        schedule_id = self.get_active_schedule_id()
        timetable = self.get_schedule_timetable(schedule_id)
        time_dialog = TimetableTimepicker(timetable_item_index=item_index, timetable_item_mode=mode)
        time_dialog.bind(time=self.get_timepicker_time)

        lessons = list(reversed(timetable['lessons']))
        if lessons[item_index][mode] != '':
            time = datetime.datetime.strptime(lessons[item_index][mode], '%H:%M').time()
            try:
                time_dialog.set_time(time)
            except AttributeError:
                pass
        time_dialog.open()

    def get_timepicker_time(self, instance, time):
        schedule_id = self.get_active_schedule_id()
        item_index = instance.timetable_item_index
        item_mode = instance.timetable_item_mode
        self.update_timetable(schedule_id, item_index, item_mode, time)
        self.open_schedule_time_table(schedule_id)

    def clear_timetable_item_time(self, item_index):
        schedule_id = self.get_active_schedule_id()
        self.update_timetable(schedule_id, item_index, 'time_start', '')
        self.update_timetable(schedule_id, item_index, 'time_end', '')
        self.open_schedule_time_table(schedule_id)

    def del_timetable_item_time(self, item_index):
        schedule_id = self.get_active_schedule_id()
        self.remove_timetable_item(schedule_id, item_index)
        self.open_schedule_time_table(schedule_id)

    def add_timetable_item(self, schedule_id):
        timetable = self.get_schedule_timetable(schedule_id)
        lessons = timetable['lessons']
        lessons.append({'time_start': '', 'time_end': ''})
        self.Timetable.save(schedule_id, lessons=lessons)

    def update_timetable(self, schedule_id, item_index, item_mode, time):
        time_str = time.strftime('%H:%M') if type(time) is datetime.time else time
        timetable = self.get_schedule_timetable(schedule_id)
        lessons = list(reversed(timetable['lessons']))
        lessons[item_index][item_mode] = time_str
        self.Timetable.save(schedule_id, lessons=list(reversed(lessons)))

    def remove_timetable_item(self, schedule_id, item_index):
        timetable = self.get_schedule_timetable(schedule_id)
        lessons = list(reversed(timetable['lessons']))
        del lessons[item_index]
        self.Timetable.save(schedule_id, lessons=list(reversed(lessons)))

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

    def add_homework(self, lesson_id):
        schedule_id = self.get_active_schedule_id()
        lesson = self.get_lesson(schedule_id, lesson_id)
        desc_field = self.root.ids.add_homework_desc_text
        top_toolbar = self.root.ids.add_homework_top_toolbar
        subtitle = self.root.ids.add_homework_subtitle

        week_num = self.get_active_week_num()
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
        subtitle.text = f'{lesson["name"]} for {self.get_date(year, week_num, day)}'

        top_toolbar.left_action_items = [['arrow-left', lambda x: self.open_schedule(schedule_id, day, week_num, year)]]
        top_toolbar.right_action_items = [['check', lambda x: self.save_homework(id=homework_id, lesson_id=lesson_id, desc=desc_field.text)]]
        top_toolbar.title = f'Add Homework'

        self.switch_screen('add_homework')

    def save_homework(self, **kwargs):
        homework_id = kwargs['id']
        lesson_id = kwargs['lesson_id']
        desc = kwargs['desc']
        schedule_id = self.get_active_schedule_id()
        week_num = self.get_active_week_num()
        year = self.get_active_year()
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
        self.open_schedule(schedule_id, day, week_num, year)
        # Clock.schedule_once(partial(self.do_notify, 'Homework Added', f'Homework added for {lesson["name"]}', 'homework added ticker', 'fancy'), 3)
        # self.do_notify('Homework Added', f'Homework added for {lesson["name"]}', 'homework added ticker', mode='toast')

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
        week_num = self.get_active_week_num() - 1
        year = self.get_active_year()
        if week_num == -1:
            week_num += 52
            year -= 1
        self.open_schedule(schedule_id, 0, week_num, year)

    def week_next(self):
        schedule_id = self.get_active_schedule_id()
        week_num = self.get_active_week_num() + 1
        year = self.get_active_year()
        if week_num == 52:
            week_num -= 52
            year += 1
        self.open_schedule(schedule_id, 0, week_num, year)

    def week_current(self):
        schedule_id = self.get_active_schedule_id()
        cur_day = self.calc_day_num()
        self.open_schedule(schedule_id, cur_day)

    # todo: use from Util
    @staticmethod
    def calc_week_num(add=0):
        current = int(datetime.datetime.today().strftime("%W"))
        return current + add

    # todo: use from Util
    @staticmethod
    def calc_year(add=0):
        current = datetime.datetime.today().year
        return current + add

    # todo: use from Util
    @staticmethod
    def calc_day_num(add=0):
        current = datetime.datetime.today().weekday()
        return current + add

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

    @staticmethod
    def get_date(year, week_num, day_index):
        day = day_index + 1
        if day == 7:
            day = 0
        date = datetime.datetime.strptime(f'{year}-W{week_num}-{day}', '%Y-W%W-%w').date()
        return f'{date.strftime("%a %d %b, %Y")}'

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
