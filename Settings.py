from kivy.storage.jsonstore import JsonStore


class Settings:
    def __init__(self, **kwargs):
        self.store = JsonStore('settings.json')

    def get(self, key):
        return self.store.get(key)

    def save(self, key, **values):
        self.store.put(key, **values)

    def exists(self, key):
        return self.store.exists(key)
