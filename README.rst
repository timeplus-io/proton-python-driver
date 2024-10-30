Timeplus Python Driver
=============================

Introduction
------------

`Timeplus <https://github.com/timeplus-io/proton>`_ is a unified streaming and historical data processing engine in a single binary.

This project provides python driver to interact with Timeplus Proton or Timeplus Enterprise, the code is based on https://github.com/mymarilyn/clickhouse-driver.  


Installation
------------
Timeplus Python Driver currently supports the following versions of Python: 3.8, 3.9, 3.10, 3.11, 3.12 and 3.13.

Installing with pip
We recommend creating a virtual environment when installing Python dependencies. For more information on setting up a virtual environment, see the `Python documentation <https://docs.python.org/3.9/tutorial/venv.html>`_.

.. code-block:: shell

   pip install proton-driver --extra-index-url https://d.timeplus.com/simple/


Quick Start
------------

1. Run Timeplus Proton with docker. Make sure the port 8463 is exposed.

.. code-block:: shell

  docker run -d -p 8463:8463 --pull always --name proton d.timeplus.com/timeplus-io/proton:latest

2. Run following python code 

.. code-block:: python

   from proton_driver import connect
   with connect("proton://default:@localhost:8463/default") as conn:
     with conn.cursor() as cursor:
       cursor.execute("select 1")
       print(cursor.fetchone())

above code should return ``(1,)`` , which shows that everything is working fine now.

Streaming Query
----------------

.. code-block:: python

  from proton_driver import client

  c = client.Client(host='127.0.0.1', port=8463)

  # create a random stream if not exist
  c.execute("CREATE RANDOM STREAM IF NOT EXISTS"
            " devices("
            " device string default 'device'||to_string(rand()%4), "
            " temperature float default rand()%1000/10"
            ")")
  # query the stream and return in a iterator
  rows = c.execute_iter(
      "SELECT device, count(*), min(temperature), max(temperature) "
      "FROM devices GROUP BY device",
  )
  for row in rows:
      print(row)


the output of the code will be something like following, as for streaming query is unbounded, you can add your flow control to terminate the loop.

.. code-block:: shell

  ('device0', 747, 0.0, 99.5999984741211)
  ('device1', 723, 0.10000000149011612, 99.30000305175781)
  ('device3', 768, 0.30000001192092896, 99.9000015258789)
  ('device2', 762, 0.20000000298023224, 99.80000305175781)
  ('device0', 1258, 0.0, 99.5999984741211)
  ('device1', 1216, 0.10000000149011612, 99.69999694824219)
  ('device3', 1276, 0.30000001192092896, 99.9000015258789)
  ('device2', 1250, 0.20000000298023224, 99.80000305175781)

Insert Data
------------
.. code-block:: python

  from proton_driver import client

  c = client.Client(host='127.0.0.1', port=8463)

  # create a random stream if not exist
  c.execute("INSERT INTO proton_stream (raw) VALUES",rows) #rows is an array of arrays

Pandas DataFrame
----------------
Big fan of Pandas? We too! You can mix SQL and Pandas API together. Also you can converting query results to a variety of formats(e.g. Numpy Array, Pandas DataFrame, Polars DataFrame, Arrow Table) by DBAPI.


.. code-block:: python

   import pandas as pd
   import time
   
   from proton_driver import client
   
   if __name__ == "__main__":
       c = client.Client(host='127.0.0.1', port=8463)
   
       # setup the test stream
       c.execute("drop stream if exists test")
       c.execute("""create stream test (
                       year int16,
                       first_name string
                   )""")
       # add some data
       df = pd.DataFrame.from_records([
           {'year': 1994, 'first_name': 'Vova'},
           {'year': 1995, 'first_name': 'Anja'},
           {'year': 1996, 'first_name': 'Vasja'},
           {'year': 1997, 'first_name': 'Petja'},
       ])
       c.insert_dataframe(
           'INSERT INTO "test" (year, first_name) VALUES',
           df,
           settings=dict(use_numpy=True),
       )
       # or c.execute("INSERT INTO test(year, first_name) VALUES", df.to_dict('records'))
       time.sleep(3) # wait for 3 sec to make sure data available in historical store
   
       df = c.query_dataframe('SELECT * FROM table(test)')
       print(df)
       print(df.describe())

       # Converting query results to a variety of formats with dbapi
       with connect('proton://localhost') as conn:
           with conn.cursor() as cur:
               cur.execute('SELECT * FROM table(test)')
               print(cur.df()) # Pandas DataFrame

               cur.execute('SELECT * FROM table(test)')
               print(cur.fetchnumpy()) # Numpy Arrays

               cur.execute('SELECT * FROM table(test)')
               print(cur.pl()) # Polars DataFrame

               cur.execute('SELECT * FROM table(test)')
               print(cur.arrow()) # Arrow Table