from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from loguru import logger
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from DTGBot.fapi.episode_route import router as ep_router
from DTGBot.fapi.guru_route import router as guru_router
from DTGBot.common.database import create_db

TEMPLATES_ = '/templates/'
THIS_DIR = Path(__file__).resolve().parent
STATIC = THIS_DIR.parent / 'frontend' / 'static'

logger.info(f'{STATIC=} \n{TEMPLATES_=}')


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        create_db()
        logger.info('tables created')
        yield
    finally:
        ...


app = FastAPI(lifespan=lifespan)

app.mount('/static', StaticFiles(directory=STATIC), name='static')
templates = Jinja2Templates(directory=TEMPLATES_)

app.include_router(ep_router, prefix='/eps')
app.include_router(guru_router, prefix='/guru')


@app.get('/robots.txt', response_class=PlainTextResponse)
async def robots_txt() -> str:
    return 'User-agent: *\nAllow: /'


@app.get('/favicon.ico', status_code=404, response_class=PlainTextResponse)
async def favicon_ico() -> str:
    return 'page not found'


@app.get('/', response_class=HTMLResponse)
async def index():
    logger.info('index')
    return RedirectResponse(url='/eps/')
