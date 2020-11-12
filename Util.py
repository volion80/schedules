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

    @staticmethod
    def get_date(year, week_num, day_index):
        day = day_index + 1
        if day == 7:
            day = 0
        return datetime.datetime.strptime(f'{year}-W{week_num}-{day}', '%Y-W%W-%w').date()

    @staticmethod
    def get_date_str(year, week_num, day_index):
        date = Util.get_date(year, week_num, day_index)
        return f'{date.strftime("%a %d %b, %Y")}'
