from __future__ import annotations

import requests

from src.config import settings

GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-001", "gemini-1.5-flash-latest", "gemini-1.5-flash"]


def research_disease(query: str) -> str:
    query = query.strip()
    if not query:
        return "Vui lòng nhập tên bệnh hoặc câu hỏi cần tra cứu."

    context = _search_tavily(query)
    if settings.gemini_api_key:
        answer = _ask_gemini(query, context)
        if answer:
            return answer
    if context:
        return "Thông tin tham khảo từ tìm kiếm:\n\n" + context
    return "Chưa cấu hình GEMINI_API_KEY/TAVILY_API_KEY hoặc chưa lấy được dữ liệu tra cứu."


def _search_tavily(query: str) -> str:
    if not settings.tavily_api_key:
        return ""
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": settings.tavily_api_key,
                "query": f"{query} bệnh truyền nhiễm triệu chứng phòng ngừa điều trị Bộ Y tế WHO",
                "search_depth": "basic",
                "max_results": 5,
                "include_answer": True,
            },
            timeout=settings.request_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        lines = []
        if payload.get("answer"):
            lines.append(str(payload["answer"]))
        for item in payload.get("results", [])[:5]:
            title = item.get("title", "")
            url = item.get("url", "")
            content = item.get("content", "")
            lines.append(f"- {title}: {content} ({url})")
        return "\n".join(lines)
    except Exception as exc:
        return f"Tavily search failed: {exc}"


def _ask_gemini(query: str, context: str) -> str:
    prompt = (
        "Bạn là trợ lý y tế công cộng. Trả lời bằng tiếng Việt, ngắn gọn, có cấu trúc. "
        "Không thay thế tư vấn bác sĩ. Nếu có dữ liệu tìm kiếm, hãy dựa vào đó.\n\n"
        f"Câu hỏi: {query}\n\nNgữ cảnh:\n{context or 'Không có ngữ cảnh tìm kiếm.'}"
    )
    last_error = ""
    for model in GEMINI_MODELS:
        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": settings.gemini_api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=settings.request_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            return payload["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as exc:
            last_error = _safe_error(exc)
    if context:
        return f"Gemini chưa trả lời được ({last_error}).\n\nThông tin tìm kiếm:\n{context}"
    return f"Gemini chưa trả lời được ({last_error})."


def _safe_error(exc: Exception) -> str:
    message = str(exc)
    if "key=" in message:
        message = message.split("?key=", 1)[0]
    return message[:240]
