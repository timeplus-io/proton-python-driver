Timeplus Proton Python Driver
=============================

Introduction
------------

`Proton <https://github.com/timeplus-io/proton>`_ is a unified streaming and historical data processing engine in a single binary. The historical store is built based on `ClickHouse <https://github.com/ClickHouse/ClickHouse>`_.

This project provides python driver to interact with Proton, the code is based on https://github.com/mymarilyn/clickhouse-driver.  


Installation
------------
Proton Python Driver currently supports the following versions of Python: 3.8, 3.9, 3.10, 3.11 and 3.12.

Installing with pip
We recommend creating a virtual environment when installing Python dependencies. For more information on setting up a virtual environment, see the `Python documentation <https://docs.python.org/3.9/tutorial/venv.html>`_.

.. code-block:: shell

   pip install proton-driver


Quick Start
------------

1. Run proton with docker. Make sure the port 8463 is exposed.

.. code-block:: shell

  docker run -d -p 8463:8463 --pull always --name proton ghcr.io/timeplus-io/proton:latest

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
