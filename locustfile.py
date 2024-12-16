from locust import FastHttpUser, task
from faker import Faker
import random

fake = Faker()

class TestUser(FastHttpUser):
    write_num = 500000

    @task
    def token(self):
        self.client.post("/v1/token", json={"length": 256})

    @task
    def employee(self):
        birth_date = fake.date_of_birth()
        self.client.post("/v1/employee", json={
            "emp_no": self.write_num,
            "birth_date": birth_date.isoformat(),
            "first_name": fake.first_name(),
            "last_name": fake.last_name,
            "gender": random.choice('M', 'F'),
            "hire_date": fake.date_between_dates(date_start=birth_date)
        })
        self.write_num += 1
        self.client.get("/v1/employee?first_name=dump1&last_name=dump1")