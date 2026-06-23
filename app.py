"""
app.py
-------
Backend Flask cho web app "Xem Chi Tay AI".
 
Chuc nang:
    - Nap san 4 model Keras (.h5) khi server khoi dong (model_loader.py).
    - Nhan anh ban tay (base64) tu frontend, chay qua 4 model.
    - Sinh noi dung tu van (luan giai / diem noi bat / loi khuyen)
      tuong ung voi diem so cua tung duong (advice_engine.py).
    - Tra ve JSON gom ca diem so va noi dung tu van cho frontend hien thi.
 
Chay server:
    pip install -r requirements.txt
    python app.py
    -> server chay tai http://localhost:5000
 
Frontend (frontend/script.js) goi den: POST http://localhost:5000/api/predict
 
SUA LOI:
    - raw_predictions tra ve {"nhan": ..., "confidence": ..., "raw_output": ...}
      nhung code cu tim key "score" (khong ton tai) -> scores luon rong
      -> get_all_consultations nhan dict rong -> khong co ket qua tra ve.
    - Da sua: lay dung key "nhan" va "confidence" de truyen vao advice_engine.
"""
 
import base64
import io
import logging
import os
 
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image
 
from advice_engine import DISCLAIMER, get_all_consultations
from model_loader import PalmModelRegistry
 
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)
 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
 
app = Flask(__name__)
CORS(app)  # cho phep frontend (file html / port khac) goi API nay
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024  # gioi han 12MB / request
 
# Nap 4 model 1 LAN DUY NHAT khi server khoi dong (khong nap lai moi request)
registry = PalmModelRegistry(MODELS_DIR)
 
 
def decode_base64_image(data_url: str) -> Image.Image:
    """
    Nhan chuoi base64 dang "data:image/jpeg;base64,xxxx" (hoac chuoi base64
    thuan, khong co tien to) -> tra ve doi tuong PIL.Image.
    """
    if "," in data_url and data_url.strip().startswith("data:"):
        data_url = data_url.split(",", 1)[1]
    image_bytes = base64.b64decode(data_url)
    return Image.open(io.BytesIO(image_bytes))
 
 
@app.route("/api/health", methods=["GET"])
def health():
    """Kiem tra nhanh server + tinh trang nap model (dung de debug/demo)."""
    return jsonify({
        "status": "ok" if registry.is_ready() else "missing_models",
        "models_loaded": list(registry.models.keys()),
        "models_missing": registry.missing_models(),
    })
 
 
@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Body JSON ky vong:
        { "image": "data:image/jpeg;base64,...." }
 
    Tra ve JSON:
        {
          "success": true,
          "disclaimer": "...",
          "results": {
             "sinh_dao":  { nhan, confidence, luan_giai, diem_noi_bat, loi_khuyen, ... },
             "su_nghiep": { ... },
             "tam_dao":   { ... },
             "tri_dao":   { ... }
          }
        }
    """
    if not registry.is_ready():
        return jsonify({
            "success": False,
            "error": "server_missing_models",
            "message": (
                "Server chua co du 4 model trong thu muc backend/models/. "
                f"Con thieu: {registry.missing_models()}"
            ),
        }), 503
 
    payload = request.get_json(silent=True) or {}
    image_data = payload.get("image")
    if not image_data:
        return jsonify({
            "success": False,
            "error": "missing_image",
            "message": "Thieu truong 'image' (base64) trong body JSON.",
        }), 400
 
    try:
        pil_image = decode_base64_image(image_data)
    except Exception:
        logger.exception("Khong doc duoc anh dau vao")
        return jsonify({
            "success": False,
            "error": "invalid_image",
            "message": "Du lieu anh khong hop le hoac bi loi khi giai ma base64.",
        }), 400
 
    raw_predictions = registry.predict_all(pil_image)
 
    # FIX: model_loader tra ve {"nhan": ..., "confidence": ..., "raw_output": ...}
    # Lay dung cac key nay de truyen vao get_all_consultations
    predictions = {
        key: {"nhan": info["nhan"], "confidence": info["confidence"]}
        for key, info in raw_predictions.items()
        if "nhan" in info and "confidence" in info
    }
    errors = {
        key: info["error"]
        for key, info in raw_predictions.items()
        if "error" in info
    }
 
    consultations = get_all_consultations(predictions)
 
    return jsonify({
        "success": True,
        "disclaimer": DISCLAIMER,
        "results": consultations,
        "errors": errors or None,
    })
 
 
if __name__ == "__main__":
    if not registry.is_ready():
        logger.warning(
            "=> Server van se chay, nhung /api/predict se tra loi 503 cho den "
            "khi ban dat du 4 file .h5 dung ten vao thu muc: %s", MODELS_DIR,
        )
    app.run(host="0.0.0.0", port=5000, debug=True)