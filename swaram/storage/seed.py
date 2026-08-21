import asyncio
from swaram.config.loader import load_yaml_config
from swaram.core.logging import get_logger, setup_logging
from swaram.storage.postgres import get_db_session, init_db
from swaram.storage.repositories.instrument_repo import InstrumentRepository

logger = get_logger("storage.seed")


async def seed_instruments() -> None:
    setup_logging()
    await init_db()

    config = load_yaml_config("symbols.yaml")
    symbols_list = config.get("symbols", [])

    logger.info(f"Seeding {len(symbols_list)} instruments from configuration...")

    async with get_db_session() as session:
        repo = InstrumentRepository(session)
        for item in symbols_list:
            canonical = item["canonical"]
            asset_class = item.get("asset_class", "crypto")
            base = item.get("base_asset", "")
            quote = item.get("quote_asset", "USD")
            tick_size = item.get("tick_size")
            lot_size = item.get("lot_size")
            providers = item.get("providers", {})

            for venue, provider_symbol in providers.items():
                inst = await repo.get_or_create(
                    canonical_symbol=canonical,
                    asset_class=asset_class,
                    base_asset=base,
                    quote_asset=quote,
                    venue=venue,
                    provider_symbol=provider_symbol,
                    tick_size=tick_size,
                    lot_size=lot_size,
                )
                logger.info(f"Seeded instrument: {inst.canonical_symbol} ({inst.venue}:{inst.provider_symbol})")

    logger.info("Database seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed_instruments())
