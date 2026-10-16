"""Stage 2 — Detect: run recipe-selected detectors, then apply filters (design §2)."""
from __future__ import annotations

from photoai.detectors import (
    eyes_gaze,
    face_analyzer,
    ocr_damage,
    person_depth,
    product_matting,
)
from photoai.engine.context import PipelineContext
from photoai.errors import NoClosedEyesError, NoFaceDetectedError
from photoai.engine.recipe_schema import DetectStep, FilterStep


def _run_filter(context: PipelineContext, config: FilterStep) -> None:
    if config.only_closed_eyes:
        eyes = context.detections.get("eyes")
        if eyes is None:
            raise NoFaceDetectedError("Không tìm thấy khuôn mặt.")
        if eyes.ear >= float(config.ear_below):
            raise NoClosedEyesError("Mắt đã mở, không có gì để sửa.")

    if config.require_face and not context.detections.get("main_face"):
        raise NoFaceDetectedError("Không tìm thấy khuôn mặt.")


def run(context: PipelineContext, detect: DetectStep, filt: FilterStep) -> PipelineContext:
    detections = context.detections
    params = context.params

    if detect.faces:
        faces = face_analyzer.detect_faces(context.image)
        detections["faces"] = faces
        detections["main_face"] = face_analyzer.largest_face(faces)

    if detect.eyes_gaze:
        detections["eyes"] = eyes_gaze.detect_eyes(
            context.image,
            face=detections.get("main_face"),
            left_ear=float(params.get("left_ear", 0.15)),
            right_ear=float(params.get("right_ear", 0.15)),
            threshold=float(params.get("ear_threshold", eyes_gaze.DEFAULT_EAR_THRESHOLD)),
        )

    if detect.persons:
        persons = person_depth.detect_persons(context.image)
        detections["persons"] = persons
        detections["main_person"] = person_depth.main_subject(persons, context.image.size)

    if detect.text_logo:
        detections["text_logo"] = ocr_damage.detect_text_logo(context.image)

    if detect.scratches:
        detections["scratches"] = ocr_damage.detect_scratches(context.image)

    if detect.product:
        detections["product_alpha"] = product_matting.product_alpha(context.image, context.mask)

    context.log("detect", "ok")
    _run_filter(context, filt)
    return context
