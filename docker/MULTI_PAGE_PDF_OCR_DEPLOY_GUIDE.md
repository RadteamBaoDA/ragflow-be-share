# Multi Page-Size PDF OCR Deployment Guide (Docker)

This guide configures RAGFlow for PDFs that contain mixed page sizes in one file (for example: A4 + Architect E pages).

## 1. What to configure

There are 2 layers:

1. Global runtime (Docker env):
- `DEEPDOC_LARGE_PAGE_MAX_ZOOMIN`
- `OCR_DET_LIMIT_SIDE_LEN`
- `OCR_DET_LIMIT_TYPE`
- `TABLE_AUTO_ROTATE` (recommended `true`)

2. Dataset parser config (per knowledge base):
- `large_page_mode`
- `large_page_threshold_pt`
- `large_page_max_zoomin`
- `table_chunk_token_num`
- `table_header_repeat`

## 2. Docker Compose override

Create `docker/docker-compose.override.ocr.yml`:

```yaml
services:
  ragflow-cpu:
    environment:
      DEEPDOC_LARGE_PAGE_MAX_ZOOMIN: "6"
      OCR_DET_LIMIT_SIDE_LEN: "1280"
      OCR_DET_LIMIT_TYPE: "max"
      TABLE_AUTO_ROTATE: "true"

  ragflow-gpu:
    environment:
      DEEPDOC_LARGE_PAGE_MAX_ZOOMIN: "6"
      OCR_DET_LIMIT_SIDE_LEN: "1280"
      OCR_DET_LIMIT_TYPE: "max"
      TABLE_AUTO_ROTATE: "true"
```

Deploy:

```bash
cd docker
docker compose -f docker-compose.yml -f docker-compose.override.ocr.yml up -d
```

## 3. Recommended profiles

### A. Conservative memory (safer)
- `DEEPDOC_LARGE_PAGE_MAX_ZOOMIN=4`
- `OCR_DET_LIMIT_SIDE_LEN=960`
- `OCR_DET_LIMIT_TYPE=max`

### B. Balanced (recommended)
- `DEEPDOC_LARGE_PAGE_MAX_ZOOMIN=6`
- `OCR_DET_LIMIT_SIDE_LEN=1280`
- `OCR_DET_LIMIT_TYPE=max`

### C. High accuracy (higher memory/time)
- `DEEPDOC_LARGE_PAGE_MAX_ZOOMIN=8`
- `OCR_DET_LIMIT_SIDE_LEN=1536`
- `OCR_DET_LIMIT_TYPE=max`

Notes:
- `DEEPDOC_LARGE_PAGE_MAX_ZOOMIN` is guarded to `1..12`.
- Larger values increase OCR quality on very large drawings, but also increase memory and latency.

## 4. Dataset parser_config (Knowledge Base)

Set parser config in KB settings (UI/API/SDK), example:

```json
{
  "layout_recognize": "DeepDOC",
  "chunk_token_num": 512,
  "large_page_mode": true,
  "large_page_threshold_pt": 3000,
  "large_page_max_zoomin": 6,
  "table_chunk_token_num": 256,
  "table_header_repeat": true,
  "table_context_size": 64
}
```

Key points:
- `large_page_mode=true`: enable adaptive zoom for oversized pages.
- `large_page_threshold_pt=3000`: long-edge threshold to trigger large-page behavior.
- `large_page_max_zoomin`: per-dataset cap (still bounded by global guard).
- `table_chunk_token_num`: split large tables into smaller chunks before indexing/LLM.

## 5. Verify after deployment

### Check container logs

```bash
docker logs ragflow-ragflow-cpu-1 2>&1 | grep -i "Large page detected"
```

You should see logs similar to:
- `Large page detected ... adaptive zoom ...`

### Check memory pressure

```bash
docker stats
```

If memory is high:
- reduce `DEEPDOC_LARGE_PAGE_MAX_ZOOMIN`
- reduce `OCR_DET_LIMIT_SIDE_LEN`

### Functional validation
1. Upload one PDF containing mixed page sizes.
2. Parse the document in KB.
3. Check extracted table/text chunks.
4. Confirm large tables are split into smaller chunks.

## 6. Rollback

Remove the override file from deploy command:

```bash
cd docker
docker compose -f docker-compose.yml up -d
```

Or set safer values:
- `DEEPDOC_LARGE_PAGE_MAX_ZOOMIN=4`
- `OCR_DET_LIMIT_SIDE_LEN=960`
