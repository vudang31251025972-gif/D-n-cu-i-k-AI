# -*- coding: utf-8 -*-
"""
advice_engine.py
-----------------
Bien doi nhan du doan (Dai / Ngan / TrungBinh) tu model AI thanh noi dung
tu van tieng Viet cho 4 duong chi tay.

QUAN TRONG: Ket qua mang tinh chiem nghiem / giai tri, khong phai ket luan
y khoa, tam ly hay tai chinh.
"""

import random

# ---------------------------------------------------------------------------
# CO SO DU LIEU: moi duong co 3 class khop voi du lieu train
# ---------------------------------------------------------------------------

ADVICE_DB = {
    "sinh_dao": {
        "ten_duong": "Đường Sinh Đạo",
        "chu_de": "Sức khỏe & Tuổi thọ",
        "icon": "leaf",
        "classes": [

            {
                "min": 0,
                "max": 35,
                "nhan": "Ngắn (Dưới trung bình)","ma_muc":"Ngan",

                "luan_giai": [
                    "Đường Sinh Đạo hiện khá mảnh, ngắn hoặc đứt đoạn ở vài điểm, cho thấy nguồn năng lượng nền của bạn đang bị phân tán nhiều hơn là được nạp lại. Đây là dấu hiệu cơ thể đang nhắc nhở bạn chậm lại, chứ không phải điều gì đáng lo ngại.",
                    "Giai đoạn này bạn dễ bị cuốn vào nhịp sống gấp, ngủ không đủ hoặc ăn uống thất thường, khiến thể lực phục hồi chậm hơn bình thường."
                ],

                "diem_noi_bat": [
                    "Khả năng nhận biết sớm khi cơ thể quá tải — bạn thường biết trước khi kiệt sức thật sự.",
                    "Sức bền tinh thần tốt, có thể gồng gánh ổn dù thể lực đang yếu."
                ],

                "loi_khuyen": "Hãy ưu tiên giấc ngủ và một bữa ăn đều đặn trong thời gian tới trước khi nghĩ đến việc tập luyện nặng. Một thói quen nhỏ duy trì đều còn quý hơn một kế hoạch lớn bỏ giữa đường."
            },

            {
                "min": 35,
                "max": 70,
                "nhan": "Trung bình (Ổn định)","ma_muc":"TrungBinh",

                "luan_giai": [
                    "Đường Sinh Đạo có độ dài và độ sâu vừa phải, khá liền mạch, phản ánh một nền thể lực ổn định — không bứt phá nhưng cũng không có dấu hiệu cảnh báo rõ rệt.",
                    "Bạn đang ở trạng thái đủ dùng: đáp ứng tốt được nhịp sống hiện tại nhưng chưa có nhiều dư địa dự trữ cho các giai đoạn áp lực kéo dài."
                ],

                "diem_noi_bat": [
                    "Nhịp sinh hoạt khá đều, ít rơi vào trạng thái cực đoan (kiệt sức hoặc lười vận động hẳn).",
                    "Khả năng hồi phục sau mệt mỏi ở mức tốt, chỉ cần thời gian nghỉ ngơi hợp lý."
                ],

                "loi_khuyen": "Đây là thời điểm tốt để xây thêm đệm năng lượng — thêm 15-20 phút vận động nhẹ mỗi ngày hoặc lên lịch kiểm tra sức khỏe định kỳ, để biến sự ổn định hiện tại thành nền tảng lâu dài."
            },

            {
                "min": 70,
                "max": 101,
                "nhan": "Dài (Khá dồi dào đến Xuất sắc)","ma_muc":"Dai",

                "luan_giai": [
                    "Đường Sinh Đạo dài, sâu và kéo dài đẹp gần như không đứt đoạn — hình ảnh đặc trưng gắn liền với một thể trạng dồi dào năng lượng, sức bền vượt trội và khả năng chống chịu tốt trước biến động.",
                    "Bạn có khả năng đáp ứng tốt với những thay đổi đột ngột của nhịp sống và phục hồi rất nhanh sau những giai đoạn bận rộn."
                ],

                "diem_noi_bat": [
                    "Sức đề kháng và khả năng thích nghi với áp lực bên ngoài (thời tiết, lịch trình dày) rất tốt. Ít bị ảnh hưởng bởi những cú sốc ngắn hạn như thiếu ngủ hay đổi múi giờ.",
                    "Tinh thần và thể chất hỗ trợ lẫn nhau tốt, tạo cảm giác tràn đầy năng lượng suốt cả ngày."
                ],

                "loi_khuyen": "Năng lượng dồi dào dễ khiến bạn chủ quan và quên đi giới hạn của cơ thể. Hãy chủ động đặt ra điểm dừng và nghỉ ngơi phòng ngừa, thay vì chỉ chịu nghỉ khi cơ thể đã thực sự kiệt sức."
            }
        ]
    },
    "su_nghiep": {
        "ten_duong": "Đường Sự Nghiệp",
        "chu_de":    "Thành công & Công danh",
        "icon":      "path",
        "classes": [
            {
                "min": 0,
                "max": 35,
                "nhan": "Ngắn (Đang tìm hướng)","ma_muc":"Ngan",

                "luan_giai": [
                    "Đường Sự Nghiệp hiện còn khá ngắn, mờ hoặc chưa định hình rõ một hướng đi cố định — thường gặp ở giai đoạn bạn đang thử nghiệm, chuyển hướng hoặc chưa tìm thấy đúng việc, đúng người. Đây không phải dấu hiệu của sự thiếu năng lực, mà nhiều khả năng bạn đang ở giữa một giai đoạn chuyển tiếp."
                ],

                "diem_noi_bat": [
                    "Sự linh hoạt cao, không bị bó buộc vào một con đường duy nhất — dễ dàng thích nghi khi cơ hội mới xuất hiện.",
                    "Khả năng học hỏi nhanh từ những thử nghiệm chưa thành công."
                ],

                "loi_khuyen": "Thay vì cố tìm một kế hoạch 5 năm hoàn hảo ngay từ đầu, hãy chọn một bước đi nhỏ, cụ thể trong 1-2 tháng tới để kiểm chứng hướng đi. Sự rõ ràng thường đến từ hành động, không phải từ suy nghĩ thêm."
            },

            {
                "min": 35,
                "max": 70,
                "nhan": "Trung bình (Tiến triển đều)","ma_muc":"TrungBinh",

                "luan_giai": [
                    "Đường Sự Nghiệp có độ dài vừa phải, khá thẳng và liền mạch, phản ánh một quá trình tích lũy đều đặn — không có cú nhảy vọt quá lớn nhưng cũng không có bước lùi đáng kể. Bạn đang xây dựng nền tảng theo cách bền vững và chắc chắn."
                ],

                "diem_noi_bat": [
                    "Tính kiên trì và khả năng duy trì cam kết dài hạn với công việc.",
                    "Được đánh giá là người đáng tin cậy, có trách nhiệm trong mắt đồng nghiệp và cấp trên."
                ],

                "loi_khuyen": "Đây là thời điểm hợp lý để chủ động đề xuất một dự án hoặc nhận thêm trách nhiệm mới — sự đều đặn và uy tín sẵn có là lợi thế lớn để bạn được tin tưởng giao phó cơ hội."
            },

            {
                "min": 70,
                "max": 101,
                "nhan": "Dài (Nhiều cơ hội & Bứt phá)","ma_muc":"Dai",

                "luan_giai": [
                    "Đường Sự Nghiệp rõ nét, dài sâu và vươn thẳng lên gần gốc các ngón tay (có thể đi kèm nhánh phụ hướng lên) — đây là hình ảnh thường gắn với giai đoạn thành quả rõ rệt, nhiều cơ hội lớn mở ra nhờ mạng lưới quan hệ hoặc sự công nhận xứng đáng từ người khác.",
                    "Bạn đang ở vị trí thuận lợi để bứt phá mạnh mẽ và biến những nỗ lực tích lũy trong thời gian qua thành trái ngọt."
                ],

                "diem_noi_bat": [
                    "Khả năng nắm bắt thời cơ tốt, phản xạ nhanh với thay đổi của môi trường làm việc.",
                    "Năng lực lãnh đạo, khả năng tạo ảnh hưởng cao và biết biến áp lực thành động lực tiến lên."
                ],

                "loi_khuyen": "Khi mọi thứ thuận lợi, đừng chờ đợi sự chắc chắn 100% mới hành động và hãy nhớ dành thời gian ghi nhận chính mình. Hãy chủ động lên tiếng, kết nối và chia sẻ thành quả với những người đã hỗ trợ — thành công bền vững luôn cần một mạng lưới quan hệ tốt đi cùng."
            }
        ]
    },

    "tam_dao": {
        "ten_duong": "Đường Tâm Đạo",
        "chu_de":    "Tình duyên & Cảm xúc",
        "icon":      "heart",
        "classes": [
            {
                "min": 0,
                "max": 35,
                "nhan": "Ngắn (Cần lắng nghe bản thân)","ma_muc":"Ngan",

                "luan_giai": [
                    "Đường Tâm Đạo hiện hơi ngắn hoặc đứt đoạn, cho thấy đời sống cảm xúc gần đây có những khoảng lặng hoặc xáo trộn nhỏ — có thể bạn đang xu hướng giữ cảm xúc cho riêng mình nhiều hơn là chia sẻ ra bên ngoài. Đây là giai đoạn bạn cần thời gian quay về bên trong."
                ],

                "diem_noi_bat": [
                    "Khả năng tự nhận biết cảm xúc của chính mình khá tốt, dù chưa hẳn đã muốn bộc lộ ra ngoài.",
                    "Có ranh giới cá nhân rõ ràng, không dễ bị cuốn theo hay bị thao túng bởi cảm xúc của người khác."
                ],

                "loi_khuyen": "Hãy cho phép mình một khoảng thời gian không cần giải thích với ai cả. Khi thế giới nội tâm đã ổn định trở lại, việc kết nối với người xung quanh sẽ tự nhiên hơn là cố gắng ép buộc."
            },

            {
                "min": 35,
                "max": 70,
                "nhan": "Trung bình (Hài hòa)","ma_muc":"TrungBinh",

                "luan_giai": [
                    "Đường Tâm Đạo có độ dài và độ cong vừa phải, khá liền mạch — phản ánh một trạng thái cảm xúc tương đối hài hòa, biết cân bằng giữa cho và nhận trong các mối quan hệ.",
                    "Bạn không quá nồng nhiệt, vồ vập cũng không quá khép kín, lạnh lùng mà giữ được một nhịp ổn định, giúp các mối quan hệ phát triển lâu dài."
                ],

                "diem_noi_bat": [
                    "Khả năng lắng nghe tốt, tạo cảm giác an toàn và tin cậy cho người đối diện khi chia sẻ.",
                    "Giữ được sự tỉnh táo, ít để cảm xúc nhất thời chi phối các quyết định quan trọng."
                ],

                "loi_khuyen": "Sự hài hòa hiện tại là bệ phóng rất tốt để bạn chủ động hơn. Hãy thử mở lòng, chia sẻ một điều bạn vẫn giữ kín với người mình thực sự tin tưởng thay vì chỉ thụ động chờ họ mở lời trước."
            },

            {
                "min": 70,
                "max": 101,
                "nhan": "Dài (Nồng nhiệt & Sâu sắc)","ma_muc":"Dai",

                "luan_giai": [
                    "Đường Tâm Đạo dài, sâu và rõ nét, cong hướng lên đẹp — dấu hiệu của một người có đời sống nội tâm phong phú, chân thành, giàu tình cảm và có khả năng yêu thương sâu sắc, bền lâu.",
                    "Bạn dễ dàng tạo được kết nối sâu sắc ở mức độ tinh thần với người khác, không thích những mối quan hệ hời hợt hay nhất thời."
                ],

                "diem_noi_bat": [
                    "Khả năng đồng cảm cao, dễ dàng nhận ra cảm xúc thật và thấu hiểu người xung quanh.",
                    "Có sức hút tự nhiên trong giao tiếp, lòng trung thành và sự kiên định trong tình cảm ở mức rất cao."
                ],

                "loi_khuyen": "Tình cảm sâu sắc đôi khi khiến bạn kỳ vọng quá nhiều ở đối phương hoặc dễ bị cảm xúc dẫn dắt. Hãy giữ một phần lý trí khi đưa ra quyết định lớn, cho mối quan hệ thời gian để chứng minh và hãy nói rõ điều bạn mong đợi thay vì để họ phải tự đoán."
            }
        ]
    },

    "tri_dao": {
        "ten_duong": "Đường Trí Đạo",
        "chu_de":    "Trí tuệ & Tư duy",
        "icon":      "eye",
        "classes": [
            {
                "min": 0,
                "max": 35,
                "nhan": "Ngắn (Cần thời gian tập trung)","ma_muc":"Ngan",

                "luan_giai": [
                    "Đường Trí Đạo hiện khá ngắn hoặc có vài điểm gãy nhỏ, cho thấy tâm trí gần đây dễ bị phân tán bởi quá nhiều luồng thông tin hoặc phải xử lý nhiều việc cùng một lúc. Đây hoàn toàn không phải hạn chế về năng lực, mà là dấu hiệu bạn cần một không gian yên tĩnh hơn để tư duy sâu."
                ],

                "diem_noi_bat": [
                    "Khả năng xử lý đa nhiệm (multitask) tương đối linh hoạt và nhanh nhạy trong thời gian ngắn.",
                    "Tư duy cởi mở, không định kiến, dễ dàng tiếp nhận các góc nhìn hoặc ý tưởng mới."
                ],

                "loi_khuyen": "Hãy thử chặn riêng từ 30-45 phút mỗi ngày (tắt thông báo, không gián đoạn) chỉ để tập trung giải quyết một việc duy nhất. Trí tuệ sắc bén thường cần một khoảng lặng để bộc lộ, chứ không cần nạp thêm thông tin nhiễu."
            },

            {
                "min": 35,
                "max": 70,
                "nhan": "Trung bình (Tư duy ổn định)","ma_muc":"TrungBinh",

                "luan_giai": [
                    "Đường Trí Đạo thẳng và có độ dài rõ ràng vừa phải, phản ánh một kiểu tư duy thực tế, có hệ thống và logic — bạn luôn ra quyết định dựa trên việc cân nhắc các dữ kiện hợp lý hơn là dựa vào cảm tính.",
                    "Đây là một nền tảng tư duy vô cùng chắc chắn, cực kỳ phù hợp để xử lý các vấn đề phức tạp đòi hỏi sự kiên nhẫn."
                ],

                "diem_noi_bat": [
                    "Khả năng phân tích vấn đề theo từng bước rõ ràng, mạch lạc, ít bị cuốn theo cảm xúc nhất thời.",
                    "Có tư duy logic tốt, đặc biệt mạnh khi làm việc với các vấn đề có cấu trúc, quy trình rõ ràng."
                ],

                "loi_khuyen": "Nền tư duy ổn định này là lợi thế lớn của bạn. Hãy thử áp dụng nó vào một công việc hoặc dự án mà bạn vẫn đang trì hoãn bấy lâu nay vì lý do chưa đủ thông tin — thực ra, bạn đã có đủ dữ liệu để quyết định rồi."
            },

            {
                "min": 70,
                "max": 101,
                "nhan": "Dài (Sắc bén & Vượt trội)","ma_muc":"Dai",

                "luan_giai": [
                    "Đường Trí Đạo dài, sâu và rõ nét bất thường (có thể hơi nghiêng nhẹ xuống) — hình ảnh đại diện cho một tư duy sắc bén, năng lực tiếp thu nhanh và khả năng sáng tạo, tư duy chiến lược vượt trội.",
                    "Bạn có khả năng kết hợp nhuần nhuyễn giữa lý trí sắc sảo và trực giác nhạy bén, giúp nhìn ra bản chất vấn đề hoặc tìm ra giải pháp nhanh hơn số đông."
                ],

                "diem_noi_bat": [
                    "Tư duy phản biện rất tốt, không dễ bị thuyết phục bởi những lập luận hời hợt bề nổi.",
                    "Có tầm nhìn bức tranh tổng thể trước khi đi vào chi tiết và có khả năng học hỏi liên ngành (kết nối các kiến thức khác nhau) xuất sắc."
                ],

                "loi_khuyen": "Tiềm năng lớn dễ bị lãng phí nếu bạn dàn trải năng lượng vào quá nhiều thứ, hoặc đôi khi bạn dễ mất kiên nhẫn vì thấy mọi việc sao đơn giản với mình mà khó với người khác. Hãy chọn 1-2 lĩnh vực cốt lõi để đầu tư chuyên sâu, đồng thời kiên nhẫn hơn khi truyền đạt ý tưởng của mình cho người xung quanh."
            }
        ]
    },
}

