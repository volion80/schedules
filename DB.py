from kivy.storage.jsonstore import JsonStore


class DB:
    def __init__(self, **kwargs):
        self.store = JsonStore(f'{kwargs["table"]}.json')

    def all(self):
        return self.store

    def get(self, key):
        return self.store.get(key)

    def clear(self):
        self.store.clear()

    def save(self, key, **values):
        self.store.put(key, **values)

    def delete(self, key):
        self.store.delete(key)

    def exists(self, key):
        return self.store.exists(key)
