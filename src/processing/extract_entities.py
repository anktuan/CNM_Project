from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re

from src.processing.clean_text import clean_text, normalize_key
from src.locations import find_locations


DISEASE_ALIASES = {
    "Sốt xuất huyết": ["sốt xuất huyết", "dengue", "sốt dengue", "sxh"],
    "Tay chân miệng": ["tay chân miệng", "tay-chân-miệng", "tcm", "hfmd"],
    "Cúm": ["cúm", "cúm a", "cúm b", "influenza", "h1n1", "h5n1"],
    "Sốt rét": ["sốt rét", "malaria"],
    "Sởi": ["sởi", "bệnh sởi", "measles"],
    "Thủy đậu": ["thủy đậu", "trái rạ", "chickenpox"],
    "Đau mắt đỏ": ["đau mắt đỏ", "viêm kết mạc"],
}
NON_VIETNAM_CONTEXT = [
    "châu âu",
    "chau au",
    "europe",
    "toàn cầu",
    "toan cau",
    "thế giới",
    "the gioi",
    "who",
    "cdc mỹ",
    "cdc my",
    "hoa kỳ",
    "hoa ky",
]
VIETNAM_CONTEXT = ["việt nam", "viet nam", "tp.hcm", "tphcm", "hồ chí minh", "ho chi minh", "hà nội", "ha noi"]
EXCLUDED_DISEASE_TERMS = ["chlamydia", "bệnh lậu", "benh lau", "giang mai", "hiv", "aids"]

@dataclass(frozen=True)
class ExtractedEvent:
    disease: str
    district: str
    cases: int | None
    raw_text: str
    event_date: date | None = None
    confidence: float = 0.6


def _find_diseases(text: str) -> list[str]:
    key = normalize_key(text)
    found = []
    for disease, aliases in DISEASE_ALIASES.items():
        if any(normalize_key(alias) in key for alias in aliases):
            found.append(disease)
    return found


def _find_cases(text: str) -> int | None:
    patterns = [
        r"([\d][\d\.,]*)\s*(?:ca|trường hợp)\s+(?:mắc|bệnh|nhiễm)?",
        r"ghi nhận\s+([\d][\d\.,]*)\s*(?:ca|trường hợp)",
        r"có\s+([\d][\d\.,]*)\s*(?:ca|trường hợp)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = match.group(1).replace(".", "").replace(",", "")
            try:
                return int(value)
            except ValueError:
                return None
    return None


def _find_event_date(text: str, default_date: date | None) -> date | None:
    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b", text)
    if not match:
        return default_date
    day = int(match.group(1))
    month = int(match.group(2))
    year_text = match.group(3)
    if year_text:
        year = int(year_text)
        year = 2000 + year if year < 100 else year
    elif default_date:
        year = default_date.year
    else:
        year = date.today().year
    try:
        parsed = date(year, month, day)
    except ValueError:
        return default_date
    if not year_text and parsed > date.today():
        try:
            parsed = date(year - 1, month, day)
        except ValueError:
            return default_date
    return parsed


def split_sentences(text: str) -> list[str]:
    text = clean_text(text)
    chunks = re.split(r"(?<=[.!?。])\s+|(?<=;)\s+", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def extract_events(text: str, default_date: date | None = None, source_confidence: float = 0.6) -> list[ExtractedEvent]:
    events: list[ExtractedEvent] = []
    full_text = clean_text(text)
    article_diseases = _find_diseases(full_text)
    article_districts = find_locations(full_text)
    for sentence in split_sentences(full_text):
        if _is_non_vietnam_context(sentence):
            continue
        sentence_diseases = _find_diseases(sentence)
        if _has_excluded_disease(sentence) and not sentence_diseases:
            continue
        diseases = sentence_diseases or (article_diseases if len(article_diseases) == 1 else [])
        if not diseases:
            continue
        districts = find_locations(sentence) or article_districts
        if not districts:
            continue
        cases = _find_cases(sentence)
        if cases is None:
            continue
        event_date = _find_event_date(sentence, default_date)
        for disease in diseases:
            for district in districts:
                events.append(
                    ExtractedEvent(
                        disease=disease,
                        district=district,
                        cases=cases,
                        raw_text=sentence[:2000],
                        event_date=event_date,
                        confidence=source_confidence,
                    )
                )
    return events


def _is_non_vietnam_context(text: str) -> bool:
    key = normalize_key(text)
    has_foreign = any(normalize_key(token) in key for token in NON_VIETNAM_CONTEXT)
    has_vietnam = any(normalize_key(token) in key for token in VIETNAM_CONTEXT) or bool(find_locations(text))
    return has_foreign and not has_vietnam


def _has_excluded_disease(text: str) -> bool:
    key = normalize_key(text)
    return any(normalize_key(token) in key for token in EXCLUDED_DISEASE_TERMS)
