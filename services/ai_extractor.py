from __future__ import annotations

import json
import time

from google import genai

from models.schemas import PageAnalysis, PageError, TransactionRecord
from prompts.extraction_prompt import TRANSACTION_EXTRACTION_PROMPT
from services.document_parser import DocumentPage


def parse_json_response(raw_text: str) -> list[dict]:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:-1] if lines and lines[-1].strip() == "```" else lines[1:]
        text = "\n".join(lines).strip()
    data = json.loads(text)
    if not isinstance(data, list):
        raise ValueError("AI 응답의 최상위 값이 배열이 아닙니다.")
    return data


class GeminiExtractor:
    def __init__(self, api_key: str, model: str = "models/gemini-3.5-flash-lite", max_retries: int = 2):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.max_retries = max_retries

    def extract_page(self, page: DocumentPage) -> PageAnalysis:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=[TRANSACTION_EXTRACTION_PROMPT, page.image],
                )
                rows = parse_json_response(response.text or "")
                records = [
                    TransactionRecord.model_validate(
                        {**row, "source_file": page.source_file, "page_number": page.page_number}
                    )
                    for row in rows
                ]
                return PageAnalysis(records=records)
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2**attempt)

        return PageAnalysis(error=PageError(
            source_file=page.source_file,
            page_number=page.page_number,
            message=str(last_error),
        ))
