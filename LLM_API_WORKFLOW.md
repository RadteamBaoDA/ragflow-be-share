# LLM API Workflow and File Guide

## Workflow Overview

This document outlines the refactored asynchronous workflow for LLM completions in the codebase. The system has been optimized to use native asyncio (`async`/`await`) for the critical completion path, moving away from synchronous blocking calls.

### 1. API Endpoints (Entry Points)
The process starts at the API layer, which handles HTTP requests (using Quart) and initiates streaming or non-streaming responses.

*   **Files:**
    *   `api/apps/sdk/session.py`: Handles chat completions for sessions.
    *   `api/apps/conversation_app.py`: Handles conversation-based completions.

*   **Refactor:**
    *   Endpoints now use `async def` and `async for` directly.
    *   Removed `stream_generator` thread wrappers.
    *   `Response` objects are initialized with async generators for streaming.

### 2. Service Layer (Business Logic)
The API calls the Service layer, which orchestrates retrieval (RAG) and model interaction.

*   **Files:**
    *   `api/db/services/dialog_service.py`: Core logic for dialogs.
        *   `chat`: Main async generator function. Handles RAG flow (query refinement, keyword extraction, retrieval, completion).
        *   `chat_solo`: Simple chat without RAG.
    *   `api/db/services/conversation_service.py`: Wrappers around dialog service, handling database updates.
    *   `api/db/services/llm_service.py`: The `LLMBundle` class.

*   **Refactor:**
    *   `DialogService.chat` is now an async generator.
    *   Helper functions (`keyword_extraction`, `question_proposal`, etc.) are awaited.
    *   **Hybrid Retrieval:** Retrieval logic (e.g., Elasticsearch calls) often remains synchronous or CPU-heavy. These parts are run in threads using `asyncio.to_thread`.
    *   **SyncLLMWrapper:** Since retrieval code running in threads might need to call LLM methods (like `encode` for embedding), and those methods are now async, a `SyncLLMWrapper` is used to bridge the gap by running the async method in a new loop (via `asyncio.run`) within the thread.

### 3. LLM Bundle (Abstraction Layer)
`LLMBundle` abstracts the specific model provider details.

*   **File:** `api/db/services/llm_service.py`

*   **Refactor:**
    *   Methods like `chat`, `chat_streamly`, `encode` are now `async def`.
    *   **Dynamic Dispatch:** Checks if the underlying model method is a coroutine (`inspect.iscoroutinefunction`).
        *   If **Async** (e.g., new LiteLLM): `await self.model.chat(...)`
        *   If **Sync** (e.g., legacy OpenAIEmbed): Wraps in `asyncio.to_thread(self.model.chat, ...)`
    *   This ensures non-blocking behavior regardless of the underlying model implementation.

### 4. Model Layer (LiteLLM Integration)
The lowest layer interacts with external APIs.

*   **File:** `rag/llm/chat_model.py`

*   **Refactor:**
    *   `LiteLLMBase` now uses `litellm.acompletion` for native async IO.
    *   Methods are `async def`.

## File List

The following files are relevant to the LLM API completion workflow:

1.  `api/apps/conversation_app.py`
2.  `api/apps/sdk/session.py`
3.  `api/db/services/dialog_service.py`
4.  `api/db/services/conversation_service.py`
5.  `api/db/services/llm_service.py`
6.  `rag/llm/chat_model.py`
7.  `rag/prompts/generator.py`
8.  `api/utils/api_utils.py` (Contains `SyncLLMWrapper`)
9.  `api/apps/chunk_app.py` (Consumer of LLM services)
10. `api/apps/sdk/doc.py` (Consumer of LLM services)
