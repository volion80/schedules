from kivy.utils import platform
from Config import config
if config['env'] == 'dev_home':
    import os
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'
from kivymd.app import MDApp
from kivymd.uix.list import ThreeLineAvatarIconListItem, OneLineAvatarIconListItem
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.tab import MDTabsBase, MDTabs
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, BooleanProperty
from kivy.utils import get_color_from_hex
from kivymd.toast import toast
from kivymd.uix.button import MDFlatButton, MDFillRoundFlatButton, MDRectangleFlatIconButton, MDFillRoundFlatIconButton, MDRoundFlatIconButton, MDTextButton, MDRaisedButton
from kivymd.uix.behaviors.toggle_behavior import MDToggleButton
from kivy.metrics import dp
from kivymd.uix.picker import MDTimePicker
from kivymd.uix.label import MDLabel
import datetime
from kivy.core.window import Window
from kivy.lang import Observable
from os.path import join, dirname
import gettext
from kivymd.color_definitions import colors
from kivymd.uix.selectioncontrol import MDCheckbox
from osc.osc_app_server import OscAppServer
from service.utils import start_service
from kivymd.uix.bottomsheet import MDGridBottomSheet
from kivymd.font_definitions import theme_font_styles
from kivymd.uix.picker import MDDatePicker
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import IRightBodyTouch, ILeftBodyTouch
from kivy.uix.button import Button
from kivy.uix.behaviors.togglebutton import ToggleButtonBehavior
from random import randrange, randint
from Util import Util
from Database import Database
from kivy.core.text import LabelBase
from decorators import log_time
from demo_data import lesson_names, time_ranges
from kivy.uix.recycleview import RecycleView
from kivymd.uix.textfield import MDTextField
from plyer import notification
if platform == 'android':
    from DroidNotification import DroidNotification

import sentry_sdk


KIVY_FONTS = [
    {
        "name": "Jura",
        "fn_regular": "fonts/Jura/static/Jura-Medium.ttf",
        "fn_bold": "fonts/Jura/static/Jura-Bold.ttf",
    }
]

SETTINGS_DEFAULTS = [
    {'name': 'lang', 'val': 'en'},
    {'name': 'remind_homework_time', 'val': '16:00'},
    {'name': 'theme_color', 'val': 'LightGreen'},
    {'name': 'theme_style', 'val': 'Light'}
]

class NotifyTimepicker(MDTimePicker):
    pass


class LessonTimepicker(MDTimePicker):
    lesson_id = ObjectProperty()
    time_mode = ObjectProperty()


class ConfirmDeleteScheduleDialog(MDDialog):
    schedule_id = StringProperty()


class ConfirmDeleteLessonDialog(MDDialog):
    lesson_id = StringProperty()


