"""ONNX bounding-box detector for the Impact Pack detailer (FaceDetailer).

Provides the node "OnnxBBoxDetectorProvider", a drop-in replacement for the Impact Subpack's
UltralyticsDetectorProvider that runs YOLO-style ONNX models with onnxruntime (CPU), so the worker
does not need the Ultralytics package. Models are read from ComfyUI's models/onnx_bbox folder.

Expected model output: (1, 4 + classes, N) with boxes as (cx, cy, w, h) on a square letterboxed input
(the usual YOLOv8 ONNX export, e.g. deepghs/anime_face_detection and deepghs/anime_hand_detection).
"""

from __future__ import annotations

import os

import numpy as np
from PIL import Image

import folder_paths

FOLDER = "onnx_bbox"
folder_paths.add_model_folder_path(FOLDER, os.path.join(folder_paths.models_dir, FOLDER))
folder_paths.folder_names_and_paths[FOLDER] = (folder_paths.folder_names_and_paths[FOLDER][0], {".onnx"})

IOU = 0.5


def _iou(a, b) -> float:
    iw = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    ih = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = iw * ih
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


class OnnxBBoxModel:
    def __init__(self, path: str, label: str):
        import onnxruntime as ort

        self.session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        inp = self.session.get_inputs()[0]
        self.input_name = inp.name
        size = inp.shape[-1]
        self.size = size if isinstance(size, int) else 640
        self.label = label

    def predict(self, image: Image.Image, threshold: float) -> list[tuple[np.ndarray, float]]:
        """Boxes (x1, y1, x2, y2 in image pixels) and confidences, highest first."""
        im = image.convert("RGB")
        w, h = im.size
        r = self.size / max(w, h)
        nw, nh = round(w * r), round(h * r)
        canvas = Image.new("RGB", (self.size, self.size), (114, 114, 114))
        px, py = (self.size - nw) // 2, (self.size - nh) // 2
        canvas.paste(im.resize((nw, nh), Image.BILINEAR), (px, py))
        x = np.asarray(canvas, dtype=np.float32).transpose(2, 0, 1)[None] / 255.0
        out = self.session.run(None, {self.input_name: x})[0][0].T
        scores = out[:, 4:].max(axis=1)
        keep = scores >= threshold
        boxes, scores = out[keep, :4], scores[keep]
        found: list[tuple[np.ndarray, float]] = []
        for i in scores.argsort()[::-1]:
            cx, cy, bw, bh = boxes[i]
            box = np.array(
                [
                    max(0.0, (cx - bw / 2 - px) / r),
                    max(0.0, (cy - bh / 2 - py) / r),
                    min(float(w), (cx + bw / 2 - px) / r),
                    min(float(h), (cy + bh / 2 - py) / r),
                ],
                dtype=np.float32,
            )
            if all(_iou(box, b) < IOU for b, _ in found):
                found.append((box, float(scores[i])))
        return found


def _results(model: OnnxBBoxModel, image: Image.Image, threshold: float):
    """Same shape as the Impact Subpack's inference_bbox: [labels, bboxes, masks, confidences]."""
    found = model.predict(image, threshold)
    w, h = image.size
    results = [[], [], [], []]
    for box, conf in found:
        mask = np.zeros((h, w), dtype=bool)
        x0, y0, x1, y1 = (int(v) for v in box)
        mask[y0:y1, x0:x1] = True
        results[0].append(model.label)
        results[1].append(box)
        results[2].append(mask)
        results[3].append(np.float32(conf))
    return results


def _segmasks(results):
    return [(results[1][i], results[2][i].astype(np.float32), results[3][i]) for i in range(len(results[2]))]


class OnnxBBoxDetector:
    """The BBOX_DETECTOR interface used by the Impact Pack (detect / detect_combined / setAux)."""

    def __init__(self, model: OnnxBBoxModel):
        self.model = model

    def detect(self, image, threshold, dilation, crop_factor, drop_size=1, detailer_hook=None):
        from impact import utils
        from impact.core import SEG

        drop_size = max(drop_size, 1)
        results = _results(self.model, utils.tensor2pil(image), threshold)
        segmasks = _segmasks(results)
        if dilation > 0:
            segmasks = utils.dilate_masks(segmasks, dilation)
        items = []
        h = image.shape[1]
        w = image.shape[2]
        for x, label in zip(segmasks, results[0]):
            item_bbox, item_mask, confidence = x[0], x[1], x[2]
            x1, y1, x2, y2 = item_bbox
            if x2 - x1 > drop_size and y2 - y1 > drop_size:
                crop_region = utils.make_crop_region(w, h, item_bbox, crop_factor)
                if detailer_hook is not None:
                    crop_region = detailer_hook.post_crop_region(w, h, item_bbox, crop_region)
                cropped_image = utils.crop_image(image, crop_region)
                cropped_mask = utils.crop_ndarray2(item_mask, crop_region)
                items.append(SEG(cropped_image, cropped_mask, confidence, crop_region, item_bbox, label, None))
        segs = (image.shape[1], image.shape[2]), items
        if detailer_hook is not None and hasattr(detailer_hook, "post_detection"):
            segs = detailer_hook.post_detection(segs)
        return segs

    def detect_combined(self, image, threshold, dilation):
        from impact import utils

        segmasks = _segmasks(_results(self.model, utils.tensor2pil(image), threshold))
        if dilation > 0:
            segmasks = utils.dilate_masks(segmasks, dilation)
        return utils.combine_masks(segmasks)

    def setAux(self, x):
        pass


class OnnxBBoxDetectorProvider:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"model_name": (folder_paths.get_filename_list(FOLDER),)}}

    RETURN_TYPES = ("BBOX_DETECTOR",)
    FUNCTION = "load"
    CATEGORY = "ImpactPack"

    def load(self, model_name):
        path = folder_paths.get_full_path(FOLDER, model_name)
        # The class label is the first word of the file name (e.g. "face_..." -> "face")
        label = os.path.basename(model_name).split("_")[0].split(".")[0] or "object"
        return (OnnxBBoxDetector(OnnxBBoxModel(path, label)),)


NODE_CLASS_MAPPINGS = {"OnnxBBoxDetectorProvider": OnnxBBoxDetectorProvider}
NODE_DISPLAY_NAME_MAPPINGS = {"OnnxBBoxDetectorProvider": "ONNX BBox Detector Provider"}
