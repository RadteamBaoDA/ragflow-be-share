# Quick Start - Testing the Async Fix

## 1. Prerequisites

- RAGFlow server running
- Python 3.8+ installed
- `aiohttp` package installed

```bash
pip install aiohttp
```

## 2. Get Your Auth Token

### Option A: From Browser
1. Login to RAGFlow UI
2. Open Browser DevTools (F12)
3. Go to Network tab
4. Make any API request
5. Find "Authorization" header
6. Copy the token value

### Option B: Via API
```bash
curl -X POST http://localhost:9380/v1/user/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your_email@example.com",
    "password": "your_password"
  }'
```

Copy the token from the response.

## 3. Get Test IDs

### Get Conversation ID
1. Go to RAGFlow Chat UI
2. Create or open a conversation
3. Copy the ID from the URL: `/chat/xxx` → `xxx` is your conversation ID

### Get Knowledge Base IDs
1. Go to Knowledge Base section
2. Note the IDs of your knowledge bases
3. Or use API:
```bash
curl -X GET http://localhost:9380/v1/kb/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 4. Run Basic Test (1 User)

```bash
python test_concurrent_requests.py \
  --token "YOUR_TOKEN" \
  --conversation-id "YOUR_CONV_ID" \
  --users 1 \
  --requests 1 \
  --test-type chat
```

**Expected output:**
```
======================================================================
Testing CHAT with 1 concurrent users
======================================================================

CHAT Test Results:
======================================================================
Total requests: 1
Successful: 1 (100.0%)
Failed: 0 (0.0%)

Time to First Chunk (TTFC):
  Average: 0.523s
  Median:  0.523s
  Min:     0.523s
  Max:     0.523s

✅ Test passed - Single request baseline established
```

## 5. Run Concurrency Test (10 Users)

```bash
python test_concurrent_requests.py \
  --token "YOUR_TOKEN" \
  --conversation-id "YOUR_CONV_ID" \
  --users 10 \
  --requests 3 \
  --test-type chat
```

**What to look for:**
- ✅ Success rate > 95%
- ✅ Max TTFC < 2 seconds
- ✅ Message: "Good: Requests appear to be handled concurrently"
- ❌ Warning: "Detected blocking behavior" (BAD - needs investigation)

## 6. Interpret Results

### Good Results ✅
```
======================================================================
Testing CHAT with 10 concurrent users
======================================================================

Total requests: 30
Successful: 30 (100.0%)
Failed: 0 (0.0%)

Time to First Chunk (TTFC):
  Average: 0.612s
  Median:  0.598s
  Min:     0.487s
  Max:     0.891s
  StdDev:  0.098s

✅ Good: Requests appear to be handled concurrently
   Max TTFC (0.891s) is within 2x of average (0.612s)
```

**Analysis:** Server is handling concurrent requests well!

### Bad Results ❌
```
======================================================================
Testing CHAT with 10 concurrent users
======================================================================

Total requests: 30
Successful: 25 (83.3%)
Failed: 5 (16.7%)

Time to First Chunk (TTFC):
  Average: 2.534s
  Median:  2.187s
  Min:     0.523s
  Max:     8.921s
  StdDev:  2.341s

⚠️ WARNING: Detected blocking behavior!
   Max TTFC (8.921s) is > 2x average (2.534s)
   This suggests requests are blocking each other.
```

**Analysis:** Blocking behavior detected - fix may not be working properly

## 7. Test Search Endpoint

```bash
python test_concurrent_requests.py \
  --token "YOUR_TOKEN" \
  --kb-ids "KB_ID_1,KB_ID_2" \
  --users 10 \
  --requests 3 \
  --test-type search
```

## 8. Stress Test (20+ Users)

```bash
# Test with 20 concurrent users
python test_concurrent_requests.py \
  --token "YOUR_TOKEN" \
  --conversation-id "YOUR_CONV_ID" \
  --users 20 \
  --requests 2 \
  --test-type chat

# Test with 50 concurrent users
python test_concurrent_requests.py \
  --token "YOUR_TOKEN" \
  --conversation-id "YOUR_CONV_ID" \
  --users 50 \
  --requests 1 \
  --test-type chat
