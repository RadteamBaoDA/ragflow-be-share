# LiteLLM Async Refactor Review

## Overview
This document reviews the transition of the `LiteLLM` integration from synchronous to native asynchronous execution.

## Changes

### 1. `rag/llm/chat_model.py`
*   **Previous:** Used `litellm.completion` (synchronous, blocking).
*   **New:** Uses `litellm.acompletion` (asynchronous, non-blocking).
*   **Impact:**
    *   `chat` and `chat_streamly` methods are now `async def`.
    *   Allows high concurrency for IO-bound API calls without blocking the Quart event loop.

### 2. `api/db/services/llm_service.py` (`LLMBundle`)
*   **Logic:**
    *   Added support for async models.
    *   Maintains backward compatibility for synchronous models (e.g., local embeddings, legacy providers) using `asyncio.to_thread`.
    *   `encode`, `chat`, `chat_streamly` are now async methods that dispatch appropriately.

### 3. API & Service Layers
*   **Refactor:**
    *   `DialogService` (and others) updated to `await` model calls.
    *   `DialogService` acts as an async generator for streaming.
    *   `api/apps/*` endpoints consume async generators directly using `async for`.

### 4. Sync/Async Interoperability (`SyncLLMWrapper`)
*   **Problem:** Some logic (like RAG retrieval in `retrieval_test` or `DialogService`) is complex and synchronous. It runs best in a separate thread (`asyncio.to_thread`). However, it needs to call `LLMBundle.encode`, which is now async.
*   **Solution:** `SyncLLMWrapper` (in `api/utils/api_utils.py`) wraps the async model.
    *   When a method like `encode` is called from the synchronous thread, the wrapper uses `asyncio.run()` (or creates a new loop) to execute the coroutine synchronously *within that thread*.
    *   This allows the main event loop to remain free while the thread handles the mixed workload.

## Conclusion
The refactor successfully modernizes the stack to use `asyncio` natively for the critical path, improving performance and scalability under load. Legacy components are safely isolated in threads.
