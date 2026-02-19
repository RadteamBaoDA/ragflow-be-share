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

from api.utils.api_utils import get_parser_config


def test_get_parser_config_contains_table_and_large_page_defaults():
    cfg = get_parser_config("naive", None)
    assert cfg["table_chunk_token_num"] == 256
    assert cfg["table_header_repeat"] is True
    assert cfg["large_page_mode"] is True
    assert cfg["large_page_threshold_pt"] == 3000
    assert cfg["large_page_max_zoomin"] == 6


def test_get_parser_config_keeps_explicit_overrides():
    cfg = get_parser_config(
        "naive",
        {
            "table_chunk_token_num": 120,
            "table_header_repeat": False,
            "large_page_mode": False,
            "large_page_threshold_pt": 4200,
            "large_page_max_zoomin": 8,
        },
    )
    assert cfg["table_chunk_token_num"] == 120
    assert cfg["table_header_repeat"] is False
    assert cfg["large_page_mode"] is False
    assert cfg["large_page_threshold_pt"] == 4200
    assert cfg["large_page_max_zoomin"] == 8
