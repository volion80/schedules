from kivymd.toast.kivytoast.kivytoast import Toast

class ScheduleToast(Toast):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.2}

def schedule_toast(text: str, duration=2.5):
    ScheduleToast(duration=duration).toast(text)