# Table Chunking Configuration Guide

## Overview

RAGFlow now supports configurable table chunking to handle large tables (100-200+ rows) more efficiently while maintaining data quality during retrieval. This feature allows you to control how table data is split into chunks for embedding and vector storage.

## Key Features

### 1. **Row-Level Granularity**
- **Default behavior**: Each table row becomes a separate chunk (batch_size=1)
- **Benefits**: 
  - Fine-grained retrieval for large tables
  - Faster vector search with smaller chunks
  - Better precision when querying specific data

### 2. **Header Preservation**
- **Default behavior**: Table headers are automatically included in each chunk
- **Benefits**:
  - Maintains context for standalone chunks
  - Improves retrieval quality by preserving column meanings
  - Better understanding during RAG generation

### 3. **Complete Row Boundaries**
- **Guarantee**: Chunks always end at complete row boundaries
- **Benefits**:
  - No data fragmentation within rows
  - Maintains data integrity
  - Cleaner chunk structure

## Configuration Parameters

Add these parameters to your `parser_config` when creating or updating a dataset:

```python
parser_config = {
    # Number of table rows per chunk (default: 1)
    "table_batch_size": 1,
    
    # Whether to include table header in each chunk (default: True)
    "preserve_table_header": True,
    
    # Other existing parameters...
    "chunk_token_num": 512,
    "delimiter": "\n!?。；！？",
    # ...
}
```

### Parameter Details

#### `table_batch_size`
- **Type**: Integer
- **Default**: 1 (row-level granularity)
- **Range**: 1 to number of rows in table
- **Description**: Controls how many table rows are grouped into a single chunk
- **Examples**:
  - `1`: Each row becomes a separate chunk (best for large tables 100-200+ rows)
  - `5`: Groups of 5 rows per chunk (balanced approach)
  - `10`: Groups of 10 rows per chunk (reduces chunk count)

#### `preserve_table_header`
- **Type**: Boolean
- **Default**: True
- **Description**: Whether to prepend table headers to each chunk
- **Impact on retrieval**:
  - `True`: Better context, higher quality retrieval (recommended)
  - `False`: Smaller chunks, but may lose column meaning

## Use Cases

### Large Financial Tables (100-200+ rows)
```python
# Recommended configuration for large tables
parser_config = {
    "table_batch_size": 1,           # One row per chunk
    "preserve_table_header": True,   # Keep headers for context
    "chunk_token_num": 512           # For text content
}
```

**Result**: 
- 200-row table → 200 chunks
- Each chunk contains: header + one data row
- Fast retrieval, high precision

### Medium Tables (20-50 rows)
```python
# Balanced configuration
parser_config = {
    "table_batch_size": 3,           # 3 rows per chunk
    "preserve_table_header": True,
    "chunk_token_num": 512
}
```

**Result**:
- 30-row table → 10 chunks
- Each chunk contains: header + 3 data rows
- Good balance between chunk count and context

### Small Tables (< 20 rows)
```python
# Keep tables together
parser_config = {
    "table_batch_size": 10,          # 10 rows per chunk
    "preserve_table_header": True,
    "chunk_token_num": 512
}
```

**Result**:
- 15-row table → 2 chunks
- Preserves more table context

## API Examples

### Python SDK

```python
from ragflow import RAGFlow

client = RAGFlow(api_key="your_api_key", base_url="http://localhost/api/v1")

# Create dataset with table chunking config
dataset = client.create_dataset(
    name="financial_data",
    chunk_method="naive",  # or "manual", "paper", etc.
    parser_config={
        "table_batch_size": 1,
        "preserve_table_header": True,
        "chunk_token_num": 512,
        "layout_recognize": "DeepDOC"
    }
)

# Upload PDF with large tables
dataset.upload_document(file_path="large_table.pdf")
```

### HTTP API

```bash
curl -X POST "http://localhost/api/v1/datasets" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "financial_data",
    "chunk_method": "naive",
    "parser_config": {
      "table_batch_size": 1,
      "preserve_table_header": true,
      "chunk_token_num": 512,
      "layout_recognize": "DeepDOC"
    }
  }'
```

## Performance Optimization

### Speed vs Quality Trade-off

| Configuration | Chunk Count | Embedding Time | Retrieval Speed | Quality |
|--------------|-------------|----------------|-----------------|---------|
| batch_size=1 | Highest (1x rows) | Slower | Fastest | Highest |
| batch_size=5 | Medium (0.2x rows) | Medium | Medium | High |
| batch_size=10 | Low (0.1x rows) | Fast | Slower | Medium |

### Recommendations

**For 100-200 row tables:**
- ✅ Use `table_batch_size: 1` for best retrieval quality
- ✅ Enable `preserve_table_header: true` for context
- ✅ Consider increasing vector database resources

**For embedding speed optimization:**
- Use batch processing features of your embedding model
- Consider parallel document processing
- Optimize vector database indexing

## Table Format Support

This configuration works with:
- ✅ PDF tables recognized by DeepDOC
- ✅ Excel files (.xlsx, .xls)
- ✅ CSV files
- ✅ HTML tables
- ✅ DOCX tables
- ✅ Markdown tables

## Chunk Structure Example

For a table with headers `[Name, Age, City]` and batch_size=1:

**Input Table:**
```
Name    | Age | City
--------|-----|--------
Alice   | 25  | NYC
Bob     | 30  | LA
Charlie | 35  | SF
```

**Output Chunks (3 chunks total):**

**Chunk 1:**
```
Name; Age; City； Alice; 25; NYC
```

**Chunk 2:**
```
Name; Age; City； Bob; 30; LA
```

**Chunk 3:**
```
Name; Age; City； Charlie; 35; SF
```

Each chunk is independently searchable and contains full context.

## Migration Guide

### Existing Datasets

To apply new table chunking to existing datasets:

1. **Update parser configuration:**
```python
dataset.update(parser_config={
    "table_batch_size": 1,
    "preserve_table_header": True
})
```

2. **Re-parse documents:**
```python
# Re-parse all documents in dataset
dataset.parse_all_documents()
```

### Default Behavior

- **Before**: Tables were chunked in batches of 10 rows without headers
- **After**: Tables are chunked row-by-row with headers preserved
- **Backward compatibility**: Old datasets continue to work; new setting only applies to new/re-parsed documents

## Troubleshooting

### Issue: Too many chunks generated
**Solution**: Increase `table_batch_size` to reduce chunk count
```python
parser_config = {"table_batch_size": 5}  # Group more rows together
```

### Issue: Retrieval missing context
**Solution**: Ensure `preserve_table_header` is enabled
```python
parser_config = {"preserve_table_header": True}
```

### Issue: Chunks too large for embedding model
**Solution**: Reduce `table_batch_size` or adjust `chunk_token_num`
```python
parser_config = {
    "table_batch_size": 1,
    "chunk_token_num": 256  # Smaller token limit
}
```

## Best Practices

1. **Start with defaults** (batch_size=1, preserve_header=True)
2. **Monitor chunk counts** in your dataset statistics
3. **Test retrieval quality** with sample queries
4. **Adjust based on table size** and retrieval needs
5. **Consider vector database capacity** for large datasets

## Related Documentation

- [Dataset Configuration Guide](./configurations.md)
- [Chunking Methods Overview](../chunking_methods.md)
- [PDF Parsing Options](./pdf_parsing.md)
- [API Reference](../../references/python_api_reference.md)
