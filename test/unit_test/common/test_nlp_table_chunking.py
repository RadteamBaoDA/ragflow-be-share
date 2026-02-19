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

from rag.nlp import tokenize_table


def _doc():
    return {"docnm_kwd": "sample.pdf", "title_tks": "sample", "title_sm_tks": "sample"}


def test_tokenize_table_html_split_with_header_repeat():
    rows = [
        "<tr><th>col_a</th><th>col_b</th></tr>",
        "<tr><td>alpha one</td><td>beta one</td></tr>",
        "<tr><td>alpha two</td><td>beta two</td></tr>",
        "<tr><td>alpha three</td><td>beta three</td></tr>",
        "<tr><td>alpha four</td><td>beta four</td></tr>",
    ]
    html = "<table>" + "".join(rows) + "</table>"
    tbls = [((None, html), [(0, 0.0, 100.0, 0.0, 100.0)])]

    chunks = tokenize_table(tbls, _doc(), True, table_chunk_token_num=18, table_header_repeat=True)

    assert len(chunks) > 1
    assert all(c["doc_type_kwd"] == "table" for c in chunks)
    assert all("<th>" in c["content_with_weight"] for c in chunks)


def test_tokenize_table_html_split_without_header_repeat():
    rows = [
        "<tr><th>name</th><th>value</th></tr>",
        "<tr><td>a</td><td>111</td></tr>",
        "<tr><td>b</td><td>222</td></tr>",
        "<tr><td>c</td><td>333</td></tr>",
        "<tr><td>d</td><td>444</td></tr>",
    ]
    html = "<table>" + "".join(rows) + "</table>"
    tbls = [((None, html), [(0, 0.0, 100.0, 0.0, 100.0)])]

    chunks = tokenize_table(tbls, _doc(), True, table_chunk_token_num=10, table_header_repeat=False)

    assert len(chunks) > 1
    assert "<th>" in chunks[0]["content_with_weight"]
    assert all("<th>" not in c["content_with_weight"] for c in chunks[1:])


def test_tokenize_table_list_rows_split_by_token_budget():
    rows = [
        "col_a: alpha one; col_b: beta one",
        "col_a: alpha two; col_b: beta two",
        "col_a: alpha three; col_b: beta three",
        "col_a: alpha four; col_b: beta four",
    ]
    tbls = [((None, rows), [(0, 0.0, 100.0, 0.0, 100.0)])]

    chunks = tokenize_table(tbls, _doc(), True, table_chunk_token_num=14)

    assert len(chunks) > 1
    assert all(c["doc_type_kwd"] == "table" for c in chunks)
    assert all(c.get("content_with_weight") for c in chunks)
