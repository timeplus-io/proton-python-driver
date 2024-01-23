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


## performance

this sample is not targeting to provide a high throughput streaming processing pipeline, there is no performance tuning on the code, but there is a k6 test you can run to understand the overall performance of this sample code.

goto `test` folder and run `k6 run script.js` which will show some basic performance of the service.


### WebSocket

```bash
k6 run script_ws.js

          /\      |‾‾| /‾‾/   /‾‾/   
     /\  /  \     |  |/  /   /  /    
    /  \/    \    |     (   /   ‾‾\  
   /          \   |  |\  \ |  (‾)  | 
  / __________ \  |__| \__\ \_____/ .io

  execution: local
     script: script_ws.js
     output: -

  scenarios: (100.00%) 1 scenario, 1 max VUs, 1m0s max duration (incl. graceful stop):
           * default: 1 looping VUs for 30s (gracefulStop: 30s)

INFO[0000] connected                                     source=console
INFO[0030] 2 seconds passed, closing the socket          source=console
INFO[0030] disconnected                                  source=console

     ✓ status is 101

     checks................: 100.00% ✓ 1                   ✗ 0  
     data_received.........: 255 MB  8.5 MB/s
     data_sent.............: 228 B   7.595046004659361 B/s
     iteration_duration....: avg=30.01s  min=30.01s  med=30.01s  max=30.01s  p(90)=30.01s  p(95)=30.01s 
     iterations............: 1       0.033312/s
     vus...................: 1       min=1                 max=1
     vus_max...............: 1       min=1                 max=1
     ws_connecting.........: avg=17.56ms min=17.56ms med=17.56ms max=17.56ms p(90)=17.56ms p(95)=17.56ms
     ws_msgs_received......: 2490462 82961.287118/s
     ws_session_duration...: avg=30.01s  min=30.01s  med=30.01s  max=30.01s  p(90)=30.01s  p(95)=30.01s 
     ws_sessions...........: 1       0.033312/s


running (0m30.0s), 0/1 VUs, 1 complete and 0 interrupted iterations
default ✓ [======================================] 1 VUs  30s
```

### HTTP stream

```bash
k6 run script.js   

          /\      |‾‾| /‾‾/   /‾‾/   
     /\  /  \     |  |/  /   /  /    
    /  \/    \    |     (   /   ‾‾\  
   /          \   |  |\  \ |  (‾)  | 
  / __________ \  |__| \__\ \_____/ .io

  execution: local
     script: script.js
     output: -

  scenarios: (100.00%) 1 scenario, 1 max VUs, 1m0s max duration (incl. graceful stop):
           * default: 1 looping VUs for 30s (gracefulStop: 30s)

WARN[0030] Request Failed                                error="request timeout"

     data_received..............: 320 MB  10 MB/s
     data_sent..................: 97 B    3.121977997715227 B/s
     http_req_blocked...........: avg=2.08ms min=2.08ms med=2.08ms max=2.08ms p(90)=2.08ms p(95)=2.08ms
     http_req_connecting........: avg=247µs  min=247µs  med=247µs  max=247µs  p(90)=247µs  p(95)=247µs 
     http_req_duration..........: avg=30.06s min=30.06s med=30.06s max=30.06s p(90)=30.06s p(95)=30.06s
     http_req_failed............: 100.00% ✓ 1                   ✗ 0  
     http_req_receiving.........: avg=30.04s min=30.04s med=30.04s max=30.04s p(90)=30.04s p(95)=30.04s
     http_req_sending...........: avg=104µs  min=104µs  med=104µs  max=104µs  p(90)=104µs  p(95)=104µs 
     http_req_tls_handshaking...: avg=0s     min=0s     med=0s     max=0s     p(90)=0s     p(95)=0s    
     http_req_waiting...........: avg=18ms   min=18ms   med=18ms   max=18ms   p(90)=18ms   p(95)=18ms  
     http_reqs..................: 1       0.032185/s
     iteration_duration.........: avg=31.06s min=31.06s med=31.06s max=31.06s p(90)=31.06s p(95)=31.06s
     iterations.................: 1       0.032185/s
     vus........................: 1       min=1                 max=1
     vus_max....................: 1       min=1                 max=1


running (0m31.1s), 0/1 VUs, 1 complete and 0 interrupted iterations
default ✓ [======================================] 1 VUs  30s
```

without any performance tuning, the service can provide 10M/s or about 100000 eps in a macbook pro with m2pro cpu. 
