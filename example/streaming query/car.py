"""
This example uses driver DB API.
In this example, a thread writes a huge list of data of car speed into database,
and another thread reads from the database to figure out which car is speeding.
"""
import datetime
import random
import threading
import time

from proton_driver import connect


def create_stream():
    with connect("proton://default:@localhost:8463/default") as conn:
        with conn.cursor() as cursor:
            cursor.execute("drop stream if exists cars")
            cursor.execute("create stream if not exists car(id int64, speed float64)")


def write_data(car_num: int):
    car_begin_date = datetime.datetime(2022, 1, 1, 1, 0, 0)
    for day in range(100):
        car_begin_date += datetime.timedelta(days=1)
        data = [(random.randint(0, car_num - 1), random.random() * 20 + 50,
                 car_begin_date
                 + datetime.timedelta(milliseconds=i * 100)) for i in range(300000)]
        with connect("proton://default:@localhost:8463/default") as conn:
            with conn.cursor() as cursor:
                cursor.executemany("insert into car (id, speed, _tp_time) values", data)
                print(f"row count: {cursor.rowcount}")
        time.sleep(10)


def query(conn):
    query_sql = """select id, avg(speed), window_start, window_end 
                from session(car, 1h, [speed >= 60, speed < 60)) 
                group by id, window_start, window_end"""
    cursor = conn.cursor()
    cursor.set_stream_results(stream_results=True, max_row_buffer=100)
    cursor.execute(query_sql)
    return cursor


def fetch_result(cursor):
    while True:
        print(cursor.fetchone())


def main():
    create_stream()
    conn = connect("proton://default:@localhost:8463/default")
    cursor = query(conn)
    threading.Thread(target=write_data, args=[7]).start()
    fetch_result(cursor)
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
