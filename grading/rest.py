from urllib.parse import urljoin
from time import sleep

from requests import Session


class RestSession(Session):
    BASE_URL = None
    SLEEP_TIME = 0.2

    def get(self, path, *args, **kwargs):
        sleep(self.SLEEP_TIME)
        path = urljoin(self.BASE_URL, path)
        return super().get(path, *args, **kwargs)

    def post(self, path, *args, **kwargs):
        sleep(self.SLEEP_TIME)
        path = urljoin(self.BASE_URL, path)
        return super().post(path, *args, **kwargs)

    def delete(self, path, *args, **kwargs):
        sleep(self.SLEEP_TIME)
        path = urljoin(self.BASE_URL, path)
        return super().delete(path, *args, **kwargs)
