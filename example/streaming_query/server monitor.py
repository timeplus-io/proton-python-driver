"""
This example uses basic classes of the driver: Client
In this example, a few servers upload their logs of statue (include cpu, memory and disk usage,
generate randomly) detected every 100ms to the database every 10 logs generated.
The main thread will warn if any usage exceeds 95%.
"""
import random
import threading
import time
from datetime import datetime

from proton_driver import client


class Server(threading.Thread):
    def __init__(self, name: str, buffer_max_size: int = 10):
        threading.Thread.__init__(self)
        self.name = name
        self.buffer = []
        self.buffer_max_size = buffer_max_size
        self.client = None
        self.killed = False

    def __get_state(self) -> dict:
        return {
            "cpu": random.randint(0, 100),
            "memory": random.randint(0, 100),
            "disk": random.randint(0, 100),
            "server_name": self.name,
            "timestamp": datetime.now()
        }

    def __send_data(self):
        self.client.execute(
            "insert into server_monitor (cpu, memory, disk, server_name, timestamp) values",
            self.buffer
        )

    def run(self) -> None:
        self.client = client.Client(host='127.0.0.1', port=8463)
        while not self.killed:
            self.buffer.append(self.__get_state())
            if len(self.buffer) >= self.buffer_max_size:
                self.__send_data()
                self.buffer = []
            time.sleep(0.1)
        self.client.disconnect()
        self.client = None


def initial_stream():
    c = client.Client(host='127.0.0.1', port=8463)
    c.execute("drop stream if exists server_monitor")
    c.execute("""create stream server_monitor (
                    cpu float,
                    memory float,
                    disk float,
                    server_name string,
                    timestamp datetime64(3) default now64(3)
                )""")


def show():
    c = client.Client(host='127.0.0.1', port=8463)
    limit = 95
    rows = c.execute_iter(
        "select cpu, memory, disk, server_name, timestamp from server_monitor "
        "where cpu > %(limit)f or memory > %(limit)f or disk > %(limit)f",
        {"limit": limit}
    )
    for row in rows:
        msg = f"{row[4].strftime('%d-%m-%Y %H:%M:%S')} WARNING server[{row[3]}]:"
        col_names = ["cpu", "memory", "disk"]
        for col_name, usage in zip(col_names, row[:3]):
            if usage > limit:
                msg += " %s[%.2f%%]" % (col_name, usage)
        print(msg)


if __name__ == "__main__":
    initial_stream()
    servers = [Server(f"server_{i}") for i in range(7)]
    for server in servers:
        server.start()
    show()
