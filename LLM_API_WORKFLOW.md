# LLM API Completion Workflow

This document outlines the Python source code files handling API LLM completions, specifically focusing on conversation and chatbot endpoints.

## Identified Files

The following files contain the implementation for handling LLM completion requests:

1.  **`api/apps/sdk/session.py`**: Handles external API requests (SDK, Chatbots, Agents).
2.  **`api/apps/conversation_app.py`**: Handles internal conversation API requests (typically for the Web UI).

## Detailed Implementation & Workflow

### 1. `api/apps/sdk/session.py`

This file defines endpoints for external interactions, including chatbots, agents, and standard chat sessions. It maps to the `/api/v1` prefix.

#### Key Endpoints:

*   **Chatbot Completion**: `POST /chatbots/<dialog_id>/completions`
    *   **Function**: `chatbot_completions`
    *   **Usage**: Used by embedded chatbots or external integrations.
    *   **Workflow**:
        1.  Validates the API Token from the `Authorization` header.
        2.  Calls `iframe_completion(dialog_id, **req)` from `api.db.services.conversation_service`.
        3.  Supports streaming (`stream=True`) returning `text/event-stream` or a single JSON response.

*   **Chat Completion**: `POST /chats/<chat_id>/completions`
    *   **Function**: `chat_completion`
    *   **Usage**: Standard chat completion for a specific chat session.
    *   **Workflow**:
        1.  Verifies the user owns the chat and session via `@token_required`.
        2.  Calls `rag_completion(tenant_id, chat_id, **req)` from `api.db.services.conversation_service`.
        3.  Returns streamed or full response.

*   **OpenAI-Compatible Chat**: `POST /chats_openai/<chat_id>/chat/completions`
    *   **Function**: `chat_completion_openai_like`
    *   **Usage**: Simulates OpenAI's API structure for easy integration with existing tools.
    *   **Workflow**:
        1.  Validates request format (messages, model).
        2.  Calls `chat(...)` from `api.db.services.dialog_service`.
        3.  Formats the output to match OpenAI's chunk format (if streaming) or message format.

*   **Agent Completion**: `POST /agents/<agent_id>/completions`
    *   **Function**: `agent_completions`
    *   **Usage**: For interacting with configured Agents.
    *   **Workflow**:
        1.  Calls `agent_completion(...)` from `api.db.services.canvas_service`.
        2.  Iterates through the agent execution steps and yields results.

### 2. `api/apps/conversation_app.py`

This file handles requests under the `/v1/conversation` prefix, primarily used by the RAGFlow web interface.

#### Key Endpoint:

*   **Completion**: `POST /completion` (Mapped to `/v1/conversation/completion`)
    *   **Function**: `completion`
    *   **Usage**: The main endpoint for user-assistant conversations in the UI.
    *   **Workflow**:
        1.  **Authentication**: Protected by `@login_required`.
        2.  **Validation**: Checks `conversation_id`, `messages`, and user permissions.
        3.  **Setup**:
            *   Retrieves the conversation and dialog details.
            *   Updates the dialog's LLM settings if specified in the request.
        4.  **Execution**:
            *   Calls `chat(dia, msg, True, **req)` from `api.db.services.dialog_service`.
            *   Uses `structure_answer` to format the response chunks.
            *   Updates the conversation history in the database.
        5.  **Streaming**: Returns a server-sent events (SSE) stream to update the UI in real-time.

## General Workflow Summary

1.  **Request Reception**: The Quart application receives the HTTP POST request at the specific endpoint.
2.  **Authentication & Authorization**:
    *   **External**: API Tokens are validated against `APIToken` in the database.
    *   **Internal**: User sessions are validated (`@login_required`).
3.  **Data Validation**: Input data (messages, questions, IDs) is validated against schema and database records (e.g., ensuring the dialog exists and belongs to the user/tenant).
4.  **Core Service Invocation**:
    *   The controller invokes a service function (e.g., `chat`, `rag_completion`, `agent_completion`) located in `api/db/services/`.
5.  **LLM & RAG Orchestration**:
    *   The service interacts with the Knowledge Base (Retrieval) if configured.
    *   It constructs the prompt using retrieved context and conversation history.
    *   It calls the LLM service (`LLMBundle` or `TenantLLMService`) to generate a completion.
6.  **Response Formatting**:
    *   The generated text is processed (e.g., extracting reasoning, formatting references).
    *   The response is sent back to the client, either as a complete JSON object or as a stream of data chunks.
