# -*- coding: utf-8 -*-
"""
model_loader.py
-----------------
Nap 4 model Keras (.h5) va du doan nhan (Dai / Ngan / TrungBinh) cho tung
duong chi tay.

Thu tu class theo alphabet khi train voi flow_from_directory:
    index 0 = Dai
    index 1 = Ngan
    index 2 = TrungBinh
"""

import logging
import os

import numpy as np
from PIL import Image

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

import tensorflow as tf  # noqa: E402

logger = logging.getLogger(__name__)

# Ten file model mong doi trong thu muc backend/models/
MODEL_FILENAMES = {
    "sinh_dao":  "Sinh_Dao_model.h5",
    "su_nghiep": "Su_Nghiep_model.h5",
    "tam_dao":   "Tam_Dao_model.h5",
    "tri_dao":   "Tri_Dao_model.h5",
}

# Thu tu class theo alphabet (flow_from_directory): 0=Dai, 1=Ngan, 2=TrungBinh
CLASS_LABELS = ["Dai", "Ngan", "TrungBinh"]


class PalmLineModel:
    """Boc 1 model Keras, tu doc input_shape de resize anh cho dung."""

    def __init__(self, key: str, path: str):
        self.key = key
        self.model = tf.keras.models.load_model(path, compile=False)

        in_shape = self.model.input_shape
        if isinstance(in_shape, list):
            in_shape = in_shape[0]
        self.target_h = in_shape[1] or 224
        self.target_w = in_shape[2] or 224
        self.channels = in_shape[3] if len(in_shape) > 3 and in_shape[3] else 3

        out_shape = self.model.output_shape
        if isinstance(out_shape, list):
            out_shape = out_shape[0]
        self.output_dim = out_shape[-1]

        logger.info(
            "[%s] Da nap '%s' | input=%sx%sx%s | output_dim=%s",
            self.key, os.path.basename(path),
            self.target_h, self.target_w, self.channels, self.output_dim,
        )

    def preprocess(self, pil_image: Image.Image) -> np.ndarray:
        mode = "RGB" if self.channels == 3 else "L"
        img = pil_image.convert(mode).resize((self.target_w, self.target_h))
        arr = np.asarray(img).astype("float32") / 255.0
        if self.channels == 1 and arr.ndim == 2:
            arr = np.expand_dims(arr, axis=-1)
        return np.expand_dims(arr, axis=0)

    def predict_label(self, pil_image: Image.Image) -> dict:
        """
        Tra ve:
            nhan       : "Dai" | "Ngan" | "TrungBinh"
            confidence : xac suat cua class thang (0-100, %)
            raw_output : xac suat ca 3 class [p_Dai, p_Ngan, p_TrungBinh]
        """
        x = self.preprocess(pil_image)
        raw = np.asarray(self.model.predict(x, verbose=0)).flatten()

        idx = int(np.argmax(raw))
        nhan = CLASS_LABELS[idx] if idx < len(CLASS_LABELS) else "TrungBinh"
        confidence = round(float(raw[idx]) * 100, 1)

        return {
            "nhan":       nhan,
            "confidence": confidence,
            "raw_output": raw.tolist(),
        }


class PalmModelRegistry:
    """Nap va giu san trong RAM ca 4 model."""

    def __init__(self, models_dir: str):
        self.models_dir = models_dir
        self.models: dict[str, PalmLineModel] = {}
        self._load_all()

    def _load_all(self):
        missing = []
        for key, filename in MODEL_FILENAMES.items():
            path = os.path.join(self.models_dir, filename)
            if not os.path.isfile(path):
                missing.append(filename)
                continue
            self.models[key] = PalmLineModel(key, path)

        if missing:
            logger.warning(
                "Chua tim thay %d model trong '%s': %s",
                len(missing), self.models_dir, ", ".join(missing),
            )

    def is_ready(self) -> bool:
        return len(self.models) == len(MODEL_FILENAMES)

    def missing_models(self) -> list:
        return [k for k in MODEL_FILENAMES if k not in self.models]

    def predict_all(self, pil_image: Image.Image) -> dict:
        """Chay anh qua 4 model, tra ve dict {key: label_info | error}."""
        results = {}
        for key, plm in self.models.items():
            try:
                results[key] = plm.predict_label(pil_image)
            except Exception as exc:
                logger.exception("Loi model '%s'", key)
                results[key] = {"error": str(exc)}
        return results
