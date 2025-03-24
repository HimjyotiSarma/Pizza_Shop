from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.config import settings
from src.db.main import init_db
from pathlib import Path
from fastapi.staticfiles import StaticFiles
import logging

# Import Routers Here
from src.auth.routes import auth_router
from src.items_Categories.routes import item_router


APP_VERSION = settings.APP_VERSION
ROOT_ROUTE = settings.ROOT_ROUTE


# Lifespan Event
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server started running")
    try:
        await init_db()
    except Exception as e:
        logging.exception("Database Connection Failed")
        raise e  # Propagate the error
    yield
    print("Server Stopped running")


app = FastAPI(
    title="Pizza Ecommerce Shop",
    description="A REST app of Pizza Delivery Shop",
    version=APP_VERSION,
)

# Register Middleware here when Needed


# Add Routers Here
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = Path(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(
    auth_router,
    prefix=f"/{ROOT_ROUTE}/{APP_VERSION}",
    tags=["authentication and authorization"],
)
app.include_router(
    item_router,
    prefix=f"/{ROOT_ROUTE}/{APP_VERSION}/inventory",
    tags=["Items and Category"],
)
