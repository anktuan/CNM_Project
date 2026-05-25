from src.processing.extract_entities import extract_events


def test_extract_events_detects_disease_district_and_cases():
    text = "Quận 8 ghi nhận 120 ca sốt xuất huyết trong tuần qua."

    events = extract_events(text)

    assert len(events) == 1
    assert events[0].disease == "Sốt xuất huyết"
    assert events[0].district == "Quận 8"
    assert events[0].cases == 120


def test_extract_events_defaults_to_hcm_when_no_district():
    text = "TP.HCM ghi nhận 45 ca tay chân miệng."

    events = extract_events(text)

    assert events[0].disease == "Tay chân miệng"
    assert events[0].district == "TP. Hồ Chí Minh"
    assert events[0].cases == 45


def test_extract_events_detects_other_vietnam_province():
    text = "Đồng Nai ghi nhận 230 ca cúm trong tháng này."

    events = extract_events(text)

    assert events[0].disease == "Cúm"
    assert events[0].district == "Đồng Nai"
    assert events[0].cases == 230


def test_extract_events_skips_generic_sentence_without_location():
    text = "Ghi nhận 916 ca tay chân miệng trong tuần 20."

    events = extract_events(text)

    assert events == []
