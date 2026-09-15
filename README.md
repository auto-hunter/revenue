# 거래명세표 AI 추출기

스캔된 PDF/JPG/PNG 거래명세표를 Gemini로 분석하고 Excel로 내려받는 Streamlit 앱입니다.

## 설정과 실행

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

기존 코드에 노출됐던 API 키는 폐기하고 새 키를 발급하세요. `.streamlit/secrets.toml.example`을
`.streamlit/secrets.toml`로 복사한 뒤 새 키를 입력합니다. 환경변수 `GEMINI_API_KEY`도 지원합니다.

## 구조

- `app.py`: 업로드, 진행률, 결과 편집, 다운로드 UI
- `services/document_parser.py`: PDF와 이미지의 페이지 표준화
- `services/ai_extractor.py`: Gemini 호출, JSON 파싱, 페이지 단위 오류 처리
- `services/excel_exporter.py`: 결과와 오류를 메모리 내 Excel로 생성
- `models/schemas.py`: 서비스 간 데이터 규격과 검증
- `prompts/extraction_prompt.py`: 거래명세표 추출 지침
- `tests/`: 응답 파서와 Excel 생성 자동 검증
