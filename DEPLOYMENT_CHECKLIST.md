# Deployment Checklist - Async Concurrency Fix

## Pre-Deployment

### Code Review
- [x] All blocking DB operations wrapped in `run_in_executor`
- [x] All blocking vector search operations wrapped in `run_in_executor`
- [x] LLM service async handling fixed
- [x] No syntax errors in modified files
- [x] `functools.partial` used for keyword arguments
- [x] `asyncio` imported in conversation_app.py

### Testing
- [ ] Run test script with 1 user (sanity check)
- [ ] Run test script with 10 concurrent users
- [ ] Run test script with 20 concurrent users
- [ ] Verify TTFC metrics are consistent
- [ ] Check success rate > 95%
- [ ] No blocking behavior warnings

### Documentation
- [x] Analysis report created (ASYNC_CONCURRENCY_ANALYSIS.md)
- [x] Implementation guide created (ASYNC_FIX_IMPLEMENTATION.md)
- [x] Summary document created (ASYNC_FIX_SUMMARY.md)
- [x] Test script created (test_concurrent_requests.py)
- [x] Deployment checklist created (this file)

## Deployment Steps

### 1. Backup
```bash
# Backup current code
cd /path/to/ragflow
git checkout -b backup-before-async-fix
git add .
git commit -m "Backup before async concurrency fix"

# Tag current version
git tag -a pre-async-fix -m "Before async concurrency fix"
```

### 2. Apply Changes
```bash
# Merge or apply the fix
git checkout main
git merge async-concurrency-fix
```

### 3. Build and Deploy
```bash
# Rebuild Docker images
cd docker
docker compose build ragflow-server

# Restart services
docker compose down
docker compose up -d

# Wait for services to be ready
docker logs -f ragflow-server | grep "RAGFlow HTTP server start"
```

### 4. Smoke Tests
```bash
# Test basic functionality
curl -X POST http://localhost:9380/v1/user/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'

# Get auth token from response
export AUTH_TOKEN="your_token_here"

# Test single request
python test_concurrent_requests.py \
  --token "$AUTH_TOKEN" \
  --conversation-id "test_conv_id" \
  --users 1 \
  --requests 1
```

### 5. Load Testing
```bash
# Test with 10 concurrent users
python test_concurrent_requests.py \
  --token "$AUTH_TOKEN" \
  --conversation-id "test_conv_id" \
  --users 10 \
  --requests 3

# Expected: Max TTFC < 2s, Success rate > 95%

# Test with 20 concurrent users
python test_concurrent_requests.py \
  --token "$AUTH_TOKEN" \
  --conversation-id "test_conv_id" \
  --users 20 \
  --requests 2

# Expected: Max TTFC < 3s, Success rate > 95%
```

## Post-Deployment

### Monitoring (First Hour)

- [ ] Check server logs for errors
  ```bash
  docker logs -f ragflow-server | grep -i error
  ```

- [ ] Monitor response times
  ```bash
  docker logs -f ragflow-server | grep "Time elapsed"
  ```

- [ ] Check resource usage
  ```bash
  docker stats ragflow-server
  ```

- [ ] Monitor database connections
  ```bash
  docker exec -it ragflow-mysql mysql -u root -p -e "SHOW PROCESSLIST;"
  ```

### Monitoring (First Day)

- [ ] Track concurrent user count
- [ ] Monitor average response times
- [ ] Check error rates
- [ ] Verify no memory leaks
- [ ] Check thread pool exhaustion

### Success Metrics

**Critical (Must Pass):**
- ✅ No 500 errors under normal load
- ✅ Response times < 3s for 95th percentile
- ✅ Success rate > 95%
- ✅ No server hangs/freezes

**Performance (Should Pass):**
- ✅ 10 CCU: Avg TTFC < 1s
- ✅ 20 CCU: Avg TTFC < 1.5s
- ✅ Max TTFC < 2x avg TTFC
- ✅ Memory usage stable

