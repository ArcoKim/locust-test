from locust import FastHttpUser, task
from faker import Faker
import pandas as pd
import random
import threading

fake = Faker()

emp = pd.read_csv('data/employees.csv')
first_names = emp["first_name"].tolist()
last_names = emp["last_name"].tolist()

write_idx = 500000
read_idx = 0
index_lock = threading.Lock()

class TestUser(FastHttpUser):
    @task(2)
    def token(self):
        self.client.post("/v1/token?id=world&uuid=skills", json={"length": 512})

    @task(2)
    def write_employee(self):
        global write_idx
        with index_lock:
            write_now = write_idx
            write_idx += 1

        birth_date = fake.date_of_birth()
        first_name = fake.first_name()
        last_name = fake.last_name()

        self.client.post("/v1/employee?id=world&uuid=skills", json={
            "emp_no": write_now,
            "birth_date": birth_date.isoformat(),
            "first_name": first_name,
            "last_name": last_name,
            "gender": random.choice(['M', 'F']),
            "hire_date": fake.date_between_dates(date_start=birth_date).isoformat()
        })

        first_names.append(first_name)
        last_names.append(last_name)

    @task(2)
    def read_employee(self):
        global read_idx
        with index_lock:
            read_now = read_idx
            read_idx += 1

        self.client.get(f"/v1/employee?first_name={first_names[read_now]}&last_name={last_names[read_now]}&id=world&uuid=skills")

    @task(1)
    def bad_token(self):
        self.client.post("/v1/employee?id=world&uuid=skills", json={
            "emp_no": 1,
            "birth_date": "2024-12-19",
            "first_name": "attack",
            "last_name": "bot",
            "gender": 'M',
            "hire_date": "2024-12-19"
        }, headers={"User-Agent": "bot-attack"})