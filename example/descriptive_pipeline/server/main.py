from fastapi import (
    FastAPI,
    WebSocket,
    HTTPException,
    WebSocketDisconnect,
    Request,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import yaml
import queue
import threading
import asyncio
import json
from proton_driver import client
from .utils.logging import getLogger

logger = getLogger()


class Pipeline(BaseModel):
    name: str # noqa
    sqls: list[str] # noqa


class Pipelines(BaseModel):
    pipelines: list[Pipeline]


class Config(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=8463)
    db: str = Field(default="default")
    user: str = Field(default="default")
    password: str = Field(default="")
    pipelines: list[Pipeline]


class ConfigManager:
    def __init__(self):
        self.config = None
        self.lock = threading.Lock()

    def load_config_from_file(self, filename: str):
        with open(filename, 'r') as yaml_file:
            loaded_data = yaml.safe_load(yaml_file)
        config_instance = Config.parse_obj(loaded_data)
        self.config = config_instance

    def get_pipelines(self):
        return self.config.pipelines

    def get_pipeline_by_name(self, name):
        for pipeline in self.config.pipelines:
            if pipeline.name == name:
                return pipeline
        return None

    def pipeline_exist(self, name):
        for pipeline in self.config.pipelines:
            if pipeline.name == name:
                return True
        return False

    def delete_pipeline(self, name):
        updated_pipelines = [
            pipeline
            for pipeline in self.config.pipelines
            if pipeline.name != name
        ]
        self.config.pipelines = updated_pipelines
        self.save()

    def add_pipeline(self, pipeline: Pipeline):
        if self.pipeline_exist(pipeline.name):
            raise Exception('pipeline already exist')
        self.config.pipelines.append(pipeline)
        self.save()

    def save(self):
        with open('config.yaml', 'w') as yaml_file:
            yaml.dump(self.config, yaml_file)

    def run_pipeline(self, name):
        proton_client = client.Client(
            host=self.config.host,
            port=self.config.port,
            database=self.config.db,
            user=self.config.user,
            password=self.config.password,
        )
        pipeline = self.get_pipeline_by_name(name)
        if pipeline is not None:
            for query in pipeline.sqls[:-1]:
                proton_client.execute(query)

            last_query = pipeline.sqls[-1]
            query = Query(last_query, proton_client)
            return query
        else:
            raise Exception('pipeline not found!')

    def conf(self):
        return self.config


class Query:
    def __init__(self, sql, client):
        self.sql = sql
        self.lock = threading.Lock()
        self.queue = queue.Queue()
        self.client = client
        self.terminate_flag = threading.Event()
        self.header = None

        self.finished = False

        producer_thread = threading.Thread(target=self.run)
        producer_thread.start()

    def run(self):
        rows = self.client.execute_iter(self.sql, with_column_types=True)
        header = next(rows)
        self.header = header
        try:
            for row in rows:
                with self.lock:
                    if self.terminate_flag.is_set():
                        break
                    self.queue.put(row)
        except Exception:
            logger.debug('failed to get query result')

        self.finished = True

    def pull(self):
        result = []
        with self.lock:
            while not self.queue.empty():
                m = self.queue.get()
                result.append(m)
        return result

    async def get_header(self):
        while self.header is None:
            await asyncio.sleep(1)
        return self.header

    def cancel(self):
        self.terminate_flag.set()
        try:
            # self.client.cancel()
            self.client.disconnect()
        except Exception:
            logger.exception('failed to disconnect proton')

    def is_finshed(self):
        return self.finished


app = FastAPI()
config_manager = ConfigManager()


@app.on_event("startup")
def startup_event():
    config_manager.load_config_from_file('config.yaml')


@app.get("/")
def info():
    return {"info": "proton query to websocket"}


@app.get("/config")
def config():
    return config_manager.conf()


@app.post("/pipelines")
def create_pipeline(item: Pipeline):
    if config_manager.pipeline_exist(item.name):
        raise HTTPException(status_code=400, detail="pipeline exist")
    config_manager.add_pipeline(item)
    return item


@app.get("/pipelines/{name}")
def get_pipeline(name: str):
    if not config_manager.pipeline_exist(name):
        raise HTTPException(status_code=404, detail="pipeline not found")
    return config_manager.get_pipeline_by_name(name)


@app.get("/pipelines")
def list_pipeline():
    return config_manager.get_pipelines()


@app.delete("/pipelines/{name}")
def delete_pipeline(name: str):
    if not config_manager.pipeline_exist(name):
        raise HTTPException(status_code=404, detail="pipeline not found")
    config_manager.delete_pipeline(name)
    return JSONResponse(status_code=204)


async def query_stream(name, request, background_tasks):
    async def check_disconnect():
        while True:
            await asyncio.sleep(1)
            disconnected = await request.is_disconnected()
            if disconnected:
                query.cancel()
                logger.info('Client disconnected')
                break

    background_tasks.add_task(check_disconnect)

    query = config_manager.run_pipeline(name)
    header = await query.get_header()
    while True:
        messages = query.pull()
        for m in messages:
            try:
                result = {}
                for index, (name, t) in enumerate(header):
                    if t.startswith('date'):
                        # convert datetime type to string
                        result[name] = str(m[index])
                    else:
                        result[name] = m[index]
                result_str = json.dumps(result).encode("utf-8") + b"\n"
                yield result_str
            except Exception as e:
                query.cancel()
                logger.info(f'query cancelled due to {e}')
                break

        if query.is_finshed():
            break

        await asyncio.sleep(0.1)


@app.get("/queries/{name}")
def query_pipeline(
    name: str, request: Request, background_tasks: BackgroundTasks
):
    if not config_manager.pipeline_exist(name):
        raise HTTPException(status_code=404, detail="pipeline not found")

    return StreamingResponse(
        query_stream(name, request, background_tasks),
        media_type="application/json",
    )


@app.websocket("/queries/{name}")
async def websocket_endpoint(name: str, websocket: WebSocket):
    await websocket.accept()

    if not config_manager.pipeline_exist(name):
        raise HTTPException(status_code=404, detail="pipeline not found")
    query = config_manager.run_pipeline(name)
    header = await query.get_header()
    logger.debug(f'query header is {header}')

    try:
        while True:
            messages = query.pull()
            hasError = False
            for m in messages:
                try:
                    result = {}
                    for index, (name, t) in enumerate(header):
                        if t.startswith('date'):
                            # convert datetime type to string
                            result[name] = str(m[index])
                        else:
                            result[name] = m[index]

                    await websocket.send_text(f'{json.dumps(result)}')
                except Exception:
                    hasError = True
                    query.cancel()
                    logger.debug('query cancelled')
                    break

            if hasError:
                break

            if query.is_finshed():
                break

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        logger.info('session disconnected')
    except Exception as e:
        logger.exception(e)
    finally:
        # Ensure query cancellation even if an exception is raised
        query.cancel()
        await websocket.close()
        logger.debug('session closed')
