import json

from kivy.utils import platform
from time import sleep


# def start_service(arguments=None):
#     """
#     Starts service.
#     If the service is already running, it won't be started twice.
#     """
#     if platform != 'android':
#         return
#
#     from jnius import autoclass
#     package_name = 'schedules'
#     package_domain = 'org.test'
#     service_name = 'service'
#     service_class = '{}.{}.Service{}'.format(package_domain, package_name, service_name.title())
#     service = autoclass(service_class)
#     mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
#     argument = json.dumps(arguments)
#     service.start(mActivity, argument)

def start_service(arguments=None):
    """
    Starts service.
    If the service is already running, it won't be started twice.
    """
    if platform == 'android':
        from jnius import autoclass
        package_name = 'schedules'
        package_domain = 'org.test'
        service_name = 'service'
        service_class = '{}.{}.Service{}'.format(package_domain, package_name, service_name.title())
        service = autoclass(service_class)
        mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
        argument = json.dumps(arguments)
        # service.start(mActivity, argument, 'true')
        service.start(mActivity, argument)
    elif platform in ('linux', 'linux2', 'macos', 'win'):
        from runpy import run_path
        from threading import Thread
        service = Thread(
            target=run_path,
            args=['service/main.py'],
            kwargs={'run_name': '__main__'},
            daemon=True
        )
        service.start()
    else:
        return