DISCLAIMER = (
    "Kết quả được tạo bởi mô hình AI dựa trên đặc điểm hình ảnh bàn tay, mang tính "
    "chiêm nghiệm - giải trí theo thuật xem chỉ tay dân gian, KHÔNG phải kết luận y khoa, "
    "tâm lý hay tài chính chính xác. Vui lòng không dùng kết quả này để thay thế cho lời "
    "khuyên của chuyên gia trong các lĩnh vực liên quan."
)


# SỬA LỖI HÀM get_consultation
def get_consultation(line_key: str, nhan: str, confidence: float) -> dict:
    if line_key not in ADVICE_DB:
        raise ValueError(f"Khong nhan dien duoc duong chi tay: {line_key!r}")

    info = ADVICE_DB[line_key]

    # DUYỆT QUA LIST để tìm class phù hợp dựa trên nhãn
    # (Giả sử bạn truyền nhãn như: "Ngắn (Dưới trung bình)",...)
    # Hoặc tốt nhất nên đặt key trực tiếp trong dict cho dễ truy xuất.
    target_class = None
    for cls in info["classes"]:
        if cls["ma_muc"] == nhan:
            target_class = cls
            break
            
    # Fallback nếu không tìm thấy
    if not target_class:
        target_class = info["classes"][1] # Lấy "Trung bình" làm mặc định

    return {
        "key": line_key,
        "ten_duong": info["ten_duong"],
        "chu_de": info["chu_de"],
        "icon": info["icon"],
        "nhan": target_class["nhan"],
        "ma_muc": target_class["ma_muc"],
        "confidence": confidence,
        "luan_giai": " ".join(target_class["luan_giai"]),
        "diem_noi_bat": target_class["diem_noi_bat"],
        "loi_khuyen": target_class["loi_khuyen"],
    }