```

## 9. Compare Before/After

### Record Baseline (Before Fix)
```bash
# Run test and save results
python test_concurrent_requests.py \
  --token "YOUR_TOKEN" \
  --conversation-id "YOUR_CONV_ID" \
  --users 10 \
  --requests 3 > results_before.txt
```

### Apply Fix & Test (After Fix)
```bash
# After applying the fix
python test_concurrent_requests.py \
  --token "YOUR_TOKEN" \
  --conversation-id "YOUR_CONV_ID" \
  --users 10 \
  --requests 3 > results_after.txt

# Compare
diff results_before.txt results_after.txt
```

**Expected improvements:**
- Average TTFC: 5-10x faster
- Max TTFC: 5-10x faster
- Success rate: Higher
- No blocking warnings

## 10. Common Issues

### Issue: "Connection refused"
**Solution:**
```bash
# Check if server is running
docker ps | grep ragflow

# Check server logs
docker logs ragflow-server

# Verify port
netstat -an | grep 9380
```

### Issue: "Authentication error"
**Solution:**
- Token may have expired
- Get a fresh token from browser or login API
- Ensure token format: `Bearer YOUR_TOKEN`

### Issue: "Conversation not found"
**Solution:**
- Verify conversation ID exists
- Create a new conversation in UI
- Use the correct ID from the URL

### Issue: Test hangs or times out
**Solution:**
```bash
# Check server is responsive
curl http://localhost:9380/health

# Check resource usage
docker stats ragflow-server

# Check for errors
docker logs ragflow-server | tail -50
```

## 11. Quick Verification Commands

```bash
# Check server is running
curl -s http://localhost:9380/health | jq

# Check version
curl -s http://localhost:9380/v1/system/version | jq

# Test authentication
curl -s http://localhost:9380/v1/user/me \
  -H "Authorization: Bearer YOUR_TOKEN" | jq

# Monitor real-time logs
docker logs -f ragflow-server | grep -i "time elapsed"
```

## 12. Automated Test Script

Save this as `quick_test.sh`:

```bash
#!/bin/bash

# Configuration
TOKEN="YOUR_TOKEN_HERE"
CONV_ID="YOUR_CONV_ID_HERE"
KB_IDS="YOUR_KB_IDS_HERE"

echo "=== Quick Concurrency Test ==="
echo ""

# Test 1: Single user baseline
echo "Test 1: Single user baseline..."
python test_concurrent_requests.py \
  --token "$TOKEN" \
  --conversation-id "$CONV_ID" \
  --users 1 \
  --requests 1 \
  --test-type chat

# Test 2: 10 concurrent users
echo ""
echo "Test 2: 10 concurrent users..."
python test_concurrent_requests.py \
  --token "$TOKEN" \
  --conversation-id "$CONV_ID" \
  --users 10 \
  --requests 3 \
  --test-type chat

# Test 3: 20 concurrent users
echo ""
echo "Test 3: 20 concurrent users..."
python test_concurrent_requests.py \
  --token "$TOKEN" \
  --conversation-id "$CONV_ID" \
  --users 20 \
  --requests 2 \
  --test-type chat

echo ""
echo "=== Tests Complete ==="
```

Run it:
```bash
chmod +x quick_test.sh
./quick_test.sh
```

## 13. Success Indicators

✅ **Fix is working if you see:**
- Success rate > 95%
- Max TTFC < 2x average TTFC
- No exponential growth with CCU
- Message: "Good: Requests appear to be handled concurrently"
- 20+ concurrent users: Server still responsive

❌ **Fix needs attention if you see:**
- Success rate < 90%
- Max TTFC > 3x average TTFC
- Warning: "Detected blocking behavior"
- Response times grow exponentially
- Server becomes unresponsive

## Need Help?

1. Check [ASYNC_FIX_IMPLEMENTATION.md](./ASYNC_FIX_IMPLEMENTATION.md) for detailed guide
2. Review [ASYNC_CONCURRENCY_ANALYSIS.md](./ASYNC_CONCURRENCY_ANALYSIS.md) for technical details
3. Check server logs: `docker logs ragflow-server`
4. Verify test script: `python test_concurrent_requests.py --help`

## Next Steps

After verifying the fix works:
1. Test with your actual production load
2. Monitor metrics over 24 hours
3. Gradually increase CCU
4. Implement monitoring (Phase 2)
5. Plan async ORM migration (Phase 3)
