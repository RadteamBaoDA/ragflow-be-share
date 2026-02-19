# Docker Compose Override File List (Selected Commits)

- Commit A: `ad2aaf5c5b6c310915165f33af00628603fd66f3`
- Commit B: `0db393ee30f8dd53e0e4f20a38e050a1adfd6f58`
- Repository root: `/mnt/d/Project/RAG/ragflow-be-share`
- Unique changed files: **15**
- Container code root assumed: `/ragflow`

## Usage

Use the `docker-compose Volume` column in your override file.

## Changed Files

| Relative Path | Changed In Commit(s) | Host Full Path | Container Path | docker-compose Volume |
|---|---|---|---|---|
| `api/apps/chunk_app.py` | `ad2aaf5(M)` | `/mnt/d/Project/RAG/ragflow-be-share/api/apps/chunk_app.py` | `/ragflow/api/apps/chunk_app.py` | `- /mnt/d/Project/RAG/ragflow-be-share/api/apps/chunk_app.py:/ragflow/api/apps/chunk_app.py:ro` |
| `api/apps/sdk/doc.py` | `ad2aaf5(M)` | `/mnt/d/Project/RAG/ragflow-be-share/api/apps/sdk/doc.py` | `/ragflow/api/apps/sdk/doc.py` | `- /mnt/d/Project/RAG/ragflow-be-share/api/apps/sdk/doc.py:/ragflow/api/apps/sdk/doc.py:ro` |
| `api/apps/sdk/session.py` | `ad2aaf5(M)` | `/mnt/d/Project/RAG/ragflow-be-share/api/apps/sdk/session.py` | `/ragflow/api/apps/sdk/session.py` | `- /mnt/d/Project/RAG/ragflow-be-share/api/apps/sdk/session.py:/ragflow/api/apps/sdk/session.py:ro` |
| `api/db/services/dialog_service.py` | `ad2aaf5(M)` | `/mnt/d/Project/RAG/ragflow-be-share/api/db/services/dialog_service.py` | `/ragflow/api/db/services/dialog_service.py` | `- /mnt/d/Project/RAG/ragflow-be-share/api/db/services/dialog_service.py:/ragflow/api/db/services/dialog_service.py:ro` |
| `api/utils/language_utils.py` | `ad2aaf5(A)` | `/mnt/d/Project/RAG/ragflow-be-share/api/utils/language_utils.py` | `/ragflow/api/utils/language_utils.py` | `- /mnt/d/Project/RAG/ragflow-be-share/api/utils/language_utils.py:/ragflow/api/utils/language_utils.py:ro` |
| `rag/prompts/generator.py` | `ad2aaf5(M)` | `/mnt/d/Project/RAG/ragflow-be-share/rag/prompts/generator.py` | `/ragflow/rag/prompts/generator.py` | `- /mnt/d/Project/RAG/ragflow-be-share/rag/prompts/generator.py:/ragflow/rag/prompts/generator.py:ro` |
| `test/unit_test/utils/test_language_utils.py` | `ad2aaf5(A)` | `/mnt/d/Project/RAG/ragflow-be-share/test/unit_test/utils/test_language_utils.py` | `/ragflow/test/unit_test/utils/test_language_utils.py` | `- /mnt/d/Project/RAG/ragflow-be-share/test/unit_test/utils/test_language_utils.py:/ragflow/test/unit_test/utils/test_language_utils.py:ro` |
| `api/utils/api_utils.py` | `0db393e(M)` | `/mnt/d/Project/RAG/ragflow-be-share/api/utils/api_utils.py` | `/ragflow/api/utils/api_utils.py` | `- /mnt/d/Project/RAG/ragflow-be-share/api/utils/api_utils.py:/ragflow/api/utils/api_utils.py:ro` |
| `api/utils/validation_utils.py` | `0db393e(M)` | `/mnt/d/Project/RAG/ragflow-be-share/api/utils/validation_utils.py` | `/ragflow/api/utils/validation_utils.py` | `- /mnt/d/Project/RAG/ragflow-be-share/api/utils/validation_utils.py:/ragflow/api/utils/validation_utils.py:ro` |
| `deepdoc/parser/pdf_parser.py` | `0db393e(M)` | `/mnt/d/Project/RAG/ragflow-be-share/deepdoc/parser/pdf_parser.py` | `/ragflow/deepdoc/parser/pdf_parser.py` | `- /mnt/d/Project/RAG/ragflow-be-share/deepdoc/parser/pdf_parser.py:/ragflow/deepdoc/parser/pdf_parser.py:ro` |
| `deepdoc/vision/ocr.py` | `0db393e(M)` | `/mnt/d/Project/RAG/ragflow-be-share/deepdoc/vision/ocr.py` | `/ragflow/deepdoc/vision/ocr.py` | `- /mnt/d/Project/RAG/ragflow-be-share/deepdoc/vision/ocr.py:/ragflow/deepdoc/vision/ocr.py:ro` |
| `rag/app/naive.py` | `0db393e(M)` | `/mnt/d/Project/RAG/ragflow-be-share/rag/app/naive.py` | `/ragflow/rag/app/naive.py` | `- /mnt/d/Project/RAG/ragflow-be-share/rag/app/naive.py:/ragflow/rag/app/naive.py:ro` |
| `rag/nlp/__init__.py` | `0db393e(M)` | `/mnt/d/Project/RAG/ragflow-be-share/rag/nlp/__init__.py` | `/ragflow/rag/nlp/__init__.py` | `- /mnt/d/Project/RAG/ragflow-be-share/rag/nlp/__init__.py:/ragflow/rag/nlp/__init__.py:ro` |
| `test/unit_test/common/test_nlp_table_chunking.py` | `0db393e(A)` | `/mnt/d/Project/RAG/ragflow-be-share/test/unit_test/common/test_nlp_table_chunking.py` | `/ragflow/test/unit_test/common/test_nlp_table_chunking.py` | `- /mnt/d/Project/RAG/ragflow-be-share/test/unit_test/common/test_nlp_table_chunking.py:/ragflow/test/unit_test/common/test_nlp_table_chunking.py:ro` |
| `test/unit_test/common/test_parser_config_defaults.py` | `0db393e(A)` | `/mnt/d/Project/RAG/ragflow-be-share/test/unit_test/common/test_parser_config_defaults.py` | `/ragflow/test/unit_test/common/test_parser_config_defaults.py` | `- /mnt/d/Project/RAG/ragflow-be-share/test/unit_test/common/test_parser_config_defaults.py:/ragflow/test/unit_test/common/test_parser_config_defaults.py:ro` |
