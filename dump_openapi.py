import json
from pathlib import Path

from fastapi import FastAPI, APIRouter

from planitor.endpoints import api


def custom_generate_unique_id(route: APIRouter):
    return route.name


app = FastAPI(generate_unique_id_function=custom_generate_unique_id)
app.include_router(api.router, prefix="/api")
file_path = Path("./openapi.json")
file_path.write_text(json.dumps(app.openapi(), indent=2))
