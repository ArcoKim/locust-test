from locust import FastHttpUser, task
from faker import Faker
import pandas as pd
import random

fake = Faker()

emp = pd.read_csv('data/employees.csv')
first_names = emp["first_name"].tolist()
last_names = emp["last_name"].tolist()

class TestUser(FastHttpUser):
    write_num = 500000
    read_num = 0

    @task
    def token(self):
        self.client.post("/v1/token?id=world&uuid=skills", json={"length": 256})

    @task
    def employee(self):
        birth_date = fake.date_of_birth()
        first_name = fake.first_name()
        last_name = fake.last_name()

        self.client.post("/v1/employee?id=world&uuid=skills", json={
            "emp_no": self.write_num,
            "birth_date": birth_date.isoformat(),
            "first_name": first_name,
            "last_name": last_name,
            "gender": random.choice('M', 'F'),
            "hire_date": fake.date_between_dates(date_start=birth_date)
        })

        first_names.append(first_name)
        last_names.append(last_name)
        self.write_num += 1

        self.client.get(f"/v1/employee?first_name={first_names[self.read_num]}&last_name={last_names[self.read_num]}&id=world&uuid=skills")
        self.read_num += 1