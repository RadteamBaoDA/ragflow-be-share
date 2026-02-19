#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
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
"""
Lightweight language detection utilities.

Goals:
- Better accuracy on common languages without external dependencies.
- Fast under high concurrency (bounded scan + memoized core).
- Deterministic output for query-language routing.
"""

from __future__ import annotations

import asyncio
import re
from functools import lru_cache


_QUOTE_PATTERNS = (
    re.compile(r'"[^"]*"'),
    re.compile(r"'[^']*'"),
    re.compile(r"「[^」]*」"),
    re.compile(r"『[^』]*』"),
    re.compile(r"\u2018[^\u2019]*\u2019"),
)
_ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")
_WS_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[a-zA-Z]+")

_VIETNAMESE_UNIQUE = set(
    "ăđơưĂĐƠƯ"
    "ặẳẵắằậẩẫấầ"
    "ợởỡớờộổỗốồ"
    "ựửữứừ"
    "ẶẲẴẮẰẬẨẪẤẦ"
    "ỢỞỠỚỜỘỔỖỐỒ"
    "ỰỬỮỨỪ"
)
_VIETNAMESE_COMMON = set(
    "ạảẹẻịỉọỏụủỵỷ"
    "ẠẢẸẺỊỈỌỎỤỦỴỶ"
)

_LANG_STOPWORDS = {
    "English": {
        "the", "is", "are", "what", "how", "why", "who", "where", "when", "which",
        "can", "could", "would", "should", "do", "does", "did", "and", "or",
        "to", "of", "in", "on", "for", "with", "please", "explain", "tell",
    },
    "Spanish": {
        "el", "la", "los", "las", "que", "como", "por", "para", "con", "una", "un",
        "es", "son", "hola", "donde", "cuando", "porque",
    },
    "French": {
        "le", "la", "les", "de", "des", "est", "sont", "que", "pour", "avec",
        "une", "un", "bonjour", "comment", "quoi",
    },
    "German": {
        "der", "die", "das", "und", "ist", "sind", "wie", "was", "mit", "fur",
        "ein", "eine", "danke",
    },
    "Portuguese": {
        "o", "a", "os", "as", "que", "como", "para", "com", "uma", "um", "por",
        "obrigado", "ola",
    },
    "Italian": {
        "il", "lo", "la", "gli", "le", "che", "come", "per", "con", "una", "un",
        "ciao", "grazie",
    },
}


def _count_stopword_hits(tokens: list[str]) -> tuple[str | None, int]:
    if not tokens:
        return None, 0
    best_lang = None
    best_hits = 0
    for lang, words in _LANG_STOPWORDS.items():
        hits = 0
        for t in tokens:
            if t in words:
                hits += 1
        if hits > best_hits:
            best_lang = lang
            best_hits = hits
    return best_lang, best_hits


def extract_first_sentence_for_detection(
    text: str,
    max_words: int = 10,
    max_chars: int = 160,
) -> str:
    """
    Extract a small, language-rich prefix for language detection.

    Rules:
    - First segment split by newline or dot-like sentence delimiter.
    - Then cap to first `max_words` words.
    - Strip quoted fragments/acronyms to reduce noise.
    """
    if text is None:
        return ""
    text = str(text).strip()
    if not text:
        return ""

    if max_chars > 0 and len(text) > max_chars:
        text = text[:max_chars]

    split_pos = len(text)
    for delim in ("\n", ".", "。", "！", "？", "!", "?"):
        pos = text.find(delim)
        if pos != -1 and pos + 1 < split_pos:
            split_pos = pos + 1
    sentence = text[:split_pos]

    for pattern in _QUOTE_PATTERNS:
        sentence = pattern.sub("", sentence)
    sentence = _ACRONYM_RE.sub("", sentence)
    sentence = _WS_RE.sub(" ", sentence).strip()

    if max_words > 0:
        words = sentence.split()
        if len(words) > max_words:
            sentence = " ".join(words[:max_words])

    return sentence


