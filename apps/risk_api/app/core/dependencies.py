from fastapi import Request # type: ignore
from pymongo.database import Database

def get_db(request: Request) -> Database:
    return request.app.mongodb
