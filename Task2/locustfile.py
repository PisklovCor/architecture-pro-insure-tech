from locust import HttpUser, constant, task


class WebsiteUser(HttpUser):
    host = "http://127.0.0.1:50769"
    wait_time = constant(0.05)

    @task
    def index(self):
        self.client.get("/")

    @task(3)  # Этот запрос будет выполняться в 3 раза чаще
    def index_heavy(self):
        self.client.get("/")
