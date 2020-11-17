import datetime
from kivymd.toast import toast


def log_time(func):
    def wrapper_log_time(app, *args, **kwargs):
        stime = datetime.datetime.now()
        func(app, *args, **kwargs)
        etime = datetime.datetime.now()
        diff = (etime - stime).total_seconds()
        toast(f'schedules loaded: {diff} sec')
    return wrapper_log_time
