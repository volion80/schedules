import datetime


def calc_day_num(add=0):
    current = datetime.datetime.today().weekday()
    return current + add


def calc_week_num(add=0):
    current = int(datetime.datetime.today().strftime("%W"))
    return current + add


def calc_year(add=0):
    current = datetime.datetime.today().year
    return current + add
