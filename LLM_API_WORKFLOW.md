# LLM API Workflow and File Guide

## Workflow Overview

This document outlines the (synchronous) workflow for LLM completions in the codebase. The system handles API requests using Quart, but the core LLM execution path relies on synchronous calls (blocking) or is wrapped in threads.

### 1. API Endpoints (Entry Points)
The process starts at the API layer, which handles HTTP requests.

*   **Files:**
    *   `api/apps/sdk/session.py`: Handles chat completions for sessions (`/chats/<chat_id>/completions`, `/chats_openai/...`).
    *   `api/apps/conversation_app.py`: Handles conversation-based completions (`/completion`, `/ask`).

*   **Logic:**
    *   Endpoints validate requests and call services.
    *   Streaming responses use generator functions wrapped in `stream_generator` (a helper that runs the synchronous generator in a thread).

### 2. Service Layer (Business Logic)
The API calls the Service layer, which orchestrates retrieval (RAG) and model interaction.

*   **Files:**
    *   `api/db/services/dialog_service.py`: Core logic for dialogs.
        *   `chat`: Main generator function. Handles RAG flow (query refinement, keyword extraction, retrieval, completion).
        *   `chat_solo`: Simple chat without RAG.
    *   `api/db/services/conversation_service.py`: Wrappers around dialog service, handling database updates.
    *   `api/db/services/llm_service.py`: The `LLMBundle` class.

*   **Workflow:**
    *   `DialogService.chat` orchestrates the process.
    *   It calls `LLMBundle` methods (`chat`, `encode`) synchronously.
    *   Retrieval (`settings.retriever.retrieval`) is also called synchronously.

### 3. LLM Bundle (Abstraction Layer)
`LLMBundle` abstracts the specific model provider details.

*   **File:** `api/db/services/llm_service.py`

*   **Logic:**
    *   Instantiates the appropriate model class (e.g., `LiteLLMBase`, `OpenAIEmbed`) based on type.
    *   `chat` and `encode` methods delegate to the underlying model instance.

### 4. Model Layer (LiteLLM Integration)
The lowest layer interacts with external APIs.

*   **File:** `rag/llm/chat_model.py`

*   **Logic:**
    *   `LiteLLMBase` uses `litellm.completion` (synchronous) to make API calls to providers like OpenAI, Anthropic, etc.
    *   Streaming is handled by setting `stream=True` in `litellm.completion`, which returns a synchronous iterator.

## File List

The following files are relevant to the LLM API completion workflow:

1.  `api/apps/conversation_app.py`
2.  `api/apps/sdk/session.py`
3.  `api/db/services/dialog_service.py`
4.  `api/db/services/conversation_service.py`
5.  `api/db/services/llm_service.py`
6.  `rag/llm/chat_model.py`
7.  `rag/prompts/generator.py`
8.  `api/apps/chunk_app.py` (Consumer of LLM services)
9.  `api/apps/sdk/doc.py` (Consumer of LLM services)
