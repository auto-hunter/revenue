from io import BytesIO

import pandas as pd

from models.schemas import PageError, TransactionRecord

COLUMN_LABELS = {
    "product_spec": "품명 및 규격", "gross_weight": "총중량",
    "bobbin_weight": "보빈중량", "net_weight": "실중량", "subtotal": "소계",
    "bobbin_spec": "보빈명세 규격", "bobbin_quantity": "보빈명세 수량",
    "customer": "거래처", "corporate_entity": "거래법인", "transaction_date": "날짜",
    "source_file": "출처 파일", "page_number": "페이지",
}
ONE_DECIMAL_COLUMNS = {"총중량", "보빈중량", "실중량", "소계"}


def create_excel(records: list[TransactionRecord], errors: list[PageError] | None = None) -> bytes:
    """Build an XLSX workbook in memory."""
    result_df = pd.DataFrame([record.model_dump(mode="json") for record in records])
    result_df = result_df.reindex(columns=COLUMN_LABELS).rename(columns=COLUMN_LABELS)
    error_df = pd.DataFrame(
        [error.model_dump() for error in (errors or [])],
        columns=["source_file", "page_number", "message"],
    ).rename(columns={"source_file": "출처 파일", "page_number": "페이지", "message": "오류 내용"})

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result_df.to_excel(writer, sheet_name="추출 결과", index=False)
        if not error_df.empty:
            error_df.to_excel(writer, sheet_name="처리 오류", index=False)
        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            if worksheet.title == "추출 결과":
                for header_cell in worksheet[1]:
                    if header_cell.value in ONE_DECIMAL_COLUMNS:
                        for row_number in range(2, worksheet.max_row + 1):
                            worksheet.cell(row=row_number, column=header_cell.column).number_format = "0.0"
            for cells in worksheet.columns:
                width = min(max(len(str(cell.value or "")) for cell in cells) + 2, 40)
                worksheet.column_dimensions[cells[0].column_letter].width = width
    return output.getvalue()
