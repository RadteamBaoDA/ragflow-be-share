# Additional Blocking Operations Found - Review Results

## Date: January 5, 2026
## Status: ⚠️ **CRITICAL ISSUES FOUND**

---

## Executive Summary

After deep review of database services and reranker calls, I identified **additional blocking operations** that were **not fixed** in the initial implementation. These need immediate attention.

---

## 🔴 CRITICAL: Reranker Calls Are **SYNCHRONOUS**

### Location
`rag/nlp/search.py` - Line 351

### Issue
```python
def rerank_by_model(self, rerank_mdl, sres, query, tkweight=0.3, vtweight=0.7, ...):
    # ...
    # ❌ BLOCKING: Synchronous call to rerank model
    vtsim, _ = rerank_mdl.similarity(query, [remove_redundant_spaces(" ".join(tks)) for tks in ins_tw])
    # ...
```

### Reranker Implementation
`rag/llm/rerank_model.py` - All models use **synchronous HTTP requests**:

```python
class JinaRerank(Base):
    def similarity(self, query: str, texts: list):
        # ❌ BLOCKING: Uses requests.post (synchronous)
        res = requests.post(self.base_url, headers=self.headers, json=data).json()
        # ...

class XInferenceRerank(Base):
    def similarity(self, query: str, texts: list):
        # ❌ BLOCKING: Uses requests.post (synchronous)
        res = requests.post(self.base_url, headers=self.headers, json=data).json()
        # ...

class LocalAIRerank(Base):
    def similarity(self, query: str, texts: list):
        # ❌ BLOCKING: Uses requests.post (synchronous)
        res = requests.post(self.base_url, headers=self.headers, json=data).json()
        # ...

class NvidiaRerank(Base):
    def similarity(self, query: str, texts: list):
        # ❌ BLOCKING: Uses requests.post (synchronous)
        # ...
```

### Impact
- **HTTP call duration**: 100-500ms per rerank operation
- **Called from**: `retriever.retrieval()` which we already wrapped in executor
- **Severity**: Medium (already mitigated by wrapping retrieval(), but inefficient)

### Why This Partially Works
We wrapped `retriever.retrieval()` in executor, which includes the rerank call:
```python
# This wraps the ENTIRE retrieval including reranking
kbinfos = await loop.run_in_executor(None, retriever.retrieval, ...)
```

So reranking runs in thread pool, but it's still **blocking within that thread**.

### Better Solution
Make reranker calls **truly async** using `httpx.AsyncClient`:

```python
class JinaRerank(Base):
    def __init__(self, key, model_name, base_url):
        self.async_client = httpx.AsyncClient(timeout=30.0)
        # ...
    
    async def async_similarity(self, query: str, texts: list):
        """Async version using httpx"""
        texts = [truncate(t, 8196) for t in texts]
        data = {
            "model": self.model_name,
            "query": query,
            "documents": texts,
            "top_n": len(texts)
        }
        res = await self.async_client.post(
            self.base_url,
            headers=self.headers,
            json=data
        )
        result = res.json()
        # ... process result
```

---

## 🔴 CRITICAL: Blocking DB Operations in `conversation_service.py`

### Location
`api/db/services/conversation_service.py`

### Issues Found

#### 1. `async_completion()` - Line 94
```python
async def async_completion(tenant_id, chat_id, question, ...):
    # ❌ BLOCKING: Synchronous DB query
    dia = DialogService.query(id=chat_id, tenant_id=tenant_id, status=StatusEnum.VALID.value)
    
    if not session_id:
        # ❌ BLOCKING: Synchronous DB save
        ConversationService.save(**conv)
    
    # ❌ BLOCKING: Synchronous DB query
    conv = ConversationService.query(id=session_id, dialog_id=chat_id)
    
    # ❌ BLOCKING: Synchronous DB update
    ConversationService.update_by_id(conv.id, conv.to_dict())
```

**Impact:** 
- 3-4 blocking DB calls per request (50-200ms each)
- Total: 150-800ms of blocking per completion request
- **This is called from SDK/API endpoints!**

#### 2. `async_iframe_completion()` - Line 182
```python
async def async_iframe_completion(dialog_id, question, session_id=None, ...):
    # ❌ BLOCKING: Synchronous DB query
    e, dia = DialogService.get_by_id(dialog_id)
    
    # ❌ BLOCKING: Synchronous DB save
    API4ConversationService.save(**conv)
```

**Impact:**
- 2 blocking DB calls per iframe request
- Used by embedded chat widget

---

## 🟡 MEDIUM: Additional DB Service Decorators

### Locations with `@DB.connection_context()`

Found in multiple service files that may be called from async contexts:

1. **`api/db/services/api_service.py`**
   - Lines: 29, 39, 48, 79, 85, 110
   - Methods: `get_list()`, `delete_by_tenant_id()`, `increase_round()`, etc.

