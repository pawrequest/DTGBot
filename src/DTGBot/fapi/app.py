from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from loguru import logger
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from DTGBot.common.dtg_config import dtg_sett
from DTGBot.fapi.guru_route import router as guru_router
from DTGBot.fapi.episode_route import router as ep_router
from DTGBot.fapi.red_route import router as red_router
from DTGBot.fapi.admin_route import router as admin_router
from DTGBot.common.database import create_db

dtg_settings = dtg_sett()
STATIC = dtg_settings.guru_frontend / 'static'
TEMPLATES_DIR = str(dtg_settings.guru_frontend / 'templates')


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
# templates = Jinja2Templates(directory=TEMPLATES_DIR)

app.include_router(ep_router, prefix='/eps')
app.include_router(guru_router, prefix='/guru')
app.include_router(red_router, prefix='/red')
# app.include_router(admin_router, prefix='/admin')


@app.get('/robots.txt', response_class=PlainTextResponse)
async def robots_txt() -> str:
    return 'User-agent: *\nAllow: /'


@app.get('/favicon.ico', status_code=404, response_class=PlainTextResponse)
async def favicon_ico() -> str:
    return 'page not found'


@app.get('/', response_class=RedirectResponse)
async def index():
    return RedirectResponse(url=f'{dtg_sett().url_prefix}/eps')
