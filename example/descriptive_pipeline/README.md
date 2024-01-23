# Descriptive Pipeline

In this sample, we leverage following open source components to build a descriptive streaming SQL based pipeline, and exposed the query result as WebSocket or http stream API endpoint.

- FastAPI
- Proton


## quick start

to run this sample, you need `python`

1. run `pip install -r requirements.txt` to install all the dependencies
2. run `docker run -d -p 8463:8463 --pull always --name proton ghcr.io/timeplus-io/proton:latest` to start a proton docker instance, with port `8643` exposed, the python driver will use this port
3. configure your streaming pipeline in [config.yaml](config.yaml)
4. run `uvicorn server.main:app --port 5001 --host 0.0.0.0 --http h11 --reload` to start the server which will be hosting the sql pipeline using FastAPI and expose WebSocket and HTTP stream api endpoint
5. run `wscat -c ws://localhost:5001/queries/<pipeline_name>` to consume the WebSocket streaming result from the pipeline
6. run `curl http://localhost:5001/queries/<pipeline_name>` to consume the HTTP stream result from the pipeline

## pipeline description

you can configure your pipeline in format of yaml, here is the sample pipeline for your reference.

```yaml
pipelines:
  - name: pipeline1
    sqls:
      - |
        CREATE RANDOM STREAM IF NOT EXISTS devices(
          device string default 'device'||to_string(rand()%4), 
          temperature float default rand()%1000/10
        )
      - |
        SELECT * FROM devices
  - name: pipeline2
    sqls:
      - |
        CREATE RANDOM STREAM IF NOT EXISTS devices(
          device string default 'device'||to_string(rand()%4), 
          temperature float default rand()%1000/10
        )
      - |
        SELECT 
          window_start, 
          count(*) as count 
        FROM 
          tumble(devices, 1s) 
        GROUP BY 
          window_start
  - name: pipeline3
    sqls:
      - |
        SELECT 1
```

1. you can define multiple pipelines
2. each pipeline has a unqiue name, this name will be used in the url of WebScoket or HTTP stream endpoint to identify which pipeline to consume
3. pipeline execution is triggerred by API call
4. each pipeline contains a list of SQL queries to run, you can call DDL create streams, external streams, views, materialized views and query in your pipeline, the last query and only the last query should be the query that return streaming or historical query result.

in the above case, we defined 3 pipelines

- pipeline1 : create a random stream -> run a streaming query to tail all data on that stream
- pipeline2 : create a random stream -> run a tumble window to caculate the count of event in each window
- pipeline3 : run a historical query `select 1` which is usually used to quick test if the SQL is working or not


## streaming result

In this sample, all query results are returned in lines of json object. for example:


Websocket:

```shell
wscat -c ws://localhost:5001/queries/pipeline1      
Connected (press CTRL+C to quit)
< {'device': 'device1', 'temperature': 16.899999618530273, '_tp_time': '2024-01-23 02:50:37.798000+00:00'}
< {'device': 'device2', 'temperature': 55.0, '_tp_time': '2024-01-23 02:50:37.798000+00:00'}
< {'device': 'device2', 'temperature': 33.0, '_tp_time': '2024-01-23 02:50:37.798000+00:00'}
< {'device': 'device3', 'temperature': 59.900001525878906, '_tp_time': '2024-01-23 02:50:37.798000+00:00'}
< {'device': 'device0', 'temperature': 92.0, '_tp_time': '2024-01-23 02:50:37.798000+00:00'}
< {'device': 'device1', 'temperature': 11.699999809265137, '_tp_time': '2024-01-23 02:50:37.803000+00:00'}
< {'device': 'device2', 'temperature': 23.399999618530273, '_tp_time': '2024-01-23 02:50:37.803000+00:00'}
< {'device': 'device3', 'temperature': 37.900001525878906, '_tp_time': '2024-01-23 02:50:37.803000+00:00'}
< {'device': 'device1', 'temperature': 77.69999694824219, '_tp_time': '2024-01-23 02:50:37.803000+00:00'}
< {'device': 'device3', 'temperature': 13.899999618530273, '_tp_time': '2024-01-23 02:50:37.803000+00:00'}
< {'device': 'device2', 'temperature': 84.19999694824219, '_tp_time': '2024-01-23 02:50:37.808000+00:00'}

```

HTTP stream:

```shell
curl http://localhost:5001/queries/pipeline2
{"window_start": "2024-01-23 02:52:07+00:00", "count": 580}
{"window_start": "2024-01-23 02:52:08+00:00", "count": 1000}
{"window_start": "2024-01-23 02:52:09+00:00", "count": 1000}
```