import datetime


class Util:

    @staticmethod
    def calc_day_num(add=0):
        current = datetime.datetime.today().weekday()
        return current + add

    @staticmethod
    def calc_week_num(add=0):
        current = int(datetime.datetime.today().strftime("%W"))
        return current + add

    @staticmethod
    def calc_year(add=0):
        current = datetime.datetime.today().year
        return current + add

    @staticmethod
    def clear_list_items(mdlist):
        mdlist.clear_widgets(mdlist.children)