**Scalability (Nice to Have):**
- ✅ 50 CCU: Avg TTFC < 2s
- ✅ 100 CCU: Server responsive
- ✅ Linear scaling with CCU

## Rollback Plan

### Immediate Rollback (< 5 minutes)

If critical issues are detected:

```bash
# Stop current version
cd docker
docker compose down

# Checkout previous version
git checkout pre-async-fix

# Rebuild and start
docker compose build ragflow-server
docker compose up -d

# Verify rollback
curl http://localhost:9380/health
```

### Partial Rollback

If specific files cause issues:

```bash
# Revert specific file
git checkout pre-async-fix api/apps/conversation_app.py

# Rebuild
docker compose build ragflow-server
docker compose restart ragflow-server
```

## Troubleshooting

### Issue: Higher response times

**Check:**
```bash
# Thread pool size
python -c "import os; print(f'Thread pool size: {min(32, os.cpu_count() + 4)}')"

# Active threads
docker exec ragflow-server ps aux | wc -l

# Database connections
docker exec ragflow-mysql mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"
```

**Fix:**
```python
# Increase thread pool in settings.py
import concurrent.futures
executor = concurrent.futures.ThreadPoolExecutor(max_workers=100)
loop.set_default_executor(executor)
```

### Issue: Database connection errors

**Check:**
```bash
# Max connections
docker exec ragflow-mysql mysql -u root -p -e "SHOW VARIABLES LIKE 'max_connections';"

# Current connections
docker exec ragflow-mysql mysql -u root -p -e "SHOW PROCESSLIST;"
```

**Fix:**
```bash
# Increase MySQL connections
docker exec ragflow-mysql mysql -u root -p -e "SET GLOBAL max_connections = 500;"
```

### Issue: Memory growth

**Check:**
```bash
# Memory usage over time
watch -n 5 'docker stats ragflow-server --no-stream'

# Thread count
watch -n 5 'docker exec ragflow-server ps -eLf | wc -l'
```

**Fix:**
- Check for memory leaks in thread pool
- Reduce thread pool size
- Add connection pooling timeout

### Issue: Still seeing blocking

**Diagnosis:**
```bash
# Profile the application
docker exec ragflow-server pip install py-spy
docker exec ragflow-server py-spy top --pid 1

# Look for blocking operations
docker logs ragflow-server | grep -A5 -B5 "Time elapsed" | grep "Retrieval:"
```

**Fix:**
- Identify remaining blocking operations
- Wrap in `run_in_executor`
- Check if thread pool is exhausted

## Communication

### Stakeholders to Notify

**Before Deployment:**
- [ ] Development team
- [ ] QA team
- [ ] DevOps team

**After Deployment:**
- [ ] Send deployment summary
- [ ] Share test results
- [ ] Report any issues found

**In Case of Issues:**
- [ ] Immediate notification to on-call team
- [ ] Status update every 30 minutes
- [ ] Post-mortem after resolution

## Sign-off

### Pre-Deployment Approval

- [ ] Code reviewed by: _______________
- [ ] Tests passed: _______________
- [ ] Documentation reviewed: _______________
- [ ] Deployment approved by: _______________

### Post-Deployment Verification

- [ ] Smoke tests passed: _______________
- [ ] Load tests passed: _______________
- [ ] Monitoring confirmed stable: _______________
- [ ] Sign-off by: _______________

### Notes

_Add any deployment notes, issues encountered, or lessons learned here:_

```
Deployment Date: _______________
Deployed By: _______________
Issues Found: _______________
Rollback Required: Yes / No
Final Status: Success / Partial / Failed
```

## Reference Links

- [Analysis Report](./ASYNC_CONCURRENCY_ANALYSIS.md)
- [Implementation Guide](./ASYNC_FIX_IMPLEMENTATION.md)
- [Summary](./ASYNC_FIX_SUMMARY.md)
- [Test Script](./test_concurrent_requests.py)
