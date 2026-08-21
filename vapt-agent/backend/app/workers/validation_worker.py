"""
Validation worker - re-validate candidate findings.
"""
import asyncio
import structlog
from app.workers.celery_app import celery_app
from app.core.config import settings

logger = structlog.get_logger(__name__)


async def _validate_async(finding_id: str):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        from app.validation.engine import ValidationEngine
        validator = ValidationEngine(db=db, scan_id=None)
        await validator.validate_finding(finding_id)

    await engine.dispose()


@celery_app.task(name="app.workers.validation_worker.validate_finding_task", bind=True)
def validate_finding_task(self, finding_id: str):
    asyncio.run(_validate_async(finding_id))