def get_all_consultations(predictions: dict) -> dict:
    """
    predictions: {
        "sinh_dao":  {"nhan": "Dai",  "confidence": 87.3},
        "su_nghiep": {"nhan": "Ngan", "confidence": 62.1},
        ...
    }
    Tra ve dict cung key, gia tri la noi dung tu van day du.
    """
    return {
        key: get_consultation(key, pred["nhan"], pred["confidence"])
        for key, pred in predictions.items()
    }


if __name__ == "__main__":
    # Demo nhanh
    import json
    demo = {
        "sinh_dao":  {"nhan": random.choice(["Dai", "Ngan", "TrungBinh"]), "confidence": round(random.uniform(50, 95), 1)},
        "su_nghiep": {"nhan": random.choice(["Dai", "Ngan", "TrungBinh"]), "confidence": round(random.uniform(50, 95), 1)},
        "tam_dao":   {"nhan": random.choice(["Dai", "Ngan", "TrungBinh"]), "confidence": round(random.uniform(50, 95), 1)},
        "tri_dao":   {"nhan": random.choice(["Dai", "Ngan", "TrungBinh"]), "confidence": round(random.uniform(50, 95), 1)},
    }
    print(json.dumps(get_all_consultations(demo), ensure_ascii=False, indent=2))
    print("\nDISCLAIMER:", DISCLAIMER)
