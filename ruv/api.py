import requests
from functools import wraps
from urllib.parse import urljoin
from datetime import date
from .models import Overview, SearchResults, ProgramDetails, Schedule

API_URL = 'https://api.ruv.is/api/'

def json(model):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            resp = func(*args, **kwargs)
            resp.raise_for_status()
            return model(resp.json())
        return wrapper
    return decorator

def api_path(path):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(urljoin(API_URL, path), *args, **kwargs)
        return wrapper
    return decorator

@json(SearchResults)
@api_path('programs/search/tv/')
def search(path, search_str):
    search_path = path + search_str
    return requests.get(search_path)

@json(Overview)
@api_path('programs/featured/tv/')
def featured(path):
    return requests.get(path)

@json(ProgramDetails)
@api_path('programs/program/%s/all/')
def program_details(path, program_id):
    path = path % program_id
    return requests.get(path)

@json(Schedule)
@api_path('schedule/%s/%s/')
def schedule(path, channel='ruv', day=None):
    if day is None:
        day = date.today()
    return requests.get(path % (channel, date.strftime(day, '%Y-%m-%d')))

@json(SearchResults)
@api_path('programs/category/tv/')
def category(path, category):
    path = path + category
    return requests.get(path)
