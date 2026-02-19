#
#  Copyright 2026 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from api.utils.language_utils import (
    detect_language,
    detect_question_language,
    extract_first_sentence_for_detection,
)


def test_extract_first_sentence_newline_and_word_limit():
    text = "This is line one with many words that should be trimmed after ten words\nSecond line"
    extracted = extract_first_sentence_for_detection(text)
    assert extracted == "This is line one with many words that should be"


def test_extract_first_sentence_dot():
    text = "Hello world. This is another sentence."
    extracted = extract_first_sentence_for_detection(text)
    assert extracted == "Hello world."


def test_detect_language_japanese():
    assert detect_language("機械学習とは何ですか？") == "Japanese"


def test_detect_language_vietnamese():
    assert detect_language("Học máy là gì?") == "Vietnamese"


def test_detect_language_korean():
    assert detect_language("안녕하세요 오늘 날씨 어때요?") == "Korean"


def test_detect_language_chinese():
    assert detect_language("人工智能是什么？") == "Chinese"


def test_detect_language_arabic():
    assert detect_language("ما هو التعلم الآلي؟") == "Arabic"


def test_detect_language_english():
    assert detect_language("What is machine learning?") == "English"


def test_detect_question_language_with_noise():
    text = "Explain 'RAGFlow' in detail for API usage.\nIgnore this line."
    assert detect_question_language(text) == "English"

