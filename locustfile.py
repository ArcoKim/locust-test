from locust import FastHttpUser, task, events
from faker import Faker
import pandas as pd
import random
import threading
import boto3
import os
import time

fake = Faker()

emp = pd.read_csv('data/employees.csv')
first_names = emp["first_name"].tolist()
last_names = emp["last_name"].tolist()

write_idx = 500000
read_idx = 0
index_lock = threading.Lock()

instance_list = []
ec2 = boto3.client("ec2", aws_access_key_id=os.getenv("access_key"), aws_secret_access_key=os.getenv("secret_access_key"), region_name="ap-northeast-2")
ssm = boto3.client("ssm")

def get_instance_count():
    response = ec2.describe_instances(Filters=[{"Name": "instance-state-name", "Values": ["running"]}])
    instances = sum(len(reservation["Instances"]) for reservation in response["Reservations"])
    return instances

class MonitorThread(threading.Thread):
    def __init__(self, interval=300):
        super().__init__()
        self.interval = interval
        self.running = True
    
    def run(self):
        while self.running:
            instance_count = get_instance_count()
            print(f"[Monitor] Running EC2 Instances: {instance_count}")
            instance_list.append(instance_count)
            time.sleep(self.interval)

    def stop(self):
        self.running = False

monitor_thread = None

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global monitor_thread
    monitor_thread = MonitorThread()
    monitor_thread.start()
    print("[Monitor] EC2 Instance Monitoring Started.")

@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    global monitor_thread
    if monitor_thread:
        monitor_thread.stop()
        monitor_thread.join()
        print("[Monitor] EC2 Instance Monitoring Stopped.")

    df = pd.DataFrame.from_records(instance_list)
    df.to_excel("instances.xlsx")

    s3 = boto3.client("s3")
    metrics = ["exceptions", "failures", "stats_history", "stats"]
    username = os.getenv("username")

    for metric in metrics:
        csv = f"{username}_{metric}.csv"
        s3.upload_file(csv, "student-monitoring", f"{username}/{csv}")
    s3.upload_file("instances.xlsx", "student-monitoring", f"{username}/instances.xlsx")

class TestUser(FastHttpUser):
    @task(2)
    def token(self):
        self.client.post("/v1/token?id=world&uuid=skills", json={"length": 2048}, name="/v1/token")

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
        }, name="/v1/employee")

        first_names.append(first_name)
        last_names.append(last_name)

    @task(2)
    def read_employee(self):
        global read_idx
        with index_lock:
            read_now = read_idx
            read_idx += 1

        self.client.get(f"/v1/employee?first_name={first_names[read_now]}&last_name={last_names[read_now]}&id=world&uuid=skills", name="/v1/employee")

    @task(1)
    def bad_token(self):
        self.client.post("/v1/employee?id=world&uuid=skills", json={
            "emp_no": 1,
            "birth_date": "2024-12-19",
            "first_name": "attack",
            "last_name": "bot",
            "gender": 'M',
            "hire_date": "2024-12-19"
        }, headers={"User-Agent": "bot-attack"}, name="abnormal")