from __future__ import annotations

from src.processing.clean_text import normalize_key


LOCATION_COORDINATES: dict[str, tuple[float, float]] = {
    "TP. Hồ Chí Minh": (10.8231, 106.6297),
    "Thành phố Thủ Đức": (10.8494, 106.7537),
    "Quận 1": (10.7757, 106.7004),
    "Quận 3": (10.7844, 106.6840),
    "Quận 4": (10.7592, 106.7047),
    "Quận 5": (10.7540, 106.6634),
    "Quận 6": (10.7460, 106.6357),
    "Quận 7": (10.7340, 106.7216),
    "Quận 8": (10.7241, 106.6286),
    "Quận 10": (10.7732, 106.6679),
    "Quận 11": (10.7629, 106.6501),
    "Quận 12": (10.8672, 106.6413),
    "Bình Thạnh": (10.8106, 106.7097),
    "Bình Tân": (10.7653, 106.6031),
    "Gò Vấp": (10.8387, 106.6653),
    "Phú Nhuận": (10.7992, 106.6803),
    "Tân Bình": (10.8016, 106.6520),
    "Tân Phú": (10.7901, 106.6289),
    "Bình Chánh": (10.7050, 106.5760),
    "Cần Giờ": (10.4114, 106.9547),
    "Củ Chi": (10.9733, 106.4933),
    "Hóc Môn": (10.8833, 106.5833),
    "Nhà Bè": (10.6956, 106.7047),
    "Hà Nội": (21.0285, 105.8542),
    "Hải Phòng": (20.8449, 106.6881),
    "Đà Nẵng": (16.0544, 108.2022),
    "Cần Thơ": (10.0452, 105.7469),
    "An Giang": (10.5216, 105.1259),
    "Bà Rịa - Vũng Tàu": (10.5417, 107.2429),
    "Bắc Giang": (21.2810, 106.1975),
    "Bắc Kạn": (22.1470, 105.8348),
    "Bạc Liêu": (9.2940, 105.7216),
    "Bắc Ninh": (21.1861, 106.0763),
    "Bến Tre": (10.2434, 106.3756),
    "Bình Định": (13.7820, 109.2197),
    "Bình Dương": (11.3254, 106.4770),
    "Bình Phước": (11.7512, 106.7235),
    "Bình Thuận": (11.0904, 108.0721),
    "Cà Mau": (9.1527, 105.1961),
    "Cao Bằng": (22.6666, 106.2639),
    "Đắk Lắk": (12.7100, 108.2378),
    "Đắk Nông": (12.2646, 107.6098),
    "Điện Biên": (21.3860, 103.0230),
    "Đồng Nai": (11.0686, 107.1676),
    "Đồng Tháp": (10.4938, 105.6882),
    "Gia Lai": (13.8079, 108.1094),
    "Hà Giang": (22.8233, 104.9836),
    "Hà Nam": (20.5835, 105.9229),
    "Hà Tĩnh": (18.3559, 105.8877),
    "Hải Dương": (20.9373, 106.3146),
    "Hậu Giang": (9.7579, 105.6413),
    "Hòa Bình": (20.6861, 105.3131),
    "Hưng Yên": (20.6464, 106.0511),
    "Khánh Hòa": (12.2585, 109.0526),
    "Kiên Giang": (10.0125, 105.0809),
    "Kon Tum": (14.3497, 108.0005),
    "Lai Châu": (22.3862, 103.4703),
    "Lâm Đồng": (11.9404, 108.4583),
    "Lạng Sơn": (21.8537, 106.7615),
    "Lào Cai": (22.4809, 103.9755),
    "Long An": (10.6956, 106.2431),
    "Nam Định": (20.4388, 106.1621),
    "Nghệ An": (19.2342, 104.9200),
    "Ninh Bình": (20.2506, 105.9745),
    "Ninh Thuận": (11.6739, 108.8620),
    "Phú Thọ": (21.2684, 105.2046),
    "Phú Yên": (13.0882, 109.0929),
    "Quảng Bình": (17.6103, 106.3487),
    "Quảng Nam": (15.5394, 108.0191),
    "Quảng Ngãi": (15.1214, 108.8044),
    "Quảng Ninh": (21.0064, 107.2925),
    "Quảng Trị": (16.7500, 107.1907),
    "Sóc Trăng": (9.6025, 105.9739),
    "Sơn La": (21.3270, 103.9141),
    "Tây Ninh": (11.3352, 106.1099),
    "Thái Bình": (20.4463, 106.3366),
    "Thái Nguyên": (21.5672, 105.8252),
    "Thanh Hóa": (19.8067, 105.7852),
    "Thừa Thiên Huế": (16.4637, 107.5909),
    "Tiền Giang": (10.4493, 106.3421),
    "Trà Vinh": (9.8127, 106.2993),
    "Tuyên Quang": (21.7767, 105.2280),
    "Vĩnh Long": (10.2396, 105.9572),
    "Vĩnh Phúc": (21.3089, 105.6049),
    "Yên Bái": (21.7168, 104.8986),
}

LOCATION_ALIASES: dict[str, list[str]] = {
    "TP. Hồ Chí Minh": ["TP.HCM", "TP HCM", "TPHCM", "Hồ Chí Minh", "Thành phố Hồ Chí Minh", "Sài Gòn"],
    "Thành phố Thủ Đức": ["TP Thủ Đức", "Thủ Đức"],
    "Bà Rịa - Vũng Tàu": ["Bà Rịa Vũng Tàu", "BR-VT", "Vũng Tàu"],
    "Thừa Thiên Huế": ["Huế"],
}


def location_names() -> list[str]:
    return list(LOCATION_COORDINATES)


def find_locations(text: str) -> list[str]:
    key = normalize_key(text)
    found: list[str] = []
    for name in LOCATION_COORDINATES:
        candidates = [name, *LOCATION_ALIASES.get(name, [])]
        if any(normalize_key(candidate) in key for candidate in candidates):
            found.append(name)
    return list(dict.fromkeys(found))


def get_location_coordinates(location: str) -> tuple[float | None, float | None]:
    point = LOCATION_COORDINATES.get(location)
    if point:
        return point
    key = normalize_key(location)
    for name, point in LOCATION_COORDINATES.items():
        candidates = [name, *LOCATION_ALIASES.get(name, [])]
        if any(normalize_key(candidate) == key for candidate in candidates):
            return point
    return None, None
