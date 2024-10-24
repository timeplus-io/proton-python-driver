from proton_driver import connect, Client
from datetime import date
from time import sleep


# Create a test stream
def create_test_stream(operator, table_name, table_columns):
    operator.execute(f'DROP STREAM IF EXISTS {table_name};')
    operator.execute(f'CREATE STREAM {table_name} ({table_columns})')


# Use dbapi to implement idempotent insertion
def use_dbapi():
    with connect('proton://localhost') as conn:
        with conn.cursor() as cur:
            create_test_stream(
                cur,
                'test_user',
                'id int32, name string, birthday date'
            )
            # Set idempotent_id.
            cur.set_settings(dict(idempotent_id='batch1'))
            # Insert data into test_user multiple times with the same idempotent_id. # noqa
            # The query result should contain only the first inserted data.
            data = [
                (123456, 'timeplus', date(2024, 10, 24)),
                (789012, 'stream  ', date(2023, 10, 24)),
                (135790, 'proton  ', date(2024, 10, 24)),
                (246801, 'database', date(2024, 10, 24)),
            ]
            # Execute multiple insert operations.
            for _ in range(10):
                cur.execute(
                    'INSERT INTO test_user (id, name, birthday) VALUES',
                    data
                )
                cur.fetchall()
            # wait for 3 sec to make sure data available in historical store.
            sleep(3)
            cur.execute('SELECT count() FROM table(test_user)')
            res = cur.fetchall()
            # Data is inserted only once,so res == (4,).
            print(res)


# Use Client to implement idempotent insertion
def use_client():
    cli = Client('localhost', 8463)
    create_test_stream(cli, 'test_stream', '`i` int,  `v` string')
    setting = {
        'idempotent_id': 'batch1'
    }
    data = [
        (1, 'a'), (2, 'b'), (3, 'c'), (4, 'd'),
        (5, 'e'), (6, 'f'), (7, 'g'), (8, 'h')
    ]
    # Execute multiple insert operations.
    for _ in range(10):
        cli.execute(
            'INSERT INTO test_stream (i, v) VALUES',
            data,
            settings=setting
        )
    # wait for 3 sec to make sure data available in historical store.
    sleep(3)
    res = cli.execute('SELECT count() FROM table(test_stream)')
    # Data is inserted only once,so res == (8,).
    print(res)


if __name__ == "__main__":
    use_dbapi()  # (4,)
    use_client()  # (8,)
