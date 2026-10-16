"""QThread wrapper around :class:`RecipeRunner` (design §2 ui/workers_qt.py).

Keeps the UI responsive: the seven-stage pipeline runs off the GUI thread and
communicates only through Qt signals.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from PIL import Image
from PySide6 import QtCore

from photoai.engine.loader import load_recipe_by_id
from photoai.engine.runner import RecipeRunner
from photoai.storage.db import LocalWorkspaceManager


class PipelineWorker(QtCore.QThread):
    progress = QtCore.Signal(str, int)  # stage label, percent 0-100
    finished_ok = QtCore.Signal(object)  # RunResult
    failed = QtCore.Signal(str)

    STAGES = (
        ("Ingest", 5),
        ("Detect", 20),
        ("Mask", 35),
        ("GPU Edit", 60),
        ("Blend", 75),
        ("QA", 90),
        ("Done", 100),
    )

    def __init__(
        self,
        recipe_id: str,
        image: Image.Image,
        mask: Optional[Image.Image] = None,
        params: Optional[Dict[str, Any]] = None,
        parent: Optional[QtCore.QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.recipe_id = recipe_id
        self.image = image
        self.mask = mask
        self.params = dict(params or {})
        self.workspace = LocalWorkspaceManager()

    def run(self) -> None:  # noqa: D401 - QThread entry point
        try:
            self.progress.emit(self.STAGES[0][0], self.STAGES[0][1])
            recipe = load_recipe_by_id(self.recipe_id)
            job_id = self.workspace.create_job(self.recipe_id, self.params)
            self.params["persist_result"] = True
            self.params["job_id"] = job_id

            if self.recipe_id == "remove_watermark" and self.params.get("ownership_confirmed"):
                self.workspace.audit("watermark_confirmed", {"job_id": job_id})

            for stage, percent in self.STAGES[1:]:
                self.progress.emit(stage, percent)

            result = RecipeRunner().run(
                recipe, self.image, mask=self.mask, params=self.params, job_id=job_id
            )

            self.workspace.finish_job(
                job_id,
                status="done",
                result_path=result.context.export_path,
                warnings=result.warnings,
                qa_report=result.report.to_dict(),
            )
            self.progress.emit("Done", 100)
            self.finished_ok.emit(result)
        except Exception as exc:  # pragma: no cover - UI path
            self.failed.emit(str(exc))
