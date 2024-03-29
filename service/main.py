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
from Util import Util
from Database import Database
if platform == 'android':
    from DroidNotification import DroidNotification


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
        # Set `osc_server_port` to enable UI synchronization with service.
        self.osc_app_client = None
        if osc_server_port is not None:
            self.osc_app_client = OscAppClient('localhost', osc_server_port)
        # so that the `App._running_app` singleton is available
        self.db = Database()

        if platform == 'android':
            MyApp()

    def run(self):
        while True:
            self.check_homework_notify()
            sleep(10)
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

    def check_homework_notify(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        notify_time = self.db.get_setting('remind_homework_time')
        if current_time == notify_time:
            add_week = 0
            add_year = 0
            day = Util.calc_day_num(1)
            if day == 7:
                day = 0
                add_week = 1
            week_num = Util.calc_week_num(add_week)
            if week_num >= 52:
                week_num -= 52
                add_year = 1
            year = Util.calc_year(add_year)

            homeworks = self.db.get_homeworks(year=year, week_num=week_num, day=day, notified=0, done=0, notifiable=1)
            if len(homeworks):
                homework = homeworks[0]
                notify_text = f'You have a task for tomorrow: {homework["lesson_name"]} - {homework["desc"]}'
                self.do_notify(notify_text)
                self.db.update_homework(id=homework['id'], notified=1)

    def do_notify(self, message_text):
        """
        Also notifies the app process via OSC.
        """
        ticker = "Task Reminder"
        title = 'Schedules Notification'
        message = message_text
        kwargs = {'title': title, 'message': message, 'ticker': ticker}
        if self.osc_app_client is not None:
            self.osc_app_client.send_refresh()
        if platform == 'android':
            kwargs['app_icon'] = ''
            kwargs['toast'] = False
            noti = DroidNotification()
            noti._notify(**kwargs)
        else:
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
        service.set_auto_restart_service(False)


if __name__ == '__main__':
    main()
