# Example to Integrate Bytewax and Proton together
[proton.py](https://github.com/timeplus-io/proton-python-driver/blob/develop/example/bytewax/proton.py) is a Bytewax sink for [Timeplus Proton](https://github.com/timeplus-io/proton) streaming SQL engine.

Inspired by https://bytewax.io/blog/polling-hacker-news, you can call Hacker News HTTP API with Bytewax and send latest news to Proton for SQL-based analysis, such as

```sql
select * from story
```

## Run with Docker Compose (Highly Recommended)

Simply run `docker compose up` in this folder and it will start

1. A Proton instance with pre-configured streams, materialized views and views.
2. A container that leverages Bytewax to call Hacker News API and send data to Proton.
3. A pre-configured Grafana instance to visualize the live data.

## Run without Docker

```shell
python3.10 -m venv py310-env
source py310-env/bin/activate
#git clone and cd to this proton-python-driver/example/bytewax folder
pip install -r requirements.txt

python -m bytewax.run hackernews.py -w 5
```

It will start bytewax with 5 workers and load new items every 15 seconds and send the data to Proton.

## How it works

When the Proton server is started, we create 2 streams to receive the raw JSON data pushed from Bytewax.

```sql
CREATE STREAM hn_stories_raw(raw string);
CREATE STREAM hn_comments_raw(raw string);
```

Then we create 2 materialized view to extract the key information from the JSON and put into more meaningful columns:

```sql
CREATE MATERIALIZED VIEW hn_stories AS
  SELECT to_time(raw:time) AS _tp_time,raw:id::int AS id,raw:title AS title,raw:by AS by, raw FROM hn_stories_raw;
CREATE MATERIALIZED VIEW hn_comments AS
  SELECT to_time(raw:time) AS _tp_time,raw:id::int AS id,raw:root_id::int AS root_id,raw:by AS by, raw FROM hn_comments_raw;
```

Finally we create 2 views to load both incoming data and existin data:

```sql
CREATE VIEW IF NOT EXISTS story AS SELECT * FROM hn_stories WHERE _tp_time>earliest_ts();
CREATE VIEW IF NOT EXISTS comment AS SELECT * FROM hn_comments WHERE _tp_time>earliest_ts()
```

With all those streams and views, you can query the data in whatever ways, e.g.

```sql
select * from comment;

select 
    story._tp_time as story_time,comment._tp_time as comment_time,
    story.id as story_id, comment.id as comment_id,
    substring(story.title,1,20) as title,substring(comment.raw:text,1,20) as comment
from story join comment on story.id=comment.root_id;
```

The key code in hackernews.py:

```python
op.output("stories-out", story_stream, ProtonSink("hn_stories", os.environ.get("PROTON_HOST","127.0.0.1")))
```

`hn_stories` is the stream name. The `ProtonSink` will create the stream if it doesn't exist.

```python
class _ProtonSinkPartition(StatelessSinkPartition):
    def __init__(self, stream: str, host: str):
        self.client=client.Client(host=host, port=8463)
        self.stream=stream
        sql=f"CREATE STREAM IF NOT EXISTS `{stream}` (raw string)"
        logger.debug(sql)
        self.client.execute(sql)
```

and batch insert data

```python
    def write_batch(self, items):
        rows=[]
        for item in items:
            rows.append([item]) # single column in each row
        sql = f"INSERT INTO `{self.stream}` (raw) VALUES"
        # logger.debug(f"inserting data {sql}")
        self.client.execute(sql,rows)
```

```python
class ProtonSink(DynamicSink):
    def __init__(self, stream: str, host: str):
        self.stream = stream
        self.host = host if host is not None and host != "" else "127.0.0.1"


    def build(self, worker_index, worker_count):
        """See ABC docstring."""
        return _ProtonSinkPartition(self.stream, self.host)
```

### Querying and visualizing with Grafana

Please try the docker-compose file. The Grafana instance is setup to install [Proton Grafana Data Source Plugin](https://github.com/timeplus-io/proton-grafana-source). Create such a data source and preconfigure a dashboard. Open Grafana UI at http://localhost:3000 in your browser and choose the `Hackernews Live Dashboard`.
