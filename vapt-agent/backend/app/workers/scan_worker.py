"""
Main scan orchestration worker.
Coordinates recon → browser crawl → security tests → validation → report.
"""
import asyncio
from datetime import datetime, timezone
from typing import Optional

import structlog
from celery import Task

from app.workers.celery_app import celery_app
from app.core.config import settings

logger = structlog.get_logger(__name__)


def get_sync_db():
    """Get synchronous DB session for Celery workers."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(settings.DATABASE_URL_SYNC)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


async def _run_full_scan_async(scan_id: str):
    """Async implementation of the full scan pipeline."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from app.models.scan import Scan, ScanStatus
    from app.models.project import Target

    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        result = await db.execute(select(Scan).where(Scan.id == scan_id))
        scan = result.scalar_one_or_none()
        if not scan:
            logger.error("scan_not_found", scan_id=scan_id)
            return

        target_result = await db.execute(select(Target).where(Target.id == scan.target_id))
        target = target_result.scalar_one_or_none()

        scan.started_at = datetime.now(timezone.utc)

        try:
            from app.core.websocket_manager import ws_manager

            # ── Phase 1: Recon ─────────────────────────────────────────────
            scan.status = ScanStatus.RECON
            await db.commit()

            from app.recon.recon_engine import ReconEngine
            recon = ReconEngine(db=db, scan_id=scan_id, target=target)
            await recon.run()

            # ── Phase 2: Browser/API Crawl ────────────────────────────────
            scan.status = ScanStatus.CRAWLING
            await db.commit()

            from app.browser.crawler import BrowserCrawler
            crawler = BrowserCrawler(db=db, scan_id=scan_id, target=target)
            await crawler.crawl()

            # ── Phase 3: Security Tests ───────────────────────────────────
            scan.status = ScanStatus.TESTING
            await db.commit()

            from app.security_tests.runner import SecurityTestRunner
            runner = SecurityTestRunner(db=db, scan=scan, target=target)
            await runner.run()

            # ── Phase 4: External Scanners ────────────────────────────────
            from app.scanners.orchestrator import ScannerOrchestrator
            orch = ScannerOrchestrator(db=db, scan=scan, target=target)
            await orch.run()

            # ── Phase 5: Validation ───────────────────────────────────────
            scan.status = ScanStatus.VALIDATING
            await db.commit()

            from app.validation.engine import ValidationEngine
            validator = ValidationEngine(db=db, scan_id=scan_id)
            await validator.run()

            # ── Phase 6: AI Analysis ──────────────────────────────────────
            try:
                from app.agents.vapt_agent import VAPTAgent
                agent = VAPTAgent(db=db, user_id=None)
                await agent.analyze_scan(scan_id=scan_id)
            except Exception as e:
                logger.warning("ai_analysis_failed", error=str(e))

            # ── Complete ──────────────────────────────────────────────────
            scan.status = ScanStatus.COMPLETED
            scan.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.error("scan_failed", scan_id=scan_id, error=str(e))
            scan.status = ScanStatus.FAILED
            scan.error_message = str(e)

        await db.commit()
        logger.info("scan_finished", scan_id=scan_id, status=scan.status)

    await engine.dispose()


@celery_app.task(name="app.workers.scan_worker.run_full_scan", bind=True, max_retries=1)
def run_full_scan(self: Task, scan_id: str):
    """Main scan task - runs the full VAPT pipeline."""
    logger.info("scan_task_started", scan_id=scan_id)
    asyncio.run(_run_full_scan_async(scan_id))


async def _generate_report_async(report_id: str, scan_id: str, format: str):
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from app.models.audit import Report

    engine = create_async_engine(settings.DATABASE_URL)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as db:
        from app.reports.generator import ReportGenerator
        generator = ReportGenerator(db=db)
        await generator.generate(report_id=report_id, scan_id=scan_id, format=format)

    await engine.dispose()


@celery_app.task(name="app.workers.scan_worker.generate_report_task", bind=True)
def generate_report_task(self: Task, report_id: str, scan_id: str, format: str):
    """Generate VAPT report in specified format."""
    asyncio.run(_generate_report_async(report_id, scan_id, format))