2. **`api/db/services/file2document_service.py`**
   - Lines: 30, 36, 42, 48, 55
   - Methods: Various CRUD operations

3. **`api/db/services/conversation_service.py`**
   - Lines: 30, 50
   - Methods: `get_list()`, `get_all_conversation_by_dialog_ids()`

**Note:** These may not be called from async contexts currently, but they're potential landmines.

---

## 📊 Performance Impact Analysis

### Current State (With Partial Fix)

| Operation | Before Fix | With Executor | Truly Async | Impact |
|-----------|-----------|---------------|-------------|--------|
| DB Query | ❌ Blocks 50-100ms | ⚠️ Thread pool 50-100ms | ✅ <1ms | High |
| Vector Search | ❌ Blocks 200-500ms | ⚠️ Thread pool 200-500ms | ✅ <1ms | High |
| Reranker HTTP | ❌ Blocks 100-300ms | ⚠️ In thread 100-300ms | ✅ <1ms | Medium |
| LLM Streaming | ✅ Async | ✅ Async | ✅ Async | N/A |

### Thread Pool Limitations

**Current approach** (`run_in_executor`):
- ✅ Prevents blocking event loop
- ✅ Allows concurrent requests
- ⚠️ Still uses OS threads (expensive)
- ⚠️ Thread pool can be exhausted (default 32-36 threads)
- ⚠️ Each thread still blocks during I/O

**Truly async approach**:
- ✅ No thread overhead
- ✅ Thousands of concurrent operations
- ✅ True non-blocking I/O
- ✅ Better resource utilization

---

## 🔧 Required Fixes

### Priority 1: Fix conversation_service.py (IMMEDIATE)

```python
# File: api/db/services/conversation_service.py

async def async_completion(tenant_id, chat_id, question, name="New session", session_id=None, stream=True, **kwargs):
    assert name, "`name` can not be empty."
    
    # ✅ FIX: Wrap in executor
    loop = asyncio.get_event_loop()
    from functools import partial
    
    dia = await loop.run_in_executor(
        None,
        partial(
            DialogService.query,
            id=chat_id,
            tenant_id=tenant_id,
            status=StatusEnum.VALID.value
        )
    )
    assert dia, "You do not own the chat."

    if not session_id:
        session_id = get_uuid()
        conv = {
            "id": session_id,
            "dialog_id": chat_id,
            "name": name,
            "message": [{"role": "assistant", "content": dia[0].prompt_config.get("prologue"), "created_at": time.time()}],
            "user_id": kwargs.get("user_id", "")
        }
        # ✅ FIX: Wrap in executor
        await loop.run_in_executor(
            None,
            partial(ConversationService.save, **conv)
        )
        # ... rest of the code
    
    # ✅ FIX: Wrap in executor
    conv = await loop.run_in_executor(
        None,
        partial(
            ConversationService.query,
            id=session_id,
            dialog_id=chat_id
        )
    )
    
    # ... in streaming section ...
    # ✅ FIX: Wrap in executor
    await loop.run_in_executor(
        None,
        ConversationService.update_by_id,
        conv.id,
        conv.to_dict()
    )
```

### Priority 2: Make Reranker Async (RECOMMENDED)

Create async versions of reranker models:

```python
# File: rag/llm/rerank_model.py

import httpx

class JinaRerank(Base):
    def __init__(self, key, model_name, base_url):
        self.base_url = "https://api.jina.ai/v1/rerank"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}"
        }
        self.model_name = model_name
        # Add async client
        self.async_client = httpx.AsyncClient(timeout=30.0)
    
    # Keep sync version for backward compatibility
    def similarity(self, query: str, texts: list):
        texts = [truncate(t, 8196) for t in texts]
        data = {
            "model": self.model_name,
            "query": query,
            "documents": texts,
            "top_n": len(texts)
        }
        res = requests.post(self.base_url, headers=self.headers, json=data).json()
        # ... process result
    
    # Add new async version
    async def async_similarity(self, query: str, texts: list):
        texts = [truncate(t, 8196) for t in texts]
        data = {
            "model": self.model_name,
            "query": query,
            "documents": texts,
            "top_n": len(texts)
        }
        response = await self.async_client.post(
            self.base_url,
            headers=self.headers,
            json=data
        )
        res = response.json()
        rank = np.zeros(len(texts), dtype=float)
        try:
            for d in res["results"]:
                rank[d["index"]] = d["relevance_score"]
        except Exception as _e:
            log_exception(_e, res)
        return rank, total_token_count_from_response(res)
```

Then update `rag/nlp/search.py`:

