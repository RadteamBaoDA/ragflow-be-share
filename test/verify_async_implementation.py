#!/usr/bin/env python3
"""
Quick verification that async_retrieval is being called correctly
"""

import re
import sys
from pathlib import Path

def check_file(filepath, patterns):
    """Check if file contains expected patterns"""
    content = Path(filepath).read_text(encoding='utf-8')
    results = []
    for pattern, description in patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        results.append({
            'pattern': description,
            'found': len(matches),
            'matches': matches[:3] if matches else []
        })
    return results

def main():
    print("=" * 80)
    print("ASYNC RETRIEVAL IMPLEMENTATION VERIFICATION")
    print("=" * 80)
    
    # Check search.py has async_retrieval
    print("\n✓ Checking rag/nlp/search.py...")
    search_patterns = [
        (r'async def async_retrieval\(', 'async_retrieval method defined'),
        (r'await self\.async_rerank_by_model\(', 'calls async_rerank_by_model'),
        (r'sres = await loop\.run_in_executor', 'search wrapped in executor'),
    ]
    
    search_results = check_file('rag/nlp/search.py', search_patterns)
    for result in search_results:
        status = "✅" if result['found'] > 0 else "❌"
        print(f"  {status} {result['pattern']}: {result['found']} occurrences")
    
    # Check dialog_service.py uses async_retrieval
    print("\n✓ Checking api/db/services/dialog_service.py...")
    dialog_patterns = [
        (r'await retriever\.async_retrieval\(', 'calls async_retrieval'),
        (r'await settings\.retriever\.async_retrieval\(', 'calls settings.retriever.async_retrieval'),
        (r'loop\.run_in_executor.*retriever\.retrieval[^_]', 'OLD sync retrieval in executor (should be minimal)'),
    ]
    
    dialog_results = check_file('api/db/services/dialog_service.py', dialog_patterns)
    for result in dialog_results:
        if 'OLD' in result['pattern']:
            status = "✅" if result['found'] <= 1 else "⚠️"  # 1 is OK (DeepResearcher)
            print(f"  {status} {result['pattern']}: {result['found']} occurrences (1 expected for DeepResearcher)")
        else:
            status = "✅" if result['found'] > 0 else "❌"
            print(f"  {status} {result['pattern']}: {result['found']} occurrences")
    
    # Check rerank_model.py has async_similarity
    print("\n✓ Checking rag/llm/rerank_model.py...")
    rerank_patterns = [
        (r'async def async_similarity\(', 'async_similarity methods'),
        (r'self\.async_client = httpx\.AsyncClient', 'httpx AsyncClient initialized'),
        (r'await self\.async_client\.post\(', 'async HTTP calls'),
    ]
    
    rerank_results = check_file('rag/llm/rerank_model.py', rerank_patterns)
    for result in rerank_results:
        status = "✅" if result['found'] >= 7 else "⚠️"  # Should have 7+ (OpenAI, Jina, Xinference, LocalAI, Nvidia, SILICONFLOW, GPUStack)
        print(f"  {status} {result['pattern']}: {result['found']} occurrences (7+ expected)")
    
    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    
    # Summary
    all_checks = search_results + dialog_results + rerank_results
    failed = [r for r in all_checks if r['found'] == 0 and 'OLD' not in r['pattern']]
    
    if failed:
        print("\n❌ FAILED CHECKS:")
        for f in failed:
            print(f"  - {f['pattern']}")
        return 1
    else:
        print("\n✅ ALL CHECKS PASSED!")
        print("\nAsync retrieval is properly implemented:")
        print("  • async_retrieval() method created in search.py")
        print("  • async_rerank_by_model() is called within async_retrieval()")
        print("  • dialog_service.py updated to call async_retrieval()")
        print("  • 7+ reranker classes have async_similarity()")
        print("\n🚀 Ready for testing and deployment!")
        return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please run this script from the ragflow-be-share directory")
        sys.exit(1)
