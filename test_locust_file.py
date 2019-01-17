from locust import HttpLocust, TaskSet, task
import requests
import random


class UserBehavior(TaskSet):
    fullURL = 'http://localhost:5555/'

    def on_start(self):
        """ on_start is called when a Locust start before any task is scheduled """
        self.login()

    def on_stop(self):
        """ on_stop is called when the TaskSet is stopping """
        self.logout()

    def login(self):
        res = self.client.get('login')
        if res.ok:
            print(res.content)

    def logout(self):
        res = self.client.get('logout')
        if res.ok:
            print(res.content)
        res = self.client.get('test/version')
        if res.ok:
            print(res.content)

    @task(1)
    def profile(self):
        res = self.client.post("test/update")
        if res.ok:
            print(res.content)

    @task(2)
    def index(self):
        res = self.client.get("test/count")
        if res.ok:
            print(res.content)


class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    host = 'http://localhost:5555/'
    # wait_function = lambda self: random.expovariate(1) * 1000
    min_wait = 1000
    max_wait = 2000