class ScheduleGridBottomSheet(MDGridBottomSheet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sheet_list.ids.box_sheet_list.padding = (dp(16), 0, dp(16), dp(16))


class OneLineScheduleListItem(OneLineAvatarIconListItem):
    pass


class ThreeLineLessonListItem(ThreeLineAvatarIconListItem):
    pass


class ThreeLineHomeworkListItem(ThreeLineAvatarIconListItem):
    done = BooleanProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class ScheduleLessonListRV(RecycleView):
    def __init__(self, **kwargs):
        super(ScheduleLessonListRV, self).__init__(**kwargs)

    def update(self, data):
        self.data = data


class HomeworkListRV(RecycleView):
    def __init__(self, **kwargs):
        super(HomeworkListRV, self).__init__(**kwargs)

    def update(self, data):
        self.data = data


class RoundFlatToggleButton(MDFillRoundFlatIconButton, MDToggleButton):
    item_id = NumericProperty()

    def __init__(self, **kwargs):
        self._radius = "5dp"
        self.ripple_alpha = 0
        super().__init__(**kwargs)


class SettingsThemeColorToggleButton(MDFillRoundFlatButton, MDToggleButton):
    setting_value = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class SettingsThemeStyleToggleButton(MDFillRoundFlatButton, MDToggleButton):
    setting_value = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class SettingsLangToggleButton(MDFillRoundFlatButton, MDToggleButton):
    setting_value = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MDRoundFlatIconDateButton(MDFillRoundFlatIconButton):
    def __init__(self, **kwargs):
        self._radius = "5dp"
        super().__init__(**kwargs)


class MDFillRoundFlatProceedButton(MDRaisedButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class TitleTextField(MDTextField):
    text_max = NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_text(self, instance, val):
        if len(val) > self.text_max:
            self.text = val[:self.text_max]
        super().on_text(instance, val)

    def on_focus(self, *args):
        app = MainApp.get_running_app()
        app.add_schedule_title_on_focus(args[1])
        super().on_focus()




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
        self.current_schedule_id = None
        self.current_week_num = None
        self.current_year = None
        self.cfg = config
        self.confirm_delete_schedule_dialog = None
        self.confirm_delete_lesson_dialog = None
        self.db = None
        self.history = []
        self.init_sentry()
        super(MainApp, self).__init__(**kwargs)

    def build(self):
        super(MainApp, self).build()
        self.db = Database()
        self.db.setup_schema()

        self.check_settings()

        self.set_theme_color()
        self.set_theme_style()
        self.set_fonts()

        self.start_services()

        return self.root

    def init_sentry(self):
        if platform == 'android':
            sentry_sdk.init("https://02810d9a4a0547408822ce2500480a32@o492578.ingest.sentry.io/5560168", traces_sample_rate=1.0)

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
        Window.bind(on_keyboard=self.on_key)
        self.load_start_screen()

    def on_pause(self):
        return True

    def on_key(self, window, key, *args):
        if key == 27:
            if self.root.current == 'start':
                return True
            else:
                self.go_back()
                return True

    def change_lang(self, btn):
        lang = btn.setting_value
        self.db.update_setting('lang', lang)
        self.lang = lang

    def change_theme_color(self, btn):
        theme_color = btn.setting_value
        self.db.update_setting('theme_color', theme_color)
        self.set_theme_color(cb=self.refresh_settings)
        self.load_homeworks()

    def change_theme_style(self, btn):
        theme_style = btn.setting_value
        self.db.update_setting('theme_style', theme_style)
        self.set_theme_style(cb=self.refresh_settings)
        self.load_homeworks()

    def check_settings(self):
        for setting in SETTINGS_DEFAULTS:
            self.db.add_setting(name=setting['name'], val=setting['val'])

    def create_demo_schedules(self, num=1, cb=None):
        for s in range(num):
            schedule_name = 'Demo ' + str(Util.current_milli_time())
            schedule_id = self.db.add_schedule(name=schedule_name)
            lessons = []
            for d in range(6):
                for ls in range(randrange(5, 7)):
                    time_range = time_ranges[randrange(len(time_ranges))]
                    lesson = {
                        'schedule_id': schedule_id,
                        'day': d,
                        'name': lesson_names[randrange(len(lesson_names))],
                        'time_start': time_range['start'],
                        'time_end': time_range['end']
                    }
                    lessons.append(lesson)

            self.db.add_lessons(lessons)

        lesson_rows = self.db.get_lessons()
        for i in range(20):
            lesson_row = lesson_rows[randrange(len(lesson_rows))]
            week_num = Util.calc_week_num(randrange(1, 10))
            year = Util.calc_year()
            if week_num >= 52:
                week_num -= 52
                year += 1
            homework_exists = self.db.homework_exists(lesson_id=lesson_row['id'], week_num=week_num, year=year)
            if not homework_exists:
                self.db.add_homework(lesson_id=lesson_row['id'], week_num=week_num, year=year,
                                     desc=f'test homework for {lesson_row["name"]}', done=randint(0, 1), notifiable=randint(0, 1))

        if cb is not None:
            cb()

    def load_start_screen(self):
        start_tab_panel = self.root.ids.start_tabs
        start_tab_panel.background_color = self.get_tabs_color()
        self.load_schedules()
        self.load_homeworks()

    def on_screen_pre_enter(self, screen):
        if screen.name == 'start':
            self.root.ids.start_tabs.background_color = self.get_tabs_color()

    # @log_time
    def load_schedules(self):
        schedule_list = self.root.ids.schedule_list
        Util.clear_list_items(schedule_list)
        schedules = self.db.get_schedules()
        for schedule in schedules:
            schedule_item = OneLineScheduleListItem(
                id=str(schedule['id']),
                text=schedule['name']
            )
            schedule_list.add_widget(schedule_item)

    def load_homeworks(self):
        week_now = Util.calc_week_num()
        year_now = Util.calc_year()
        day_now = Util.calc_day_num()
        homework_list = self.root.ids.homework_list
        homeworks = self.db.get_upcoming_homeworks(week_num=week_now, year=year_now, day=day_now)

        homework_data = []
        for homework in homeworks:
            homework_date = Util.get_date(homework['year'], homework['week_num'], homework['day'])
            is_today = datetime.datetime.today().strftime("%Y-%m-%d") == homework_date.strftime("%Y-%m-%d")
            homework_data.append({
                'id': str(homework['id']),
                'text': f'{homework["lesson_name"]} ({homework["schedule_name"]}) {homework["lesson_time_start"]}',
                'font_style': 'Body1',
                'secondary_text': self.translate_date(homework_date.strftime("%a %d %b, %Y"), '%a %d %b, %Y'),
                'secondary_theme_text_color': 'Custom',
                'secondary_text_color': self.theme_cls.primary_dark if not is_today else self.theme_cls.accent_dark,
                'secondary_font_style': 'Subtitle1',
                'tertiary_text': homework['desc'],
                'tertiary_font_style': 'Subtitle2',
                'bg_color': self.theme_cls.primary_light_hue if homework['done'] == 1 else self.theme_cls.bg_normal,
                'done': homework['done'] == 1
            })
        homework_list.update(homework_data)

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
            homework = self.db.get_homework(homework_id)
            self.add_lesson_homework(homework['lesson_id'], homework['schedule_id'], homework['week_num'], homework['year'])
        elif action == 'delete':
            self.db.delete_homework(homework_id)
        elif action == 'mark':
            done = 0 if kwargs['done'] else 1
            self.db.update_homework(id=homework_id, done=done)
        if 'cb' in kwargs:
            kwargs['cb']()

    def schedule_has_future_homeworks(self, schedule_id):
        year = Util.calc_year()
        week_num = Util.calc_week_num()
        return self.db.schedule_has_homeworks(schedule_id=schedule_id, year=year, week_num=week_num)

    def lesson_has_future_homeworks(self, lesson_id):
        year = Util.calc_year()
        week_num = Util.calc_week_num()
        return self.db.lesson_has_homeworks(lesson_id=lesson_id, year=year, week_num=week_num)

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
                action='delete',
                cb=self.load_homeworks
            ),
            icon_src='delete',
        )
        mark_text = tr._('Undone') if instance.done else tr._('Done')
        mark_icon = 'checkbox-blank-off' if instance.done else 'checkbox-marked'
        homework_menu.add_item(
            mark_text,
            lambda x: self.callback_for_homework_menu_items(
                homework_id=instance.id,
                done=instance.done,
                action='mark',
                cb=self.load_homeworks
            ),
            icon_src=mark_icon,
        )
        homework_menu.open()

    # @log_time
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

        tab_list = schedule_tab_panel.get_tab_list()

        week_days = self.week_days()
        for i in range(len(week_days)):
            tab = tab_list[(len(tab_list) - 1) - i]
            tab.text = week_days[i]
            lesson_list = self.root.ids[f'lesson_list_day_{i}']
            lessons = self.db.get_lessons(schedule_id=schedule_id, day=i, homework_week_num=week_num, homework_year=year)
            lessons_data = []
            for lesson in lessons:
                time_start = lesson['time_start'] if lesson['time_start'] != '' else '..'
                time_end = lesson['time_end'] if lesson['time_end'] != '' else '..'

                lessons_data.append({
                    'id': str(lesson['id']),
                    'text': lesson['name'],
                    'secondary_text': f'{time_start} - {time_end}',
                    'tertiary_text': ' ' if lesson['homework_desc'] is None else lesson['homework_desc']
                })
            lesson_list.update(lessons_data)

        schedule = self.db.get_schedule(schedule_id)
        schedule_tab_panel.ids.carousel.index = day_index
        date_range = self.get_week_date_range(week_num=week_num, year=year)
        date_str = Util.get_date_str(year, week_num, day_index)
        self.root.ids.schedule_toolbar.title = f'{schedule["name"]} ({self.translate_date(date_str, "%a %d %b, %Y")})'
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
        homework = self.db.find_homework(lesson_id=instance.id, week_num=week_num, year=year)
        if homework is None:
            hw_action_name = tr._('Add')
        elif homework is False:
            toast(f'warning: duplicated homeworks found. lesson_id: {instance.id}, week_num: {week_num}, year: {year}')
            hw_action_name = tr._('Add')
        else:
            hw_action_name = tr._('Edit')
            homework_exists = True

        lesson_menu.add_item(
            f'{hw_action_name} ' + tr._('Task'),
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='add_homework'
            ),
            icon_src='home-plus',
        )
        if homework_exists:
            lesson_menu.add_item(
                tr._('Clear Task'),
                lambda x: self.callback_for_lesson_menu_items(
                    lesson_id=instance.id,
                    action='clear_homework'
                ),
                icon_src='home-minus',
            )

        lesson_menu.add_item(
            tr._('Edit'),
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='edit'
            ),
            icon_src='pencil',
        )

        lesson_menu.add_item(
            tr._('Delete'),
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='delete'
            ),
            icon_src='delete',
        )
        lesson_menu.add_item(
            tr._('Set Time Start'),
            lambda x: self.callback_for_lesson_menu_items(
                lesson_id=instance.id,
                action='set_start_time'
            ),
            icon_src='clock-in',
        )
        lesson_menu.add_item(
            tr._('Set Time End'),
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

    def save_schedule(self, **kwargs):
        title_field = self.root.ids.add_schedule_title
        schedule_id = kwargs['schedule_id']
        title = kwargs['title']

        title_limit = self.get_config_item('schedule_title_max_len')
        title = title[:title_limit]

        if title.strip() == '':
            title_field.text = ''
            self.show_error(text='Missing Schedule name!')
        else:
            if schedule_id is not None:
                self.db.update_schedule(id=schedule_id, name=title)
            else:
                self.db.add_schedule(name=title)

            if 'cb' in kwargs:
                kwargs['cb']()

    def save_lesson(self, **kwargs):
        title_field = self.root.ids.add_lesson_title
        lesson_id = kwargs['lesson_id']
        schedule_id = kwargs['schedule_id']
        day = kwargs['day']
        title = kwargs['title']
        del_homeworks = kwargs['del_homeworks']

        title_limit = self.get_config_item('lesson_title_max_len')
        title = title[:title_limit]
        if title.strip() == '':
            title_field.text = ''
            self.show_error(text='Title cannot be empty!')
        else:
            if lesson_id is not None:
                self.db.update_lesson(id=lesson_id, name=title)
                if del_homeworks:
                    self.db.delete_homeworks(lesson_id=lesson_id)
            else:
                lessons = [{'name': title, 'day': day, 'time_start': '', 'time_end': '', 'schedule_id': schedule_id}]
                self.db.add_lessons(lessons)

                if 'cb' in kwargs:
                    kwargs['cb']()

    def show_confirm_del_schedule_dialog(self, schedule_id):
        schedule = self.db.get_schedule(schedule_id)
        self.confirm_delete_schedule_dialog = ConfirmDeleteScheduleDialog(
            title=f'Delete {schedule["name"]}?',
            size_hint=(0.8, 0.4),
            text=f'There are homeworks assigned related to the schedule.\n\nDelete anyway?',
            schedule_id=schedule_id,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    text_color=self.theme_cls.primary_color,
                    on_release=self.callback_confirm_del_schedule
                ),
                MDFlatButton(
                    text="ACCEPT",
                    text_color=self.theme_cls.primary_color,
                    on_release=self.callback_confirm_del_schedule
                ),
            ],
        )
        self.confirm_delete_schedule_dialog.open()

    def show_confirm_del_lesson_dialog(self, lesson_id):
        lesson = self.db.get_lesson(id=lesson_id)
        self.confirm_delete_lesson_dialog = ConfirmDeleteLessonDialog(
            title=f'Delete {lesson["name"]}?',
            size_hint=(0.8, 0.4),
            text=f'There are homeworks assigned to the lesson.\n\nDelete anyway?',
            lesson_id=lesson_id,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    text_color=self.theme_cls.primary_color,
                    on_release=self.callback_confirm_del_lesson
                ),
                MDFlatButton(
                    text="ACCEPT",
                    text_color=self.theme_cls.primary_color,
                    on_release=self.callback_confirm_del_lesson
                ),
            ],
        )
        self.confirm_delete_lesson_dialog.open()

    def callback_confirm_del_schedule(self, *args):
        button = args[0]
        confirm = button.text == 'ACCEPT'
        if confirm:
            schedule_id = self.confirm_delete_schedule_dialog.schedule_id
            self.delete_schedule(schedule_id)
        self.confirm_delete_schedule_dialog.dismiss()
        self.confirm_delete_schedule_dialog = None

    def callback_confirm_del_lesson(self, *args):
        button = args[0]
        confirm = button.text == 'ACCEPT'
        if confirm:
            lesson_id = self.confirm_delete_lesson_dialog.lesson_id
            self.delete_lesson(lesson_id)
        self.confirm_delete_lesson_dialog.dismiss()
        self.confirm_delete_lesson_dialog = None

    def delete_schedule(self, schedule_id):
        self.db.delete_homeworks(schedule_id=schedule_id)
        self.db.delete_lessons(schedule_id=schedule_id)
        self.db.delete_schedule(schedule_id)
        self.load_schedules()
        self.load_homeworks()

    def delete_lesson(self, lesson_id):
        self.db.delete_homeworks(lesson_id=lesson_id)
        self.db.delete_lessons(id=lesson_id)

        schedule_id = self.get_active_schedule_id()
        day = self.get_current_tab_index('schedule')
        week_num = self.get_active_week_num()
        year = self.get_active_year()
        self.load_homeworks()
        self.open_schedule(schedule_id, day, week_num, year)

    def on_start_add_button_release(self):
        tab_index = self.get_current_tab_index('start')
        if tab_index == 0:
            self.add_schedule()
        elif tab_index == 1:
            self.add_homework()

    def add_schedule(self, schedule_id=None):
        title_field = self.root.ids.add_schedule_title
        top_toolbar = self.root.ids.add_schedule_top_toolbar

        schedule = self.db.get_schedule(schedule_id) if schedule_id else None

        title_field.text = '' if not schedule else schedule['name']
        title_field.focus = True

        def cb():
            self.load_schedules()
            self.go_back()

        top_toolbar.left_action_items = [['arrow-left', lambda x: self.go_back()]]
        top_toolbar.right_action_items = [['check', lambda x: self.save_schedule(schedule_id=schedule_id, title=title_field.text, cb=cb)]]
        top_toolbar.title = tr._('Edit Schedule') if schedule is not None else tr._('Add Schedule')
        self.switch_screen('add_schedule')

    def add_schedule_title_on_focus(self, focused):
        if not focused:
            self.request_focus_for_main_view()

    def add_homework(self):
        top_toolbar = self.root.ids.add_homework_top_toolbar
        hw_date = self.root.ids.add_homework_date
        today = datetime.datetime.today().date()
        hw_date.text = str(today)
        self.add_homework_load_schedules(today)
        top_toolbar.left_action_items = [['arrow-left', lambda x: self.go_back()]]
        self.switch_screen('add_homework')

    def open_add_homework(self):
        str_date = self.root.ids.add_homework_date.text
        date = datetime.datetime.strptime(str_date, '%Y-%m-%d').date()
        schedule_id = self.add_homework_get_selected_schedule()
        lesson_id = self.add_homework_get_selected_lesson()

        if schedule_id is None:
            toast('Unable get selected Schedule')
            return
        if lesson_id is None:
            toast('Unable get selected Lesson')
            return
        week_num = int(date.strftime("%W"))
        year = date.year

        self.add_lesson_homework(lesson_id, schedule_id, week_num, year)

    def add_homework_get_selected_schedule(self):
        schedule_id = None
        widgets = ToggleButtonBehavior.get_widgets('schedule')
        for w in widgets:
            if w.state == 'down':
                schedule_id = w.item_id
                break
        del widgets
        return schedule_id

    def add_homework_get_selected_lesson(self):
        lesson_id = None
        widgets = ToggleButtonBehavior.get_widgets('lesson')
        for w in widgets:
            if w.state == 'down':
                lesson_id = w.item_id
                break
        del widgets
        return lesson_id

    def open_add_homework_datepicker(self):
        str_date = self.root.ids.add_homework_date.text
        date = datetime.datetime.strptime(str_date, '%Y-%m-%d').date()
        today = datetime.datetime.today().date()
        min_date = today - datetime.timedelta(days=1)
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
        self.add_homework_load_schedules(date)

    def add_homework_load_schedules(self, date):
        self.add_homework_reset_schedules()
        self.add_homework_reset_lessons()
        self.add_homework_toggle_next_button(True)

        schedules_wrapper = self.root.ids.add_homework_schedules_wrapper
        weekday = date.weekday()

        schedules = self.db.get_schedules(day=weekday)
        for schedule in schedules:
            schedule_button = RoundFlatToggleButton(
                text=schedule['name'],
                item_id=schedule['id'],
                icon="view-list",
                group="schedule",
                pos_hint={"center_x": .5},
                background_down=self.theme_cls.accent_color,
                font_name=self.get_app_font(),
                on_release=self.add_homework_schedule_button_click
            )
            schedules_wrapper.add_widget(schedule_button)

        if len(schedules_wrapper.children) == 0:
            not_found_btn = MDTextButton(text=tr._("No Schedules available"))
            schedules_wrapper.add_widget(not_found_btn)

        self.add_homework_add_lessons_hint()

    def add_homework_add_lessons_hint(self):
        hint_btn = MDTextButton(text=tr._("Select a Schedule..."), font_name=self.get_app_font())
        self.root.ids.add_homework_lessons_wrapper.add_widget(hint_btn)

    def add_homework_reset_lessons(self):
        self.root.ids.add_homework_lessons_wrapper.clear_widgets()

    def add_homework_reset_schedules(self):
        self.root.ids.add_homework_schedules_wrapper.clear_widgets()

    def add_homework_schedule_button_click(self, button):
        schedule_id = button.item_id
        str_date = self.root.ids.add_homework_date.text
        date = datetime.datetime.strptime(str_date, '%Y-%m-%d').date()
        is_down = button.state == 'down'
        self.add_homework_load_lessons(date, schedule_id, is_down)

    def add_homework_load_lessons(self, date, schedule_id, btn_is_down):
        lessons_wrapper = self.root.ids.add_homework_lessons_wrapper
        self.add_homework_reset_lessons()
        self.add_homework_toggle_next_button(True)
        if not btn_is_down:
            self.add_homework_add_lessons_hint()
            return
        day = date.weekday()
        lessons = self.db.get_lessons(day=day, schedule_id=schedule_id)
        for lesson in lessons:
            lesson_button = RoundFlatToggleButton(
                text=lesson['name'],
                item_id=lesson['id'],
                icon="book-open-page-variant",
                group="lesson",
                pos_hint={"center_x": .5},
                background_down=self.theme_cls.accent_dark,
                font_name=self.get_app_font(),
                on_release=self.add_homework_lesson_button_click
            )
            lessons_wrapper.add_widget(lesson_button)

    def add_homework_lesson_button_click(self, button):
        disable = button.state != 'down'
        self.add_homework_toggle_next_button(disable)

    def add_homework_toggle_next_button(self, disable):
        self.root.ids.add_homework_next_btn.disabled = disable

    def add_lesson(self, lesson_id=None):
        title_field = self.root.ids.add_lesson_title
        top_toolbar = self.root.ids.add_lesson_top_toolbar
        grid_layout = self.root.ids.add_lesson_grid_layout

        week_num = self.get_active_week_num()
        year = self.get_active_year()
        day = self.get_current_tab_index('schedule')
        schedule_id = self.get_active_schedule_id()
        lesson = self.db.get_lesson(id=lesson_id, schedule_id=schedule_id) if lesson_id is not None else None

        title_field.text = '' if not lesson else lesson['name']
        title_field.focus = True

        for child in grid_layout.children:
            if type(child).__name__ == 'BoxLayout' and child.id == 'add_lesson_del_homeworks_layout':
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
                text=tr._('delete all related homeworks'),
                color=self.theme_cls.text_color
            )
            del_homeworks_wrapper.add_widget(del_chkbx)
            del_homeworks_wrapper.add_widget(del_chkbx_lbl)
            grid_layout.add_widget(del_homeworks_wrapper)

        def cb():
            self.open_schedule(schedule_id, day, week_num, year)
            self.clear_recent_history('add_lesson', 'schedule')

        top_toolbar.left_action_items = [['arrow-left', lambda x: self.go_back()]]
        top_toolbar.right_action_items = [['check', lambda x: self.save_lesson(cb=cb, schedule_id=schedule_id, lesson_id=lesson_id, day=day, title=title_field.text, del_homeworks=(del_chkbx.state == 'down' if del_chkbx is not None else False))]]
        lesson_mode = tr._("Edit") if lesson is not None else tr._("Add")
        week_days = self.week_days()
        top_toolbar.title = f'{lesson_mode} ' + tr._('Lesson for') + f' {week_days[day]}'
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
        time_dialog = LessonTimepicker(lesson_id=lesson_id, time_mode=mode)
        time_dialog.bind(time=self.save_lesson_time)

        lesson = self.db.get_lesson(id=lesson_id)
        lesson_time = lesson[mode]

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
        week_num = self.get_active_week_num()
        year = self.get_active_year()

        lesson = self.db.get_lesson(id=lesson_id)
        lesson[mode] = time_str
        time_start = time_str if mode == 'time_start' else None
        time_end = time_str if mode == 'time_end' else None

        if mode == 'time_start':
            if lesson['time_end'] == '':
                time_end = time_str
            else:
                if datetime.datetime.strptime(time_str, '%H:%M') > datetime.datetime.strptime(lesson['time_end'], '%H:%M'):
                    time_end = time_str
        elif mode == 'time_end':
            if lesson['time_start'] == '':
                time_start = time_str
            else:
                if datetime.datetime.strptime(time_str, '%H:%M') < datetime.datetime.strptime(lesson['time_start'], '%H:%M'):
                    time_end = lesson['time_start']

        if time_start is None:
            time_start = lesson['time_start']
        if time_end is None:
            time_end = lesson['time_end']

        day = lesson['day']
        self.db.update_lesson(id=lesson_id, time_start=time_start, time_end=time_end)
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
        self.db.update_setting('remind_homework_time', time_str)
        self.refresh_settings_notify_homework()

    def add_lesson_homework(self, lesson_id, schedule_id=None, week_num=None, year=None):
        if schedule_id is None:
            schedule_id = self.get_active_schedule_id()
        lesson = self.db.get_lesson(schedule_id=schedule_id, id=lesson_id)
        desc_field = self.root.ids.add_lesson_homework_desc_text
        top_toolbar = self.root.ids.add_lesson_homework_top_toolbar
        subtitle = self.root.ids.add_lesson_homework_subtitle
        notifiable_field = self.root.ids.add_lesson_homework_notifiable

        if week_num is None:
            week_num = self.get_active_week_num()
        if year is None:
            year = self.get_active_year()
        homework = self.db.find_homework(lesson_id=lesson_id, week_num=week_num, year=year)
        if homework is None:
            desc = ''
            notifiable = True
        elif homework is False:
            toast(f'warning: duplicated homeworks found. lesson_id: {lesson_id}, week_num: {week_num}, year: {year}')
            desc = ''
            notifiable = True
        else:
            desc = homework['desc']
            notifiable = homework['notifiable']

        desc_field.text = desc
        desc_field.focus = True

        notifiable_field.active = notifiable

        homework_id = None if homework is None else homework['id']
        done = 0 if homework is None else homework['done']
        notified = 0 if homework is None else homework['notified']
        day = lesson['day']
        date_str = Util.get_date_str(year, week_num, day)
        subtitle.text = f'{lesson["name"]} on {self.translate_date(date_str, "%a %d %b, %Y")}'

        top_toolbar.left_action_items = [[
            'arrow-left',
            lambda x: self.go_back()
        ]]

        def cb ():
            self.load_homeworks()
            if self.history[-1] == 'add_homework':
                self.clear_recent_history('add_homework')
                self.go_back()
            else:
                self.open_schedule(schedule_id, day, week_num, year)
                self.clear_recent_history('add_lesson_homework', 'schedule')

        top_toolbar.right_action_items = [[
            'check',
            lambda x: self.save_lesson_homework(
                id=homework_id,
                lesson_id=lesson_id,
                desc=desc_field.text,
                week_num=week_num,
                year=year,
                done=done,
                notified=notified,
                notifiable=int(notifiable_field.active),
                cb=cb
            )]]

        title = tr._('Add Task') if homework_id is None else tr._('Edit Task')
        top_toolbar.title = title

        self.switch_screen('add_lesson_homework')

    def save_lesson_homework(self, **kwargs):
        homework_id = kwargs['id']
        lesson_id = kwargs['lesson_id']
        desc = kwargs['desc']
        week_num = kwargs['week_num']
        year = kwargs['year']
        done = kwargs['done']
        notified = kwargs['notified']
        notifiable = kwargs['notifiable']

        if desc.strip() == '':
            if homework_id is not None:
                self.db.delete_homework(homework_id)
        else:
            text_limit = self.get_config_item('homework_desc_max_len')
            desc = desc[:text_limit]
            if homework_id is None:
                self.db.add_homework(lesson_id=lesson_id, desc=desc, week_num=week_num, year=year, notified=notified, done=done, notifiable=notifiable)
            else:
                self.db.update_homework(id=homework_id, desc=desc, notifiable=notifiable)
        if 'cb' in kwargs:
            kwargs['cb']()

    def clear_homework(self, lesson_id):
        schedule_id = self.get_active_schedule_id()
        lesson = self.db.get_lesson(schedule_id=schedule_id, id=lesson_id)
        day = lesson['day']
        week_num = self.get_active_week_num()
        year = self.get_active_year()
        homework = self.db.find_homework(lesson_id=lesson_id, week_num=week_num, year=year)
        if homework is False:
            toast(f'warning: duplicated homeworks found. lesson_id: {lesson_id}, week_num: {week_num}, year: {year}')
        elif homework is not None:
            self.db.delete_homework(homework['id'])
        self.open_schedule(schedule_id, day, week_num, year)

    def week_back(self):
        schedule_id = self.get_active_schedule_id()
        day = self.get_current_tab_index('schedule')
        week_num = self.get_active_week_num() - 1
        year = self.get_active_year()
        if week_num <= -1:
            week_num += 52
            year -= 1
        self.open_schedule(schedule_id, day, week_num, year)

    def week_next(self):
        schedule_id = self.get_active_schedule_id()
        day = self.get_current_tab_index('schedule')
        week_num = self.get_active_week_num() + 1
        year = self.get_active_year()
        if week_num >= 52:
            week_num -= 52
            year += 1
        self.open_schedule(schedule_id, day, week_num, year)

    def week_current(self):
        schedule_id = self.get_active_schedule_id()
        cur_day = Util.calc_day_num()
        self.open_schedule(schedule_id, cur_day)

    def get_week_date_range(self, **kwargs):
        year = datetime.datetime.today().year if 'year' not in kwargs else kwargs['year']
        week_num = self.get_active_week_num() if 'week_num' not in kwargs else kwargs['week_num']
        try:
            monday = datetime.datetime.strptime(f'{year}-W{week_num}-1', '%Y-W%W-%w').date()
            sunday = datetime.datetime.strptime(f'{year}-W{week_num}-0', '%Y-W%W-%w').date()
            monday_str = monday.strftime("%d %b")
            sunday_str = sunday.strftime("%d %b")
            return f'{self.translate_date(monday_str, "%d %b")} - {self.translate_date(sunday_str, "%d %b")}'
        except ValueError as err:
            toast(f'Oops! Invalid date format: {err}')
            return False

    def open_settings(self):
        self.refresh_settings()
        self.switch_screen('settings')

    def refresh_settings(self):
        self.refresh_theme_color_settings()
        self.refresh_theme_style_settings()
        self.refresh_lang_settings()
        self.refresh_settings_notify_homework()

    def refresh_theme_color_settings(self):
        self.reset_theme_color_settings()
        current_theme_color = self.db.get_setting('theme_color')
        widgets = ToggleButtonBehavior.get_widgets('theme_color')
        for w in widgets:
            if w.setting_value == current_theme_color:
                w.state = 'down'
        del widgets

    def refresh_theme_style_settings(self):
        self.reset_theme_style_settings()
        current_theme_style = self.db.get_setting('theme_style')
        widgets = ToggleButtonBehavior.get_widgets('theme_style')
        for w in widgets:
            if w.setting_value == current_theme_style:
                w.state = 'down'
        del widgets

    def refresh_lang_settings(self):
        self.reset_lang_settings()
        current_lang = self.db.get_setting('lang')
        widgets = ToggleButtonBehavior.get_widgets('lang')
        for w in widgets:
            if w.setting_value == current_lang:
                w.state = 'down'
        del widgets

    def refresh_settings_notify_homework(self):
        current_value = self.db.get_setting('remind_homework_time')
        control = self.root.ids.notify_select
        control.text = current_value

    def reset_theme_color_settings(self):
        widgets = ToggleButtonBehavior.get_widgets('theme_color')
        for w in widgets:
            w.state = 'normal'
        del widgets

    def reset_theme_style_settings(self):
        widgets = ToggleButtonBehavior.get_widgets('theme_style')
        for w in widgets:
            w.state = 'normal'
        del widgets

    def reset_lang_settings(self):
        widgets = ToggleButtonBehavior.get_widgets('lang')
        for w in widgets:
            w.state = 'normal'
        del widgets

    def set_theme_color(self, **kwargs):
        theme_color = self.db.get_setting('theme_color')
        self.theme_cls.primary_palette = theme_color
        if 'cb' in kwargs:
            kwargs['cb']()

    def set_theme_style(self, **kwargs):
        theme_style = self.db.get_setting('theme_style')
        self.theme_cls.theme_style = theme_style
        if 'cb' in kwargs:
            kwargs['cb']()

    def get_app_font(self):
        return 'Jura'

    def set_fonts(self):
        for font in KIVY_FONTS:
            LabelBase.register(**font)

        font_name = self.get_app_font()
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
        toolbars = [
            'start_top_toolbar',
            'settings_toolbar',
            'schedule_toolbar',
            'bottom_schedule_toolbar',
            'add_schedule_top_toolbar',
            'add_lesson_top_toolbar',
            'add_homework_top_toolbar',
            'add_lesson_homework_top_toolbar'
        ]
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

        # Add lesson homework screen
        add_lesson_homework_items = ['add_lesson_homework_subtitle', 'add_lesson_homework_reminder_label']
        for alh_item in add_lesson_homework_items:
            self.root.ids[alh_item].font_name = font_name



    def get_theme_color(self, palette, hue):
        return get_color_from_hex(colors[palette][hue])

    def get_tabs_color(self):
        return get_color_from_hex(colors[self.theme_cls.primary_palette]['700'])

    def on_schedule_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        week_days = self.week_days()
        schedule_id = self.get_active_schedule_id()
        schedule = self.db.get_schedule(schedule_id)
        day_index = None
        for i in week_days:
            if i.lower() == tab_text.lower():
                day_index = week_days.index(i)

        week_num = self.get_active_week_num()
        year = self.get_active_year()
        if week_num >= 52:
            week_num -= 52
            year += 1
        date_str = Util.get_date_str(year, week_num, day_index)
        self.root.ids.schedule_toolbar.title = f'{schedule["name"]} ({self.translate_date(date_str, "%a %d %b, %Y")})'

    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        pass

    def mark_homework(self, homework_id, checkbox):
        val = checkbox.state
        done = 1 if val == 'down' else 0
        self.db.update_homework(id=homework_id, done=done)
        self.load_homeworks()

    def do_notify(self, message_text):
        ticker = "Schedules Reminder"
        title = 'Schedules Notification'
        message = message_text
        kwargs = {'title': title, 'message': message, 'ticker': ticker}
        if platform == 'android':
            kwargs['app_icon'] = ''
            kwargs['toast'] = False
            noti = DroidNotification()
            noti._notify(**kwargs)
        else:
            notification.notify(**kwargs)

    def reset_active_states(self):
        self.reset_active_schedule_id()
        self.reset_active_week_num()
        self.reset_active_year()

    def switch_screen(self, screen):
        if self.root.current != screen:
            self.history.append(self.root.current)
        # Snackbar(text=f'Switch "{screen}". History::: ' + '->'.join(self.history)).open()
        self.root.current = screen

    def go_back(self):
        # index = 1 if self.root.current == 'add_homework' else 0
        # self.root.ids.start_tabs.ids.carousel.index = tab_index

        if len(self.history) == 0:
            Snackbar(text='Empty History!').open()
            return
        back_screen = self.history[-1]
        del self.history[-1]
        # Snackbar(text=f'Back to "{back_screen}". History::: ' + '->'.join(self.history)).open()
        if back_screen == 'start':
            self.reset_active_states()
        self.root.current = back_screen

    def clear_recent_history(self, *args):
        if len(args)>= len(self.history):
            toast('Clear History failed. History:::' + '->'.join(self.history)) + ' Requested to remove:::' + '->'.join(args)
        for screen in args:
            if screen == self.history[-1]:
                del self.history[-1]
            else:
                break

    def request_focus_for_main_view(self):
        if platform != 'android':
            return

        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        PythonActivity.requestFocusForMainView()

    def generate_demo_schedule(self):
        num = 1
        def cb():
            self.load_schedules()
            self.load_homeworks()
            self.go_back()
        self.create_demo_schedules(num, cb)

    def week_days(self):
        week_days = self.week_days_config()
        values = week_days.values()
        return list(values)

    @staticmethod
    def week_days_config():
        return {'Mon': tr._('Mon'), 'Tue': tr._('Tue'), 'Wed': tr._('Wed'), 'Thu': tr._('Thu'), 'Fri': tr._('Fri'), 'Sat': tr._('Sat'), 'Sun': tr._('Sun')}

    @staticmethod
    def months_config():
        return {'Jan': tr._('Jan'), 'Feb': tr._('Feb'), 'Mar': tr._('Mar'), 'Apr': tr._('Apr'), 'May': tr._('May'),
                'Jun': tr._('Jun'), 'Jul': tr._('Jul'), 'Aug': tr._('Aug'), 'Sep': tr._('Sep'), 'Oct': tr._('Oct'),
                'Nov': tr._('Nov'), 'Dec': tr._('Dec')}

    def translate_date(self, date_str, format=None):
        week_days = self.week_days_config()
        months = self.months_config()
        if format == '%a %d %b, %Y':
            day_name = date_str[:3]
            if day_name in week_days:
                date_str = date_str[:3].replace(day_name, week_days[day_name]) + date_str[3:]
            month_name = date_str[-9:-6]
            if month_name in months:
                date_str = date_str[:-9] + date_str[-9:-6].replace(month_name, months[month_name]) + date_str[-6:]
        elif format == '%d %b':
            month_name = date_str[-3:]
            if month_name in months:
                date_str = date_str[:-3] + date_str[-3:].replace(month_name, months[month_name])
        return date_str


db = Database()
lang = None
if db.table_exists('settings'):
    lang = db.get_setting('lang')
if lang is None:
    lang = SETTINGS_DEFAULTS[0]['val']
db.conn.close()

tr = Lang(lang)

MainApp().run()