```python
# File: rag/nlp/search.py

async def async_rerank_by_model(self, rerank_mdl, sres, query, tkweight=0.3, vtweight=0.7, ...):
    """Async version of rerank_by_model"""
    # ... existing code ...
    
    # ✅ Use async similarity if available
    if hasattr(rerank_mdl, 'async_similarity'):
        vtsim, token_count = await rerank_mdl.async_similarity(
            query,
            [remove_redundant_spaces(" ".join(tks)) for tks in ins_tw]
        )
    else:
        # Fallback to sync in executor
        loop = asyncio.get_event_loop()
        vtsim, token_count = await loop.run_in_executor(
            None,
            rerank_mdl.similarity,
            query,
            [remove_redundant_spaces(" ".join(tks)) for tks in ins_tw]
        )
    
    # ... rest of code
```

### Priority 3: Long-term - Async ORM

Migrate to async database driver:
- aiomysql for MySQL
- SQLAlchemy 2.0 (async support)
- Connection pooling

---

## 📝 Testing Requirements

### Test 1: Verify conversation_service.py fixes
```bash
# Test async_completion endpoint
python test_concurrent_requests.py \
    --token "$TOKEN" \
    --conversation-id "new_conv" \
    --users 10 \
    --requests 3
```

### Test 2: Reranker performance
```python
# Add timing to retrieval
import time

start = time.time()
kbinfos = retriever.retrieval(...)
print(f"Retrieval with rerank: {time.time() - start:.3f}s")
```

### Test 3: Check for remaining blocking
```bash
# Profile with py-spy
py-spy record -o profile.svg -- python -m api.ragflow_server

# Look for:
# - requests.post calls
# - database query stacks
# - Thread.join() calls
```

---

## 🎯 Recommendations

### Immediate (This Week)
1. ✅ **Fix conversation_service.py** - Wrap all DB calls in executor
2. ✅ **Test with 20+ concurrent users** - Verify no degradation
3. ✅ **Monitor thread pool usage** - Check if 32 threads is enough

### Short-term (Next 2 Weeks)
1. ⚠️ **Add async reranker methods** - Start with JinaRerank
2. ⚠️ **Update retrieval to use async rerank** - When available
3. ⚠️ **Add metrics** - Track thread pool exhaustion

### Long-term (1-2 Months)
1. 🔄 **Migrate to aiomysql** - True async DB
2. 🔄 **Implement connection pooling** - Better resource management
3. 🔄 **Add async vector store clients** - Elasticsearch async

---

## 📋 Updated File Change List

### Files That Need Additional Fixes

1. **`api/db/services/conversation_service.py`** ⚠️ **URGENT**
   - `async_completion()` - 4 blocking DB calls
   - `async_iframe_completion()` - 2 blocking DB calls

2. **`rag/llm/rerank_model.py`** (Recommended)
   - Add `async_similarity()` methods to all reranker classes
   - Use `httpx.AsyncClient` instead of `requests`

3. **`rag/nlp/search.py`** (If reranker made async)
   - Add `async_rerank_by_model()` method
   - Update `retrieval()` to use async rerank when available

---

## 🔍 Code Inspection Results

### Reranker Call Chain

```
User Request
    ↓
conversation_app.py: completion()
    ↓
dialog_service.py: async_chat()
    ↓
[WRAPPED] loop.run_in_executor(retriever.retrieval, ...)  ✅ Non-blocking to event loop
    ↓
    [IN THREAD POOL] ↓
    search.py: retrieval()
        ↓
        search.py: rerank_by_model()
            ↓
            rerank_model.py: similarity()
                ↓
                [BLOCKING] requests.post(...)  ⚠️ Blocks thread (not event loop)
```

**Current State:** 
- ✅ Event loop is NOT blocked (good!)
- ⚠️ Thread in pool IS blocked for 100-300ms (inefficient)
- ⚠️ Under very high load (100+ CCU), thread pool could be exhausted

### Database Call Chain

```
conversation_service.py: async_completion()
    ↓
❌ DialogService.query()  [BLOCKING - NOT WRAPPED]
    ↓
❌ ConversationService.save()  [BLOCKING - NOT WRAPPED]
    ↓
❌ ConversationService.query()  [BLOCKING - NOT WRAPPED]
    ↓
❌ ConversationService.update_by_id()  [BLOCKING - NOT WRAPPED]
```

**Current State:**
- ❌ All DB calls block event loop
- ❌ Each call: 50-200ms
- ❌ Total blocking: 200-800ms per request
- ❌ Severe performance degradation under concurrent load

---

## ✅ Action Items

- [ ] Fix conversation_service.py DB calls (IMMEDIATE)
- [ ] Test with 20+ concurrent users
- [ ] Add async reranker methods (recommended)
- [ ] Update documentation
- [ ] Add monitoring for thread pool usage
- [ ] Plan async ORM migration

---

## 📚 References

- [httpx Async Client](https://www.python-httpx.org/async/)
- [aiomysql Documentation](https://aiomysql.readthedocs.io/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html)
