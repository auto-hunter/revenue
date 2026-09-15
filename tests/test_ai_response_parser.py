import pytest

from services.ai_extractor import parse_json_response


def test_parses_plain_json_array():
    assert parse_json_response('[{"거래처": "테스트"}]') == [{"거래처": "테스트"}]


def test_parses_markdown_fenced_json():
    assert parse_json_response('```json\n[{"총중량": 10}]\n```') == [{"총중량": 10}]


def test_rejects_non_array_response():
    with pytest.raises(ValueError):
        parse_json_response('{"거래처": "테스트"}')
