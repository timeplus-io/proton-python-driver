Timeplus Proton Python Driver
================

Introduction
------------

`Proton <https://github.com/timeplus-io/proton>`_ is a unified streaming and historical data processing engine in a single binary. The historical store is built based on `ClickHouse <https://github.com/ClickHouse/ClickHouse>`_.

This project provides python driver to interact with Proton, the code is based on https://github.com/mymarilyn/clickhouse-driver.  


Installation
------------

.. code-block:: shell

   pip install proton-driver


Quick Start
------------

1. Run proton with docker, ``docker run -d -p 8463:8463 --pull always --name proton ghcr.io/timeplus-io/proton:develop``
2. Run python code 
.. code-block:: python

   from proton_driver import connect
   with connect("proton://default:@localhost:8463/default") as conn:
     with conn.cursor() as cursor:
       cursor.execute("select 1")
       print(cursor.fetchone())


Streaming Query
------------

.. code-block:: python

   from proton_driver import connect
   with connect("proton://default:@localhost:8463/default") as conn:
     with conn.cursor() as cursor:
       cursor.execute("select 1")


