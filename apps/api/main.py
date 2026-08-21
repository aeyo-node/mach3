from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.routes.health import router as health_router
from apps.api.routes.market import router as market_router
from apps.api.routes.analytics import router as analytics_router
from apps.api.routes.macro import router as macro_router
from swaram.config.settings import get_settings
from swaram.core.logging import get_logger, setup_logging
from swaram.storage.postgres import close_db, init_db
from swaram.storage.redis import close_redis, get_redis
from swaram.storage.seed import seed_instruments

logger = get_logger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(log_level=settings.log_level)
    logger.info("Starting Swaram Market Engine API Service...", version="0.1.0")

    # Initialize Database Schema & Seed default instruments
    await init_db()
    await seed_instruments()

    # Ping Redis
    try:
        redis = get_redis()
        await redis.ping()
        logger.info("Connected to Redis successfully.")
    except Exception as e:
        logger.error("Failed to connect to Redis during startup", error=str(e))

    yield

    logger.info("Shutting down Swaram Market Engine API Service...")
    await close_redis()
    await close_db()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Swaram Market Engine API",
        description="Production-grade multi-market quantitative intelligence platform.",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(macro_router)        # specific: /macro/*, /market/universe — must be before market_router
    app.include_router(analytics_router)    # specific: /market/{symbol}/indicators, /market/{symbol}/structure
    app.include_router(market_router)       # catch-all: /market/{symbol}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "apps.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development",
    )
