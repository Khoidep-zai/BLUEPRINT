"""Detect step (AGENT_SKILLS S1/S3/S4)."""
from __future__ import annotations

from typing import Any, Dict

from ...detectors import eyes_ear, face, person, text_logo
from ...pipeline.context import JobContext


def run(context: JobContext, config: Dict[str, Any]) -> JobContext:
    """Populate ``context.detections`` according to the recipe detect config."""
    config = config or {}
    detections = context.detections

    if config.get("faces"):
        faces = face.detect_faces(context.image)
        detections["faces"] = faces
        detections["main_face"] = face.largest_face(faces)

    if config.get("eyes_ear"):
        params = context.params
        eyes = eyes_ear.detect_eyes(
            context.image,
            face=detections.get("main_face"),
            left_ear=float(params.get("left_ear", 0.15)),
            right_ear=float(params.get("right_ear", 0.15)),
            threshold=float(params.get("ear_threshold", eyes_ear.DEFAULT_EAR_THRESHOLD)),
        )
        detections["eyes"] = eyes

    if config.get("persons"):
        persons = person.detect_persons(context.image)
        detections["persons"] = persons
        detections["main_person"] = person.main_subject(persons, context.image.size)

    if config.get("text_logo"):
        detections["text_logo"] = text_logo.detect_text_logo(context.image)

    context.log("detect", "ok")
    return context