@lru_cache(maxsize=32768)
def _detect_language_cached(sample: str) -> str | None:
    hiragana = katakana = kanji = 0
    hangul = thai = arabic = devanagari = 0
    cyrillic = greek = 0
    ascii_alpha = latin_ext_alpha = 0
    vietnamese_unique = vietnamese_common = 0
    total_alpha = 0

    for ch in sample:
        code = ord(ch)

        if 0x3040 <= code <= 0x309F:
            hiragana += 1
            total_alpha += 1
            continue
        if 0x30A0 <= code <= 0x30FF:
            katakana += 1
            total_alpha += 1
            continue
        if 0x4E00 <= code <= 0x9FFF:
            kanji += 1
            total_alpha += 1
            continue
        if 0xAC00 <= code <= 0xD7AF or 0x1100 <= code <= 0x11FF:
            hangul += 1
            total_alpha += 1
            continue
        if 0x0E00 <= code <= 0x0E7F:
            thai += 1
            total_alpha += 1
            continue
        if 0x0600 <= code <= 0x06FF or 0x0750 <= code <= 0x077F:
            arabic += 1
            total_alpha += 1
            continue
        if 0x0900 <= code <= 0x097F:
            devanagari += 1
            total_alpha += 1
            continue
        if 0x0400 <= code <= 0x04FF:
            cyrillic += 1
            total_alpha += 1
            continue
        if 0x0370 <= code <= 0x03FF:
            greek += 1
            total_alpha += 1
            continue

        if ch in _VIETNAMESE_UNIQUE:
            vietnamese_unique += 1
            total_alpha += 1
            continue
        if ch in _VIETNAMESE_COMMON:
            vietnamese_common += 1
            total_alpha += 1
            continue

        if ch.isalpha():
            total_alpha += 1
            if code < 128:
                ascii_alpha += 1
            elif 0x00C0 <= code <= 0x024F or 0x1E00 <= code <= 0x1EFF:
                latin_ext_alpha += 1

    if total_alpha == 0:
        return None

    if hangul:
        return "Korean"
    if thai:
        return "Thai"
    if arabic:
        return "Arabic"
    if devanagari:
        return "Hindi"
    if cyrillic:
        return "Russian"
    if greek:
        return "Greek"

    if hiragana or katakana:
        return "Japanese"
    if vietnamese_unique > 0 or vietnamese_common > 0:
        return "Vietnamese"
    if kanji > 0:
        return "Chinese"

    lowered = sample.lower()
    tokens = _TOKEN_RE.findall(lowered)[:24]
    likely_lang, hits = _count_stopword_hits(tokens)
    if likely_lang and hits >= 2:
        return likely_lang

    # Language markers where stopwords are too short/ambiguous.
    if any(c in lowered for c in ("¿", "¡", "ñ")):
        return "Spanish"
    if any(c in lowered for c in ("ß",)):
        return "German"
    if any(c in lowered for c in ("ã", "õ")):
        return "Portuguese"

    if ascii_alpha >= max(4, int(total_alpha * 0.55)):
        return "English"
    if ascii_alpha and not latin_ext_alpha:
        return "English"
    return None


def detect_language(text: str, max_scan_chars: int = 256) -> str | None:
    """
    Detect language from a short text.

    `max_scan_chars` bounds CPU work for high-CCU scenarios.
    """
    if text is None:
        return None
    sample = str(text).strip()
    if not sample:
        return None
    if max_scan_chars > 0 and len(sample) > max_scan_chars:
        sample = sample[:max_scan_chars]
    return _detect_language_cached(sample)


def detect_question_language(
    text: str,
    max_words: int = 10,
    max_chars: int = 160,
    max_scan_chars: int = 256,
) -> str | None:
    """
    Detect question language using first sentence/line and first words only.
    """
    first = extract_first_sentence_for_detection(text, max_words=max_words, max_chars=max_chars)
    return detect_language(first if first else text, max_scan_chars=max_scan_chars)


async def detect_question_language_async(
    text: str,
    max_words: int = 10,
    max_chars: int = 160,
    max_scan_chars: int = 256,
    offload_threshold: int = 2048,
) -> str | None:
    """
    Async-friendly wrapper for high-CCU servers.

    Keeps short requests on-event-loop (lower overhead), and offloads only long
    inputs to worker threads to avoid event-loop stalls.
    """
    if text is None:
        return None
    if len(text) < offload_threshold:
        return detect_question_language(
            text,
            max_words=max_words,
            max_chars=max_chars,
            max_scan_chars=max_scan_chars,
        )
    return await asyncio.to_thread(
        detect_question_language,
        text,
        max_words,
        max_chars,
        max_scan_chars,
    )

