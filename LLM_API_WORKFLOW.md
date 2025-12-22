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

## Deep Dive: From Service to LLM Provider

The connection from the `DialogService` to the actual LLM provider involves several layers of abstraction to handle different providers (OpenAI, Azure, etc.) uniformly.

### 1. `api/db/services/dialog_service.py` (`chat` function)
The `chat` function orchestrates the retrieval and generation process.
*   **Retrieval**: Uses `settings.retriever.retrieval` to fetch relevant documents from the Knowledge Base (Elasticsearch/Infinity).
*   **Model Initialization**: Calls `get_models(dialog)` which initializes an `LLMBundle`.
    ```python
    chat_mdl = LLMBundle(dialog.tenant_id, LLMType.CHAT, dialog.llm_id)
    ```
*   **Prompt Construction**: Merges system prompts, retrieved knowledge, and user history.
*   **Generation**: Calls `chat_mdl.chat_streamly(...)` or `chat_mdl.chat(...)`.

### 2. `api/db/services/llm_service.py` (`LLMBundle`)
`LLMBundle` acts as a wrapper around the tenant-specific model instance.
*   **Inheritance**: Inherits from `LLM4Tenant`.
*   **Initialization**: Calls `TenantLLMService.model_instance(...)` to create the actual model object.
*   **Methods**: `chat()` and `chat_streamly()` delegate to `self.mdl.chat()` and `self.mdl.chat_streamly()`, while handling token usage tracking and Langfuse tracing.

### 3. `api/db/services/tenant_llm_service.py` (`TenantLLMService`)
This service is responsible for instantiating the correct Python class for the specific LLM provider.
*   **`model_instance` method**:
    *   Retrieves the API key and configuration for the given tenant and model name using `get_model_config`.
    *   Determines the `llm_factory` (e.g., "OpenAI", "Azure-OpenAI", "HuggingFace").
    *   Instantiates the corresponding class from `rag.llm` module.
    *   **Example Mapping**:
        *   `OpenAI` -> `ChatModel['OpenAI']` (which is `GptTurbo`)
        *   `Azure-OpenAI` -> `ChatModel['Azure-OpenAI']` (which is `AzureChat`)

### 4. `rag/llm/chat_model.py` (Model Implementations)
This file contains the concrete implementations for various LLM providers. All classes inherit from `Base` (or `LiteLLMBase`).

*   **`Base` Class**:
    *   Initializes the `openai.OpenAI` client (or compatible clients).
    *   Implements `_chat` and `_chat_streamly` using `self.client.chat.completions.create`.
    *   Handles retries (exponential backoff) and error classification.
*   **Specific Implementations**:
    *   **`GptTurbo`**: Uses the standard `OpenAI` client.
    *   **`AzureChat`**: Uses `AzureOpenAI` client.
    *   **`ZhipuChat`**: Uses `ZhipuAI` client.
    *   **`LiteLLMBase`**: Uses `litellm.completion` to support a wide range of providers (e.g., Bedrock, Anthropic, Ollama).

### Summary Chain of Calls
1.  **API**: `chat_completion` (Controller)
2.  **Service**: `DialogService.chat(...)`
3.  **Wrapper**: `LLMBundle.chat_streamly(...)`
4.  **Factory**: `TenantLLMService.model_instance(...)` returns `GptTurbo` (example).
5.  **Driver**: `GptTurbo.chat_streamly(...)` -> `Base._chat_streamly(...)`
6.  **Client**: `openai.OpenAI().chat.completions.create(...)` -> **External API**
