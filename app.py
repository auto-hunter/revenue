from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from models.schemas import PageError, TransactionRecord
from services.ai_extractor import GeminiExtractor
from services.document_parser import DocumentParseError, parse_document
from services.excel_exporter import COLUMN_LABELS, create_excel


st.set_page_config(page_title="거래명세표 데이터 추출 AI 에이전트", page_icon="📄", layout="wide")
st.title("거래명세표 데이터 추출 AI 에이전트")
st.caption("스캔 PDF 또는 이미지를 분석해 Excel 파일로 변환합니다.")


def get_api_key() -> str | None:
    """Read a key without requiring a local secrets file to exist."""
    environment_key = os.getenv("GEMINI_API_KEY")
    if environment_key:
        return environment_key
    try:
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


uploaded_files = st.file_uploader(
    "분석할 파일을 선택하세요",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
)

if uploaded_files:
    st.write(f"선택된 파일: {len(uploaded_files)}개")

if st.button("분석 시작", type="primary", disabled=not uploaded_files):
    api_key = get_api_key()
    if not api_key:
        st.error("GEMINI_API_KEY가 설정되지 않았습니다. README의 설정 방법을 확인하세요.")
        st.stop()

    extractor = GeminiExtractor(api_key=api_key)
    records: list[TransactionRecord] = []
    errors: list[PageError] = []
    progress = st.progress(0, text="문서를 준비하고 있습니다.")

    parsed_documents = []
    for uploaded_file in uploaded_files:
        try:
            parsed_documents.append((uploaded_file.name, parse_document(uploaded_file)))
        except DocumentParseError as exc:
            errors.append(PageError(source_file=uploaded_file.name, page_number=None, message=str(exc)))

    pages = [page for _, document_pages in parsed_documents for page in document_pages]
    for index, page in enumerate(pages, start=1):
        progress.progress(
            (index - 1) / max(len(pages), 1),
            text=f"{page.source_file} {page.page_number}페이지 분석 중",
        )
        result = extractor.extract_page(page)
        records.extend(result.records)
        if result.error:
            errors.append(result.error)

    progress.progress(1.0, text="분석이 완료되었습니다.")
    st.session_state["records"] = [record.model_dump() for record in records]
    st.session_state["errors"] = [error.model_dump() for error in errors]

if "records" in st.session_state:
    records_df = pd.DataFrame(st.session_state["records"])
    if not records_df.empty:
        records_df = records_df.rename(columns=COLUMN_LABELS)
        st.subheader("추출 결과")
        edited_df = st.data_editor(records_df, use_container_width=True, num_rows="dynamic")

        valid_records: list[TransactionRecord] = []
        validation_errors: list[str] = []
        reverse_labels = {label: field for field, label in COLUMN_LABELS.items()}
        for row_number, row in enumerate(edited_df.rename(columns=reverse_labels).to_dict("records"), start=1):
            cleaned = {key: (None if pd.isna(value) else value) for key, value in row.items()}
            try:
                valid_records.append(TransactionRecord.model_validate(cleaned))
            except Exception as exc:
                validation_errors.append(f"{row_number}행: {exc}")

        if validation_errors:
            st.error("수정된 결과에 유효하지 않은 값이 있습니다.\n\n" + "\n".join(validation_errors))
        else:
            errors = [PageError.model_validate(item) for item in st.session_state.get("errors", [])]
            excel_bytes = create_excel(valid_records, errors)
            st.download_button(
                "Excel 다운로드",
                data=excel_bytes,
                file_name="AI_스캔파싱_결과.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    else:
        st.warning("추출된 데이터가 없습니다.")

    errors = st.session_state.get("errors", [])
    if errors:
        with st.expander(f"처리 오류 {len(errors)}건"):
            st.dataframe(pd.DataFrame(errors), use_container_width=True)
