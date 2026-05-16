"""Background execution service for page OCR jobs."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import logging
import time
from typing import Optional
import uuid

from app.database import SessionLocal
from app.models.page import Page
from app.services.pdf_ocr_service import PdfOcrService
from config import config

logger = logging.getLogger(__name__)


class PageOcrJobService:
    """Run OCR jobs inline or in a dedicated background executor."""

    _executor: Optional[ThreadPoolExecutor] = None

    @classmethod
    def _ensure_executor(cls) -> ThreadPoolExecutor:
        if cls._executor is None:
            cls._executor = ThreadPoolExecutor(
                max_workers=max(1, config.OCR_PIPELINE_MAX_WORKERS),
                thread_name_prefix="nlf-ocr",
            )
        return cls._executor

    @classmethod
    def shutdown(cls) -> None:
        if cls._executor is not None:
            cls._executor.shutdown(wait=False, cancel_futures=False)
            cls._executor = None

    @classmethod
    def should_process_inline(cls) -> bool:
        return (
            not config.OCR_PIPELINE_ASYNC
            or not config.OCR_PIPELINE_ENABLED
            or config.OCR_PIPELINE_REQUIRED
        )

    @classmethod
    def schedule_page_ocr(
        cls,
        page_id: str,
        record_id: Optional[str] = None,
        preserve_comment: bool = False,
        preserved_comment: Optional[str] = None,
        previous_current_file: Optional[str] = None,
    ) -> bool:
        """Schedule OCR for a page. Returns True when completed inline."""
        import_id = str(uuid.uuid4())
        if cls.should_process_inline():
            cls._process_page_ocr(
                page_id=page_id,
                record_id=record_id,
                import_id=import_id,
                raise_on_error=True,
                preserve_comment=preserve_comment,
                preserved_comment=preserved_comment,
                previous_current_file=previous_current_file,
            )
            return True

        logger.info(
            "Queueing background OCR job. import_id=%s page_id=%s record_id=%s",
            import_id,
            page_id,
            record_id or "-",
        )
        cls._ensure_executor().submit(
            cls._process_page_ocr,
            page_id,
            record_id,
            import_id,
            False,
            preserve_comment,
            preserved_comment,
            previous_current_file,
        )
        return False

    @classmethod
    def _parse_page_id(cls, page_id: str):
        try:
            return uuid.UUID(str(page_id))
        except (TypeError, ValueError):
            return page_id

    @classmethod
    def _process_page_ocr(
        cls,
        page_id: str,
        record_id: Optional[str],
        import_id: str,
        raise_on_error: bool = False,
        preserve_comment: bool = False,
        preserved_comment: Optional[str] = None,
        previous_current_file: Optional[str] = None,
    ) -> None:
        db = SessionLocal()
        t0 = time.monotonic()
        try:
            parsed_page_id = cls._parse_page_id(page_id)
            page = db.query(Page).filter(Page.id == parsed_page_id, Page.active == True).first()
            if not page:
                logger.warning(
                    "Skipping OCR job because page was not found. import_id=%s page_id=%s record_id=%s",
                    import_id,
                    page_id,
                    record_id or "-",
                )
                return

            if not page.orgin_file:
                logger.info(
                    "Skipping OCR job because page has no origin file. import_id=%s page_id=%s record_id=%s",
                    import_id,
                    page_id,
                    record_id or str(page.record_id),
                )
                return

            logger.info(
                "Processing OCR job. import_id=%s page_id=%s record_id=%s",
                import_id,
                page_id,
                record_id or str(page.record_id),
            )
            ocr_result = PdfOcrService.process_origin_to_current(
                page.orgin_file,
                import_id=import_id,
                page_id=page_id,
                record_id=record_id or str(page.record_id),
            )
            page.current_file = ocr_result.current_file_relative_path

            if (
                previous_current_file
                and page.current_file
                and previous_current_file != page.current_file
            ):
                previous_current_path = (config.UPLOAD_DIRECTORY / previous_current_file).resolve()
                if previous_current_path.exists() and previous_current_path.is_file():
                    previous_current_path.unlink()

            from app.routes.pages import _update_page_comment_with_detected_page_number

            _update_page_comment_with_detected_page_number(page)
            if preserve_comment:
                page.comment = preserved_comment
            page.last_modified_on = datetime.now(timezone.utc)
            db.commit()
            logger.info(
                "Completed OCR job. duration=%.1fs import_id=%s page_id=%s record_id=%s current_file=%s",
                time.monotonic() - t0,
                import_id,
                page_id,
                record_id or str(page.record_id),
                page.current_file,
            )
        except Exception:
            db.rollback()
            logger.exception(
                "OCR job failed. import_id=%s page_id=%s record_id=%s",
                import_id,
                page_id,
                record_id or "-",
            )
            if raise_on_error:
                raise
        finally:
            db.close()
