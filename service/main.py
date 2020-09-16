"""
Roll polling service script.
Monitors the chain on regular basis and send notifications on change.
Also updates the App UI via OSC:
Service -> OscAppClient -> OscAppServer -> App
On Linux run with:
```sh
PYTHONPATH=src/
PYTHON_SERVICE_ARGUMENT='{"osc_server_port": PORT}'
./src/etherollapp/service/main.py
```
"""
import json
import os
from time import sleep, time
from datetime import datetime

from kivy.app import App
from kivy.utils import platform
from plyer import notification

from osc.osc_app_client import OscAppClient

# from .Settings import Settings
from Settings import Settings
from Model import Schedule, Homework
from Util import Util


class MyApp(App):

    @staticmethod
    def get_files_dir():
        """
        Alternative App._get_user_data_dir() implementation for Android
        that also works when within a service activity.
        """
        from jnius import autoclass, cast
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = PythonActivity.mActivity
        if activity is None:
            # assume we're running from the background service
            PythonService = autoclass('org.kivy.android.PythonService')
            activity = PythonService.mService
        context = cast('android.content.Context', activity)
        file_p = cast('java.io.File', context.getFilesDir())
        data_dir = file_p.getAbsolutePath()
        return data_dir

    def _get_user_data_dir(self):
        """
        Overrides the default `App._get_user_data_dir()` behavior on Android to
        also work with service activity.
        """
        if platform == 'android':
            return self.get_files_dir()
        return super()._get_user_data_dir()


class Service:

    def __init__(self, osc_server_port=None):
        """
        Set `osc_server_port` to enable UI synchronization with service.
        """
        self.last_notify = None
        self.osc_app_client = None
        if osc_server_port is not None:
            self.osc_app_client = OscAppClient('localhost', osc_server_port)
        # so that the `App._running_app` singleton is available

        self.Settings = None
        self.Schedule = None
        self.Homework = None

        if platform == 'android':
            MyApp()

    def run(self):
        """
        Blocking pull loop call.
        Service will stop after a period of time with no roll activity.
        """
        self.last_notify = datetime.now()
        while True:
            self.check_homework_notify()
            # self.check_notify()
            sleep(5)
        # service decided to die naturally after no roll activity
        self.set_auto_restart_service(False)

    @staticmethod
    def set_auto_restart_service(restart=True):
        """
        Makes sure the service restarts automatically on Android when killed.
        """
        if platform != 'android':
            return
        from jnius import autoclass
        PythonService = autoclass('org.kivy.android.PythonService')
        PythonService.mService.setAutoRestartService(restart)

    def check_notify(self):
        now = datetime.now()
        dt = now - self.last_notify

        if dt.seconds > 10:
            self.last_notify = now
            t = now.strftime("%m/%d/%Y, %H:%M:%S")
            self.do_notify(t)

    def check_homework_notify(self):
        self.Settings = Settings()
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        notify_time = self.Settings.get('notify')['homework']
        if current_time == notify_time:
            tomorrow = Util.calc_day_num(1)
            week_num = Util.calc_week_num()
            year = Util.calc_year()

            self.Schedule = Schedule(table='schedules')
            self.Homework = Homework(table='homeworks')
            schedules = self.Schedule.all()
            for schedule_id in schedules:
                schedule = self.Schedule.get(schedule_id)
                day_lessons = list(filter(lambda d: d['day'] == tomorrow, schedule['lessons']))
                for lesson in day_lessons:
                    homeworks = self.Homework.all()
                    hw = list(homeworks.find(week_num=week_num, lesson_id=lesson['id'], year=year, notified=0))
                    if len(hw) == 1:
                        hw_id = hw[0][0]
                        hw_info = hw[0][1]
                        notify_text = f'Homework for tomorrow: {lesson["name"]} - {hw_info["desc"]}'
                        self.do_notify(notify_text)
                        self.Homework.save(hw_id, lesson_id=lesson['id'], desc=hw_info["desc"], week_num=week_num,
                                           year=year, notified=1)

    def do_notify(self, message_text):
        """
        Also notifies the app process via OSC.
        """
        ticker = "Ticker"
        title = 'Schedules Notification'
        message = message_text
        kwargs = {'title': title, 'message': message, 'ticker': ticker}
        if self.osc_app_client is not None:
            self.osc_app_client.send_refresh()
        notification.notify(**kwargs)


def main():
    argument = os.environ.get('PYTHON_SERVICE_ARGUMENT', 'null')
    argument = json.loads(argument)
    argument = argument or {}
    osc_server_port = argument.get('osc_server_port')
    service = Service(osc_server_port)
    try:
        service.set_auto_restart_service()
        service.run()
    except Exception:
        # avoid auto-restart loop
        service.set_auto_restart_service(False)


if __name__ == '__main__':
    main()
