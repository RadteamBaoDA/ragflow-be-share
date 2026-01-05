#!/usr/bin/env python3
"""
Test script for concurrent request handling in RAGFlow.
Tests both AI Chat and AI Search endpoints under concurrent load.

Usage:
    python test_concurrent_requests.py --users 10 --requests 5
"""
import asyncio
import aiohttp
import time
import argparse
import json
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    user_id: int
    request_id: int
    endpoint: str
    first_chunk_time: float
    total_time: float
    success: bool
    error: str = ""
    chunks_received: int = 0


class ConcurrencyTester:
    """Test concurrent request handling"""
    
    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.auth_token = auth_token
        self.metrics: List[RequestMetrics] = []
    
    async def chat_request(
        self,
        session: aiohttp.ClientSession,
        user_id: int,
        request_id: int,
        conversation_id: str,
        message: str
    ) -> RequestMetrics:
        """Send a chat completion request and measure response times"""
        start_time = time.time()
        first_chunk_time = None
        chunks_received = 0
        success = False
        error = ""
        
        try:
            async with session.post(
                f"{self.base_url}/v1/conversation/completion",
                json={
                    "conversation_id": conversation_id,
                    "messages": [
                        {"role": "user", "content": message}
                    ],
                    "stream": True
                },
                headers={"Authorization": self.auth_token}
            ) as resp:
                if resp.status != 200:
                    error = f"HTTP {resp.status}"
                    return RequestMetrics(
                        user_id=user_id,
                        request_id=request_id,
                        endpoint="chat",
                        first_chunk_time=0,
                        total_time=time.time() - start_time,
                        success=False,
                        error=error
                    )
                
                async for line in resp.content:
                    if first_chunk_time is None:
                        first_chunk_time = time.time() - start_time
                    chunks_received += 1
                    
                    # Process SSE data
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data:'):
                        try:
                            data = json.loads(line_str[5:])
                            if data.get("code") == 0 and data.get("data") is True:
                                success = True
                        except json.JSONDecodeError:
                            pass
                
                total_time = time.time() - start_time
                
        except Exception as e:
            error = str(e)
            total_time = time.time() - start_time
        
        return RequestMetrics(
            user_id=user_id,
            request_id=request_id,
            endpoint="chat",
            first_chunk_time=first_chunk_time or 0,
            total_time=total_time,
            success=success,
            error=error,
            chunks_received=chunks_received
        )
    
    async def search_request(
        self,
        session: aiohttp.ClientSession,
        user_id: int,
        request_id: int,
        kb_ids: List[str],
        question: str
    ) -> RequestMetrics:
        """Send a search/ask request and measure response times"""
        start_time = time.time()
        first_chunk_time = None
        chunks_received = 0
        success = False
        error = ""
        
        try:
            async with session.post(
                f"{self.base_url}/v1/conversation/ask",
                json={
                    "question": question,
                    "kb_ids": kb_ids
                },
                headers={"Authorization": self.auth_token}
            ) as resp:
                if resp.status != 200:
                    error = f"HTTP {resp.status}"
                    return RequestMetrics(
                        user_id=user_id,
                        request_id=request_id,
                        endpoint="search",
                        first_chunk_time=0,
                        total_time=time.time() - start_time,
                        success=False,
                        error=error
                    )
                
                async for line in resp.content:
                    if first_chunk_time is None:
                        first_chunk_time = time.time() - start_time
                    chunks_received += 1
                    
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data:'):
                        try:
                            data = json.loads(line_str[5:])
                            if data.get("code") == 0 and data.get("data") is True:
                                success = True
                        except json.JSONDecodeError:
                            pass
                
                total_time = time.time() - start_time
                
        except Exception as e:
            error = str(e)
            total_time = time.time() - start_time
        
        return RequestMetrics(
            user_id=user_id,
            request_id=request_id,
            endpoint="search",
            first_chunk_time=first_chunk_time or 0,
            total_time=total_time,
            success=success,
            error=error,
            chunks_received=chunks_received
        )
    
    async def run_test(
        self,
        num_concurrent_users: int,
        requests_per_user: int,
        test_type: str,
        conversation_id: str = None,
        kb_ids: List[str] = None
    ):
        """Run concurrent test with specified parameters"""
        print(f"\n{'='*70}")
        print(f"Testing {test_type.upper()} with {num_concurrent_users} concurrent users")
        print(f"Each user sends {requests_per_user} requests")
        print(f"{'='*70}\n")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for user_id in range(num_concurrent_users):
                for req_id in range(requests_per_user):
                    if test_type == "chat":
                        task = self.chat_request(
                            session,
                            user_id,
                            req_id,
                            conversation_id,
                            f"User {user_id} request {req_id}: What is RAGFlow?"
                        )
                    else:  # search
                        task = self.search_request(
                            session,
                            user_id,
                            req_id,
                            kb_ids,
                            f"User {user_id} request {req_id}: What is machine learning?"
                        )
                    tasks.append(task)
            
            # Execute all requests concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            total_test_time = time.time() - start_time
            
            self.metrics.extend(results)
            
            # Print results
            self._print_results(results, total_test_time, test_type)
    
    def _print_results(self, results: List[RequestMetrics], total_test_time: float, test_type: str):
        """Print test results with statistics"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        first_chunk_times = [r.first_chunk_time for r in successful if r.first_chunk_time > 0]
        total_times = [r.total_time for r in successful]
        
        print(f"\n{test_type.upper()} Test Results:")
        print(f"{'='*70}")
        print(f"Total requests: {len(results)}")
        print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
        print(f"Total test time: {total_test_time:.2f}s")
        print()
        
        if first_chunk_times:
            print(f"Time to First Chunk (TTFC):")
            print(f"  Average: {statistics.mean(first_chunk_times):.3f}s")
            print(f"  Median:  {statistics.median(first_chunk_times):.3f}s")
            print(f"  Min:     {min(first_chunk_times):.3f}s")
            print(f"  Max:     {max(first_chunk_times):.3f}s")
            if len(first_chunk_times) > 1:
                print(f"  StdDev:  {statistics.stdev(first_chunk_times):.3f}s")
            print()
        
        if total_times:
            print(f"Total Response Time:")
            print(f"  Average: {statistics.mean(total_times):.3f}s")
            print(f"  Median:  {statistics.median(total_times):.3f}s")
            print(f"  Min:     {min(total_times):.3f}s")
            print(f"  Max:     {max(total_times):.3f}s")
            if len(total_times) > 1:
                print(f"  StdDev:  {statistics.stdev(total_times):.3f}s")
            print()
        
        if failed:
            print(f"Failed Requests:")
            error_counts = {}
            for r in failed:
                error_counts[r.error] = error_counts.get(r.error, 0) + 1
            for error, count in error_counts.items():
                print(f"  {error}: {count} requests")
            print()
        
        # Check for blocking behavior
        if len(first_chunk_times) > 1:
            avg_ttfc = statistics.mean(first_chunk_times)
            max_ttfc = max(first_chunk_times)
            
            if max_ttfc > avg_ttfc * 2:
                print("⚠️  WARNING: Detected blocking behavior!")
                print(f"   Max TTFC ({max_ttfc:.3f}s) is > 2x average ({avg_ttfc:.3f}s)")
                print(f"   This suggests requests are blocking each other.")
            else:
                print("✅ Good: Requests appear to be handled concurrently")
                print(f"   Max TTFC ({max_ttfc:.3f}s) is within 2x of average ({avg_ttfc:.3f}s)")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Test concurrent request handling in RAGFlow"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:9380",
        help="RAGFlow base URL (default: http://localhost:9380)"
    )
    parser.add_argument(
        "--token",
        required=True,
        help="Authorization token"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=10,
        help="Number of concurrent users (default: 10)"
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=3,
        help="Requests per user (default: 3)"
    )
    parser.add_argument(
        "--test-type",
        choices=["chat", "search", "both"],
        default="both",
        help="Type of test to run (default: both)"
    )
    parser.add_argument(
        "--conversation-id",
        help="Conversation ID for chat tests"
    )
    parser.add_argument(
        "--kb-ids",
        help="Comma-separated KB IDs for search tests"
    )
    
    args = parser.parse_args()
    
    tester = ConcurrencyTester(args.url, args.token)
    
    kb_ids = args.kb_ids.split(",") if args.kb_ids else []
    
    async def run_tests():
        if args.test_type in ["chat", "both"]:
            if not args.conversation_id:
                print("ERROR: --conversation-id required for chat tests")
                return
            await tester.run_test(
                args.users,
                args.requests,
                "chat",
                conversation_id=args.conversation_id
            )
        
        if args.test_type in ["search", "both"]:
            if not kb_ids:
                print("ERROR: --kb-ids required for search tests")
                return
            await tester.run_test(
                args.users,
                args.requests,
                "search",
                kb_ids=kb_ids
            )
        
        # Overall summary
        print(f"\n{'='*70}")
        print(f"OVERALL TEST SUMMARY")
        print(f"{'='*70}")
        
        all_successful = [m for m in tester.metrics if m.success]
        all_failed = [m for m in tester.metrics if not m.success]
        all_ttfc = [m.first_chunk_time for m in all_successful if m.first_chunk_time > 0]
        
        print(f"Total requests: {len(tester.metrics)}")
        print(f"Success rate: {len(all_successful)/len(tester.metrics)*100:.1f}%")
        
        if all_ttfc:
            print(f"\nConcurrent Performance:")
            print(f"  Average TTFC: {statistics.mean(all_ttfc):.3f}s")
            print(f"  Max TTFC: {max(all_ttfc):.3f}s")
            print(f"  Spread: {max(all_ttfc) - min(all_ttfc):.3f}s")
            
            if max(all_ttfc) > statistics.mean(all_ttfc) * 3:
                print(f"\n❌ PERFORMANCE ISSUE DETECTED")
                print(f"   Some requests took 3x+ longer than average")
                print(f"   Blocking operations may be present")
            else:
                print(f"\n✅ GOOD CONCURRENT PERFORMANCE")
                print(f"   Requests handled efficiently")
        
        print()
    
    asyncio.run(run_tests())


if __name__ == "__main__":
    main()
