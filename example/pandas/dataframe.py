import pandas as pd
import time

from proton_driver import client, connect

if __name__ == "__main__":
    c = client.Client(host='127.0.0.1', port=8463)

    # setup the test stream
    c.execute("drop stream if exists test")
    c.execute(
        """create stream test (
                    year int16,
                    first_name string
                )"""
    )
    # add some data
    df = pd.DataFrame.from_records(
        [
            {'year': 1994, 'first_name': 'Vova'},
            {'year': 1995, 'first_name': 'Anja'},
            {'year': 1996, 'first_name': 'Vasja'},
            {'year': 1997, 'first_name': 'Petja'},
        ]
    )
    c.insert_dataframe(
        'INSERT INTO "test" (year, first_name) VALUES',
        df,
        settings=dict(use_numpy=True),
    )
    # or c.execute(
    #     "INSERT INTO test(year, first_name) VALUES", df.to_dict('records')
    # )
    # wait for 3 sec to make sure data available in historical store
    time.sleep(3)

    df = c.query_dataframe('SELECT * FROM table(test)')
    print(df)
    print(df.describe())

    # Also you can use proton settings in DataFrame API like using `execute` function. # noqa
    # Here's an example with idempotent id.

    # Reset stream
    c.execute('drop stream if exists test')
    c.execute(
        """create stream test (
                    year int16,
                    first_name string
                )"""
    )
    settings = dict(use_numpy=True, idempotent_id='batch')

    # Execute multiple insert operations.
    for _ in range(5):
        c.insert_dataframe(
            'INSERT INTO "test" (year, first_name) VALUES',
            df,
            settings=settings,
        )
    time.sleep(3)

    rv = c.execute('SELECT COUNT(*) FROM table(test)')
    # Only the first times insert into the historical storage.
    print(rv)  # (4,)

    # Converting query results to a variety of formats with dbapi
    with connect('proton://localhost') as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM table(test)')
            print('--------------Pandas DataFrame--------------')
            print(cur.df())

            cur.execute('SELECT * FROM table(test)')
            print('----------------Numpy Arrays----------------')
            print(cur.fetchnumpy())

            cur.execute('SELECT * FROM table(test)')
            print('--------------Polars DataFrame--------------')
            print(cur.pl())

            cur.execute('SELECT * FROM table(test)')
            print('-----------------Arrow Table----------------')
            print(cur.arrow())
