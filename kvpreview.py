from kivy.lang import Builder

from kivymd.app import MDApp

KV = '''
#:import KivyLexer kivy.extras.highlight.KivyLexer
#:import HotReloadViewer kivymd.utils.hot_reload_viewer.HotReloadViewer


BoxLayout:

    CodeInput:
        lexer: KivyLexer()
        style_name: "default"
        on_text: app.update_kv_file(self.text)
        size_hint_x: .1

    HotReloadViewer:
        size_hint_x: .9
        path: app.path_to_kv_file
        errors: True
        errors_text_color: 1, 1, 0, 1
        errors_background_color: app.theme_cls.bg_dark
'''


class Example(MDApp):
    path_to_kv_file = "test1.kv"

    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_string(KV)

    def update_kv_file(self, text):
        with open(self.path_to_kv_file, "a") as kv_file:
            kv_file.write(text)


Example().run()