/* ==========================================================================
   CHỈ TAY AI — script.js
   --------------------------------------------------------------------------
   Chịu trách nhiệm:
   1. Mở webcam + dùng MediaPipe Hands để nhận diện 21 điểm mốc bàn tay
      thời gian thực (KHÔNG phải giả lập — đây là model nhận diện tay thật,
      chạy ngay trong trình duyệt).
   2. Vẽ "khung định vị bàn tay" + hiệu ứng quét đường chỉ tay trên canvas.
   3. Logic giữ tay 3 giây trong khung -> tự động chụp & gửi đi phân tích.
   4. Chế độ tải ảnh lên (thay thế webcam).
   5. Gọi API Python (Flask) ở backend/app.py để lấy kết quả 4 model AI.
   6. Hiển thị kết quả: điểm số, luận giải, điểm nổi bật, lời khuyên.
   ========================================================================== */
 
(() => {
  "use strict";
 
  // ĐỊA CHỈ BACKEND PYTHON — đổi nếu bạn chạy server ở host/port khác.
  const BACKEND_URL = "http://localhost:5000";
 
  const HOLD_DURATION_MS = 3000;
  const GAUGE_CIRCUMFERENCE = 2 * Math.PI * 50; // r=50 trong svg gauge (results card)
  const RING_CIRCUMFERENCE = 2 * Math.PI * 52; // r=52 trong svg hold-ring
 
  // Vùng "khung định vị" mong đợi bàn tay nằm trong đó (tỉ lệ 0-1 theo khung hình
  // GỐC của camera, không phải khung hình đã lật gương trên CSS).
  const GUIDE_BOX = { xMin: 0.26, xMax: 0.74, yMin: 0.08, yMax: 0.95 };
  const MIN_HAND_HEIGHT_RATIO = 0.4; // tay phải đủ lớn (đủ gần camera)
 
  // -------------------------------------------------------------------------
  // DOM refs
  // -------------------------------------------------------------------------
  const els = {
    video: document.getElementById("video"),
    overlayCanvas: document.getElementById("overlayCanvas"),
    captureCanvas: document.getElementById("captureCanvas"),
    handGuide: document.getElementById("handGuide"),
    holdRing: document.getElementById("holdRing"),
    holdRingFill: document.getElementById("holdRingFill"),
    stageStatus: document.getElementById("stageStatus"),
 
    webcamStage: document.getElementById("webcamStage"),
    uploadStage: document.getElementById("uploadStage"),
    modeWebcamBtn: document.getElementById("modeWebcamBtn"),
    modeUploadBtn: document.getElementById("modeUploadBtn"),
 
    dropzone: document.getElementById("dropzone"),
    fileInput: document.getElementById("fileInput"),
    uploadPreview: document.getElementById("uploadPreview"),
 
    btnCapture: document.getElementById("btnCapture"),
    btnRetry: document.getElementById("btnRetry"),
    btnAbout: document.getElementById("btnAbout"),
    btnThemeToggle: document.getElementById("btnThemeToggle"),
 
    statusDot: document.getElementById("statusDot"),
    statusText: document.getElementById("statusText"),
 
    resultsError: document.getElementById("resultsError"),
    resultsGrid: document.getElementById("resultsGrid"),
    errorText: document.getElementById("errorText"),
    disclaimerText: document.getElementById("disclaimerText"),
  };
 
  const overlayCtx = els.overlayCanvas.getContext("2d");
 
  // -------------------------------------------------------------------------
  // State
  // -------------------------------------------------------------------------
  const state = {
    mode: "webcam", // "webcam" | "upload"
    cameraReady: false,
    lastLandmarks: null, // 21 điểm mốc gần nhất từ MediaPipe
    handInFrame: false,
    holdStartedAt: null, // timestamp performance.now() khi bắt đầu giữ tay
    captureTriggered: false, // tránh tự chụp 2 lần cho 1 lần giữ tay
    isProcessing: false,
    uploadDataUrl: null,
    frameTick: 0,
  };
 
  // ============================= TIỆN ÍCH CHUNG ============================
 
  function setStatus(text, level = "idle") {
    els.statusText.textContent = text;
    els.statusDot.classList.remove("is-live", "is-warn");
    if (level === "live") els.statusDot.classList.add("is-live");
    if (level === "warn") els.statusDot.classList.add("is-warn");
  }
 
  function setStageStatus(text) {
    els.stageStatus.textContent = text;
  }
 
  // ============================ WEBCAM + MEDIAPIPE ==========================
 
  async function initWebcamAndHands() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("Trình duyệt không hỗ trợ camera — hãy dùng chế độ Tải ảnh lên.", "warn");
      switchMode("upload");
      return;
    }
 
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          aspectRatio: { ideal: 4 / 3 },
          facingMode: "user",
        },
        audio: false,
      });
    } catch (err) {
      console.error("Không mở được camera:", err);
      setStatus("Không truy cập được camera — hãy cấp quyền hoặc dùng Tải ảnh lên.", "warn");
      switchMode("upload");
      return;
    }
 
    els.video.srcObject = stream;
    await new Promise((resolve) => {
      els.video.onloadedmetadata = () => resolve();
    });
 
    els.overlayCanvas.width = els.video.videoWidth || 640;
    els.overlayCanvas.height = els.video.videoHeight || 480;
 
    state.cameraReady = true;
    setStatus("Camera đã sẵn sàng — đưa bàn tay vào khung.", "live");
    updateCaptureButtonAvailability();
 
    setupMediaPipeHands();
    requestAnimationFrame(drawLoop);
  }
 
  function setupMediaPipeHands() {
    if (typeof Hands === "undefined" || typeof Camera === "undefined") {
      console.warn("Chưa nạp được thư viện MediaPipe Hands (kiểm tra kết nối mạng/CDN).");
      setStatus("Không nạp được mô-đun nhận diện tay — vẫn có thể bấm 'Chụp ảnh' thủ công.", "warn");
      els.btnCapture.disabled = !state.cameraReady;
      return;
    }
 
    const hands = new Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
    });
    hands.setOptions({
      maxNumHands: 1,
      modelComplexity: 1,
      minDetectionConfidence: 0.7,
      minTrackingConfidence: 0.6,
    });
    hands.onResults(onHandsResults);
 
    const camera = new Camera(els.video, {
      onFrame: async () => {
        await hands.send({ image: els.video });
      },
      width: 640,
      height: 480,
    });
    camera.start();
  }
 
  function onHandsResults(results) {
    const landmarks =
      results.multiHandLandmarks && results.multiHandLandmarks.length > 0
        ? results.multiHandLandmarks[0]
        : null;
 
    state.lastLandmarks = landmarks;
    state.handInFrame = landmarks ? isHandWithinGuide(landmarks) : false;
 
    if (state.mode !== "webcam" || state.isProcessing || state.captureTriggered) return;
 
    if (state.handInFrame && state.holdStartedAt === null) {
      state.holdStartedAt = performance.now();
    } else if (!state.handInFrame && state.holdStartedAt !== null) {
      state.holdStartedAt = null;
      els.holdRing.classList.remove("is-active");
      setStageStatus("Đưa bàn tay vào khung để bắt đầu quét…");
      setStatus("Camera đã sẵn sàng — đưa bàn tay vào khung.", "live");
    }
 
    if (state.handInFrame && state.holdStartedAt !== null) {
      setStatus("Đã phát hiện bàn tay — giữ yên trong giây lát…", "live");
    }
  }
 
  /** Kiểm tra bounding-box của 21 điểm mốc có nằm gọn trong GUIDE_BOX không. */
  function isHandWithinGuide(landmarks) {
    let xMin = 1, xMax = 0, yMin = 1, yMax = 0;
    for (const p of landmarks) {
      if (p.x < xMin) xMin = p.x;
      if (p.x > xMax) xMax = p.x;
      if (p.y < yMin) yMin = p.y;
      if (p.y > yMax) yMax = p.y;
    }
    const withinBox = xMin >= GUIDE_BOX.xMin && xMax <= GUIDE_BOX.xMax &&
                       yMin >= GUIDE_BOX.yMin && yMax <= GUIDE_BOX.yMax;
    const heightRatio = yMax - yMin;
    return withinBox && heightRatio >= MIN_HAND_HEIGHT_RATIO;
  }
 
  // ============================ VÒNG LẶP VẼ (60fps) =========================
 
  function drawLoop() {
    state.frameTick++;
    const w = els.overlayCanvas.width;
    const h = els.overlayCanvas.height;
    overlayCtx.clearRect(0, 0, w, h);
 
    // Khung định vị (hand-guide) tự ẩn đi ngay khi phát hiện tay — xem CSS
    // .hand-guide.is-detected — để không còn đường nét nào đè lên bàn tay thật.
    els.handGuide.classList.toggle("is-detected", state.handInFrame);
 
    updateHoldRing();
 
    requestAnimationFrame(drawLoop);
  }
 
  function updateHoldRing() {
    if (state.mode !== "webcam" || state.holdStartedAt === null || state.isProcessing) {
      els.holdRing.classList.remove("is-active");
      return;
    }
    const elapsed = performance.now() - state.holdStartedAt;
    const progress = Math.min(elapsed / HOLD_DURATION_MS, 1);
    els.holdRing.classList.add("is-active");
    els.holdRingFill.style.strokeDashoffset = String(RING_CIRCUMFERENCE * (1 - progress));
    setStageStatus(`Đang giữ yên… ${Math.round(progress * 100)}%`);
 
    if (progress >= 1 && !state.captureTriggered) {
      state.captureTriggered = true;
      captureFromWebcamAndSend();
    }
  }
 
  // ================================ CHỤP ẢNH ================================
 
  function captureFromWebcamAndSend() {
    const w = els.video.videoWidth;
    const h = els.video.videoHeight;
    els.captureCanvas.width = w;
    els.captureCanvas.height = h;
    const ctx = els.captureCanvas.getContext("2d");
    // Lật ngang khi chụp để khớp với hình ảnh gương người dùng nhìn thấy trên màn hình
    ctx.save();
    ctx.translate(w, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(els.video, 0, 0, w, h);
    ctx.restore();
 
    flashStage();
    const dataUrl = els.captureCanvas.toDataURL("image/jpeg", 0.85);
    setStageStatus("Đã chụp ảnh — đang gửi đi phân tích…");
    els.btnRetry.hidden = false;
    sendToBackend(dataUrl);
  }
 
  function flashStage() {
    els.webcamStage.style.transition = "filter 0.1s";
    els.webcamStage.style.filter = "brightness(2.2)";
    setTimeout(() => { els.webcamStage.style.filter = ""; }, 120);
  }
 
  els.btnCapture.addEventListener("click", () => {
    if (state.mode === "webcam") {
      if (!state.cameraReady || state.isProcessing) return;
      state.captureTriggered = true;
      captureFromWebcamAndSend();
    } else if (state.mode === "upload") {
      if (!state.uploadDataUrl || state.isProcessing) return;
      els.btnRetry.hidden = false;
      sendToBackend(state.uploadDataUrl);
    }
  });
 
  els.btnRetry.addEventListener("click", () => {
    state.captureTriggered = false;
    state.holdStartedAt = null;
    state.isProcessing = false;
    els.btnRetry.hidden = true;
    setStageStatus(
      state.mode === "webcam"
        ? "Đưa bàn tay vào khung để bắt đầu quét…"
        : "Chọn một ảnh khác để phân tích lại."
    );
    updateCaptureButtonAvailability();
  });
 
  els.btnAbout.addEventListener("click", () => {
    document.querySelector(".info-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  });
 
  // ================================ CHẾ ĐỘ TẢI ẢNH ===========================
 
  function switchMode(mode) {
    state.mode = mode;
    const isWebcam = mode === "webcam";
    els.modeWebcamBtn.classList.toggle("is-active", isWebcam);
    els.modeWebcamBtn.setAttribute("aria-selected", String(isWebcam));
    els.modeUploadBtn.classList.toggle("is-active", !isWebcam);
    els.modeUploadBtn.setAttribute("aria-selected", String(!isWebcam));
    els.webcamStage.hidden = !isWebcam;
    els.uploadStage.hidden = isWebcam;
    els.btnRetry.hidden = true;
    state.captureTriggered = false;
    state.holdStartedAt = null;
    updateCaptureButtonAvailability();
  }
 
  els.modeWebcamBtn.addEventListener("click", () => switchMode("webcam"));
  els.modeUploadBtn.addEventListener("click", () => switchMode("upload"));
 
  function updateCaptureButtonAvailability() {
    if (state.mode === "webcam") {
      els.btnCapture.disabled = !state.cameraReady || state.isProcessing;
      els.btnCapture.lastChild.textContent = " Chụp ảnh";
    } else {
      els.btnCapture.disabled = !state.uploadDataUrl || state.isProcessing;
      els.btnCapture.lastChild.textContent = " Phân tích ảnh này";
    }
  }
 
  function handleUploadedFile(file) {
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      state.uploadDataUrl = e.target.result;
      els.uploadPreview.src = state.uploadDataUrl;
      els.uploadPreview.hidden = false;
      els.dropzone.hidden = true;
      state.captureTriggered = false;
      els.btnRetry.hidden = true;
      setStageStatus("Ảnh đã sẵn sàng — bấm 'Phân tích ảnh này' để xem kết quả.");
      updateCaptureButtonAvailability();
    };
    reader.readAsDataURL(file);
  }
 
  els.dropzone.addEventListener("click", () => els.fileInput.click());
  els.fileInput.addEventListener("change", (e) => handleUploadedFile(e.target.files[0]));
 
  ["dragover", "dragleave", "drop"].forEach((evt) => {
    els.dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      if (evt === "dragover") els.dropzone.classList.add("is-dragover");
      if (evt === "dragleave") els.dropzone.classList.remove("is-dragover");
      if (evt === "drop") {
        els.dropzone.classList.remove("is-dragover");
        const file = e.dataTransfer.files && e.dataTransfer.files[0];
        handleUploadedFile(file);
      }
    });
  });
 
  // Cho phép quay lại chọn ảnh mới khi click vào ảnh xem trước
  els.uploadPreview.addEventListener("click", () => els.fileInput.click());
 
  // ================================ GỌI API BACKEND ==========================
 
  async function sendToBackend(dataUrl) {
    state.isProcessing = true;
    updateCaptureButtonAvailability();
 
    els.resultsError.hidden = true;
    els.resultsGrid.hidden = true;
    setStatus("Đang gửi ảnh tới 4 mô hình AI…", "live");
 
    try {
      const res = await fetch(`${BACKEND_URL}/api/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: dataUrl }),
      });
 
      const body = await res.json().catch(() => null);
 
      if (!res.ok || !body || !body.success) {
        const msg = (body && body.message) || `Server trả về lỗi (HTTP ${res.status}).`;
        throw new Error(msg);
      }
 
      renderResults(body.results, body.disclaimer, body.errors);
      els.resultsGrid.hidden = false;
      setStatus("Hoàn tất — xem kết quả luận giải phía dưới.", "live");
    } catch (err) {
      console.error("Lỗi khi gọi backend /api/predict:", err);
      els.resultsError.hidden = false;
      els.errorText.textContent =
        `Không lấy được kết quả từ server Python (${BACKEND_URL}). ` +
        `Hãy chắc chắn bạn đã chạy "python app.py" trong thư mục backend và đã đặt đủ 4 file .h5 vào backend/models/. ` +
        `Chi tiết lỗi: ${err.message}`;
      setStatus("Không kết nối được tới server phân tích.", "warn");
    } finally {
      state.isProcessing = false;
      updateCaptureButtonAvailability();
    }
  }
 
  function renderResults(results, disclaimer, errors) {
    if (disclaimer) els.disclaimerText.textContent = disclaimer;
 
    for (const key of ["sinh_dao", "su_nghiep", "tam_dao", "tri_dao"]) {
      const card = document.getElementById(`card-${key}`);
      if (!card) continue;
      const data = results && results[key];
 
      // data-score giờ hiển thị nhãn nhận định (Dài / Ngắn / Trung Bình)
      // data-label hiển thị độ tin cậy (confidence %)
      const nhanEl = card.querySelector("[data-score]");
      const confEl = card.querySelector("[data-label]");
      const luanGiaiEl = card.querySelector("[data-luangiai]");
      const highlightsEl = card.querySelector("[data-highlights]");
      const adviceEl = card.querySelector("[data-advice]");
      const badgeEl = card.querySelector("[data-badge]");
 
      if (!data) {
        const errMsg = (errors && errors[key]) || "Mô hình chưa sẵn sàng.";
        nhanEl.textContent = "—";
        confEl.textContent = "Không có dữ liệu";
        luanGiaiEl.textContent = `Không thể lấy kết quả cho đường này: ${errMsg}`;
        highlightsEl.innerHTML = "";
        adviceEl.textContent = "";
        continue;
      }
 
      // Dùng ma_muc từ backend để tô màu badge
      const MA_MUC_LABEL = { Dai: "Dài", Ngan: "Ngắn", TrungBinh: "Trung Bình" };
      const nhanNgan = MA_MUC_LABEL[data.ma_muc] || data.nhan || "";

      // Cập nhật badge class theo nhận định để đổi màu
      if (badgeEl) {
        badgeEl.classList.remove("is-dai", "is-trungbinh", "is-ngan");
        if (data.ma_muc === "Dai") badgeEl.classList.add("is-dai");
        else if (data.ma_muc === "Ngan") badgeEl.classList.add("is-ngan");
        else badgeEl.classList.add("is-trungbinh");
      }

      nhanEl.textContent = nhanNgan;  

      confEl.textContent = `${data.confidence}% tin cậy`;
      luanGiaiEl.textContent = data.luan_giai;
      adviceEl.textContent = data.loi_khuyen;
 
      highlightsEl.innerHTML = "";
      (data.diem_noi_bat || []).forEach((point) => {
        const li = document.createElement("li");
        li.textContent = point;
        highlightsEl.appendChild(li);
      });
    }
  }
 
  // ============================ GIAO DIỆN SÁNG / TỐI ========================
 
  const THEME_STORAGE_KEY = "chi-tay-ai-theme";
 
  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch (e) {
      // Trình duyệt chặn localStorage (chế độ ẩn danh...) — bỏ qua, không lưu được thì thôi.
    }
  }
 
  els.btnThemeToggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
    applyTheme(current === "light" ? "dark" : "light");
  });
 
  // ================================== KHỞI ĐỘNG ==============================
 
  function init() {
    switchMode("webcam");
    updateCaptureButtonAvailability();
    initWebcamAndHands();
  }
 
  document.addEventListener("DOMContentLoaded", init);
})();
 