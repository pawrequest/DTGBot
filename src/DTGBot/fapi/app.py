from contextlib import asynccontextmanager
import ssl

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from loguru import logger
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles

from DTGBot.common.dtg_config import dtg_sett
from DTGBot.fapi.guru_route import router as guru_router
from DTGBot.fapi.episode_route import router as ep_router
from DTGBot.fapi.red_route import router as red_router
from DTGBot.common.database import create_db

GURU_CONFIG = dtg_sett()


STATIC = GURU_CONFIG.guru_frontend / 'static'

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        create_db()
        logger.info('tables created')
        yield
    finally:
        ...


app = FastAPI(lifespan=lifespan)

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(GURU_CONFIG.ssl_cert, keyfile=GURU_CONFIG.ssl_key)


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
