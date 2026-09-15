from google import genai
import pypdfium2 as pdfium
import pandas as pd
import json
import glob
import time  # 무료 티어 분당 제한(RPM) 방지용

# 발급받은 API 키 입력
client = genai.Client(api_key="AQ.Ab8RN6JyAnaBJ_NE42PqjpRg1ZYhLjn1d_Cic3WxIHt-sL_Mgg")

# 2. 프롬프트 정의
system_prompt = """
너는 거래명세표 데이터 추출 전문가야.
첨부된 이미지에서 다음 9개 항목을 추출해서 완벽한 JSON 배열(Array) 형태로만 출력해.
마크다운 형식(```json)이나 다른 설명 없이 오직 pure JSON 텍스트만 반환해.

[추출 규칙
1. 하나의 '품명 및 규격' 아래에 여러 개의 중량(총중량, 보빈중량, 실중량) 데이터가 나열될 수 있습니다.
2. '품명 및 규격', '소계', '보빈명세 규격', '보빈명세 수량' 항목이 아래 행에서 빈칸으로 되어 있다면, 새로운 값이 나타나기 전까지 바로 위에서 추출한 값을 동일하게 복사하여 채워 넣으세요.
3. 추출한 각 중량 행마다 하나의 개별 JSON 객체(Object)를 생성하세요.
4. '거래처'와 '날짜'는 문서 좌측 상단에 있습니다. 이 두 항목은 공통 정보이므로, 생성되는 모든 JSON 객체 안에 동일한 값으로 포함시켜 주세요.

[추출 항목]
1. 품명 및 규격
2. 총중량
3. 보빈중량
4. 실중량
5. 소계
6. 보빈명세 규격
7. 보빈명세 수량
8. 거래처
9. 날짜

[출력 형식 예시]
[
  {"품명 및 규격": "34/0.18TA", "총중량": 367.0, "보빈중량": 48.0, "실중량": 319.0, "소계": 1026.5, "보빈명세 규격": 610, "보빈명세 수량": 3, "거래처": "일산전선", "날짜": "2026-08-26"},
  {"품명 및 규격": "34/0.18TA", "총중량": 396.5, "보빈중량": 41.5, "실중량": 355.0, "소계": 1026.5, "보빈명세 규격": 610, "보빈명세 수량": 3, "거래처": "일산전선", "날짜": "2026-08-26"}
]
"""

all_results = []
pdf_files = glob.glob("./*.pdf")

for file in pdf_files:
    print(f"AI 분석 중: {file}")
    pdf = pdfium.PdfDocument(file)

    # PDF 내의 모든 페이지를 순회하도록 반복문 추가
    for page_index in range(len(pdf)):
        print(f" - {page_index + 1}페이지 처리 중...")
        image_pil = pdf[page_index].render(scale=2).to_pil()

        # 모델 호출
        response = client.models.generate_content(
            model='models/gemini-3.5-flash-lite',
            contents=[system_prompt, image_pil]
        )

        try:
            raw_text = response.text.strip()
            clean_json_text = raw_text.replace("```json", "").replace("```", "").strip()

            json_data = json.loads(clean_json_text)

            for item in json_data:
                # 출처 파일에 몇 번째 페이지인지 기록해두면 나중에 검증하기 좋습니다.
                item['출처 파일'] = f"{file}_page_{page_index + 1}"
                all_results.append(item)

        except json.JSONDecodeError:
            print(f"JSON 파싱 실패 ({file} - {page_index + 1}페이지):\n", response.text)

        # API 호출 속도 조절 (페이지 당 대기)
        time.sleep(5)

# 최종 엑셀 저장
if all_results:
    df = pd.DataFrame(all_results)
    df.to_excel("AI_스캔파싱_결과.xlsx", index=False)
    print("완료! 'AI_스캔파싱_결과.xlsx' 파일이 생성되었습니다.")