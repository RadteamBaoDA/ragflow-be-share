"""
Example: Using RAGFlow's new table chunking feature for large tables

This example demonstrates how to configure RAGFlow to handle large tables
(100-200+ rows) by creating smaller chunks (1 row per chunk) while preserving
data quality through header inclusion.
"""

from ragflow import RAGFlow

# Initialize RAGFlow client
client = RAGFlow(
    api_key="your_api_key",
    base_url="http://localhost/api/v1"
)

# Example 1: Create dataset with optimal table chunking for large tables
print("Example 1: Creating dataset for large financial tables")
dataset = client.create_dataset(
    name="financial_reports_2024",
    chunk_method="naive",
    parser_config={
        # Table chunking configuration
        "table_batch_size": 1,              # 1 row per chunk (optimal for 100-200 row tables)
        "preserve_table_header": True,      # Include headers in each chunk for context
        
        # Text chunking configuration
        "chunk_token_num": 512,             # Token limit for text content
        "delimiter": "\n!?。；！？",         # Sentence delimiters
        
        # PDF parsing configuration
        "layout_recognize": "DeepDOC",      # Use DeepDOC for table recognition
        "task_page_size": 12                # Pages per task
    }
)

# Upload a PDF with large tables
print("Uploading PDF with large tables...")
document = dataset.upload_document(
    file_path="financial_report_Q4_2024.pdf",
    name="Q4 Financial Report"
)

print(f"Document uploaded: {document.id}")
print(f"Expected chunks: ~200 (if table has 200 rows)")

# Example 2: Update existing dataset to use new table chunking
print("\nExample 2: Updating existing dataset")
existing_dataset = client.get_dataset(name="old_dataset")

# Update parser configuration
existing_dataset.update(
    parser_config={
        "table_batch_size": 1,
        "preserve_table_header": True,
        "chunk_token_num": 512,
        "layout_recognize": "DeepDOC"
    }
)

# Re-parse all documents to apply new chunking
print("Re-parsing documents with new configuration...")
existing_dataset.parse_all_documents()

# Example 3: Different configurations for different use cases
print("\nExample 3: Use case specific configurations")

# Use case 3a: Large tables (100-200+ rows) - Maximum precision
large_table_config = {
    "table_batch_size": 1,              # One row per chunk
    "preserve_table_header": True,      # Keep full context
    "chunk_token_num": 512
}

# Use case 3b: Medium tables (20-50 rows) - Balanced approach
medium_table_config = {
    "table_batch_size": 3,              # Three rows per chunk
    "preserve_table_header": True,
    "chunk_token_num": 512
}

# Use case 3c: Small tables (<20 rows) - Keep together
small_table_config = {
    "table_batch_size": 10,             # Ten rows per chunk
    "preserve_table_header": True,
    "chunk_token_num": 512
}

# Create datasets for each use case
large_dataset = client.create_dataset(
    name="large_tables_dataset",
    chunk_method="naive",
    parser_config=large_table_config
)

medium_dataset = client.create_dataset(
    name="medium_tables_dataset",
    chunk_method="naive",
    parser_config=medium_table_config
)

small_dataset = client.create_dataset(
    name="small_tables_dataset",
    chunk_method="naive",
    parser_config=small_table_config
)

print("All datasets created successfully!")

# Example 4: Query with table chunks
print("\nExample 4: Querying with table chunks")

# Create a chat with the large table dataset
chat = client.create_chat(
    name="Financial Analysis Chat",
    dataset_ids=[dataset.id]
)

# Query specific data from table
response = chat.ask(
    question="What was the revenue for Q3 2024?",
    stream=False
)

print(f"Answer: {response['data']['answer']}")
print(f"Retrieved chunks: {len(response['data']['reference'])}")

# Example 5: Monitor chunking results
print("\nExample 5: Check chunking statistics")
dataset_info = client.get_dataset(dataset.id)
print(f"Total chunks: {dataset_info.chunk_num}")
print(f"Total tokens: {dataset_info.token_num}")
print(f"Documents: {len(dataset_info.documents)}")

# Example 6: Batch processing multiple documents
print("\nExample 6: Batch upload with optimized table chunking")
documents_to_upload = [
    "financial_report_2023.pdf",
    "financial_report_2024_Q1.pdf",
    "financial_report_2024_Q2.pdf",
    "financial_report_2024_Q3.pdf",
    "financial_report_2024_Q4.pdf"
]

for doc_path in documents_to_upload:
    doc = dataset.upload_document(file_path=doc_path)
    print(f"Uploaded: {doc_path} -> {doc.id}")

print("\nAll examples completed!")

# Tips for production use:
print("\n=== Tips for Production ===")
print("1. Start with table_batch_size=1 for large tables")
print("2. Monitor vector database size (1 row = 1 vector)")
print("3. Use preserve_table_header=True for better retrieval")
print("4. Adjust based on your table size distribution")
print("5. Consider vector DB indexing optimization for many chunks")
print("6. Test retrieval quality with sample queries")
