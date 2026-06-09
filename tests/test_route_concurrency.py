import inspect

from fastapi.routing import APIRoute

from planitor.database import get_db
from planitor.main import app


def _dependency_calls(dependant):
    for dependency in dependant.dependencies:
        yield dependency.call
        yield from _dependency_calls(dependency)


def test_db_backed_routes_use_sync_handlers():
    offenders = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if get_db not in set(_dependency_calls(route.dependant)):
            continue
        if inspect.iscoroutinefunction(route.endpoint):
            methods = ",".join(sorted(route.methods or []))
            offenders.append(f"{methods} {route.path} -> {route.name}")

    assert offenders == []
