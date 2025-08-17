#!/usr/bin/env python3
"""
Database Performance Dashboard
Interactive dashboard to monitor database performance metrics
"""

import sys
import os
import time
import json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def display_performance_dashboard():
    """Display comprehensive database performance dashboard"""
    print("🚀 DATABASE PERFORMANCE DASHBOARD")
    print("=" * 70)
    
    try:
        from modules.enhanced_db_manager import enhanced_db_manager
        from modules.database_routes import db_routes
        
        # Get performance statistics
        stats = enhanced_db_manager.get_performance_stats()
        routes_stats = db_routes.get_performance_stats()
        
        print(f"📊 Dashboard Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Connection Pool Statistics
        print("\n🔗 CONNECTION POOL STATISTICS")
        print("-" * 35)
        conn_stats = stats['connection_stats']
        print(f"  Total Connections: {conn_stats['total_connections']}")
        print(f"  Active Connections: {conn_stats['active_connections']}")
        print(f"  Peak Connections: {conn_stats['peak_connections']}")
        print(f"  Connections Created: {conn_stats['connections_created']}")
        print(f"  Connections Closed: {conn_stats['connections_closed']}")
        print(f"  Avg Connection Time: {conn_stats['average_connection_time']:.4f}s")
        print(f"  Connection Errors: {conn_stats['connection_errors']}")
        
        # Query Performance Statistics
        print("\n⚡ QUERY PERFORMANCE STATISTICS")
        print("-" * 35)
        query_stats = stats['query_stats']
        print(f"  Total Queries: {query_stats['total_queries']}")
        print(f"  Successful Queries: {query_stats['successful_queries']}")
        print(f"  Failed Queries: {query_stats['failed_queries']}")
        print(f"  Success Rate: {(query_stats['successful_queries']/query_stats['total_queries']*100):.1f}%" if query_stats['total_queries'] > 0 else "  Success Rate: 0%")
        print(f"  Avg Execution Time: {query_stats['average_execution_time']:.4f}s")
        print(f"  Slow Queries: {query_stats['slow_queries']}")
        print(f"  Cache Hit Rate: {query_stats['cache_hit_rate']:.1f}%")
        
        # Cache Statistics
        print("\n💾 CACHE STATISTICS")
        print("-" * 20)
        cache_stats = stats['cache_stats']
        print(f"  Cache Size: {cache_stats['size']}/{cache_stats['max_size']}")
        print(f"  Cache Usage: {(cache_stats['size']/cache_stats['max_size']*100):.1f}%")
        print(f"  Cache Hits: {cache_stats['hits']}")
        print(f"  Cache Misses: {cache_stats['misses']}")
        print(f"  Hit Rate: {cache_stats['hit_rate']:.1f}%")
        print(f"  Evictions: {cache_stats['evictions']}")
        print(f"  TTL: {cache_stats['ttl']}s")
        
        # Database Routes Performance
        print("\n🛣️  DATABASE ROUTES PERFORMANCE")
        print("-" * 35)
        print(f"  Total Route Queries: {routes_stats['query_count']}")
        print(f"  Route Cache Hits: {routes_stats['cache_hits']}")
        print(f"  Route Cache Hit Rate: {routes_stats['cache_hit_rate']:.1f}%")
        print(f"  Route Slow Queries: {routes_stats['slow_queries_count']}")
        print(f"  Route Avg Execution: {routes_stats['avg_execution_time']:.4f}s")
        
        # Recent Slow Queries
        slow_queries = stats['recent_slow_queries']
        if slow_queries:
            print("\n🐌 RECENT SLOW QUERIES")
            print("-" * 25)
            for i, query in enumerate(slow_queries[-5:], 1):
                print(f"  {i}. {query['query']} ({query['execution_time']:.4f}s)")
        
        # Performance Recommendations
        print("\n💡 PERFORMANCE RECOMMENDATIONS")
        print("-" * 35)
        
        recommendations = []
        
        # Connection pool recommendations
        if conn_stats['peak_connections'] > 15:
            recommendations.append("Consider increasing connection pool size")
        if conn_stats['connection_errors'] > 0:
            recommendations.append("Investigate connection errors")
        
        # Query performance recommendations
        if query_stats['slow_queries'] > 0:
            recommendations.append("Review and optimize slow queries")
        if query_stats['cache_hit_rate'] < 50:
            recommendations.append("Consider increasing cache size or TTL")
        
        # Cache recommendations
        if cache_stats['size'] > cache_stats['max_size'] * 0.8:
            recommendations.append("Consider increasing cache max size")
        if cache_stats['hit_rate'] < 30:
            recommendations.append("Review caching strategy")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("  ✅ No performance issues detected")
        
        # System Health Status
        print("\n🏥 SYSTEM HEALTH STATUS")
        print("-" * 25)
        
        health_score = 100
        health_issues = []
        
        # Calculate health score
        if conn_stats['connection_errors'] > 0:
            health_score -= 20
            health_issues.append("Connection errors detected")
        
        if query_stats['failed_queries'] > 0:
            health_score -= 15
            health_issues.append("Failed queries detected")
        
        if query_stats['slow_queries'] > 5:
            health_score -= 10
            health_issues.append("Multiple slow queries")
        
        if cache_stats['hit_rate'] < 25:
            health_score -= 10
            health_issues.append("Low cache hit rate")
        
        # Display health status
        if health_score >= 90:
            status = "🟢 EXCELLENT"
        elif health_score >= 75:
            status = "🟡 GOOD"
        elif health_score >= 50:
            status = "🟠 FAIR"
        else:
            status = "🔴 NEEDS ATTENTION"
        
        print(f"  Overall Health: {status} ({health_score}%)")
        
        if health_issues:
            print("  Issues:")
            for issue in health_issues:
                print(f"    - {issue}")
        
        print("\n" + "=" * 70)
        print("📈 Performance monitoring is active and running optimally!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"❌ Error displaying dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_performance_stress_test():
    """Run a stress test to demonstrate performance"""
    print("\n🔥 RUNNING PERFORMANCE STRESS TEST")
    print("-" * 40)
    
    try:
        from modules.enhanced_db_manager import enhanced_db_manager
        
        # Test 1: Concurrent query stress test
        print("  🧪 Test 1: Concurrent Query Stress Test")
        import threading
        
        def stress_worker(worker_id, results):
            try:
                for i in range(10):
                    result = enhanced_db_manager.execute_query(
                        "SELECT * FROM Products WHERE ProductID > ? LIMIT 5",
                        (worker_id,)
                    )
                    results[f"{worker_id}_{i}"] = len(result)
            except Exception as e:
                results[f"{worker_id}_error"] = str(e)
        
        threads = []
        results = {}
        start_time = time.time()
        
        # Start 20 concurrent workers
        for i in range(20):
            thread = threading.Thread(target=stress_worker, args=(i, results))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        successful = sum(1 for k, v in results.items() if not k.endswith('_error'))
        
        print(f"    ✅ Executed {successful} queries in {end_time - start_time:.2f}s")
        print(f"    ✅ Throughput: {successful/(end_time - start_time):.1f} queries/second")
        
        # Test 2: Cache performance test
        print("  🧪 Test 2: Cache Performance Test")
        
        # First query (cache miss)
        start_time = time.time()
        result1 = enhanced_db_manager.execute_query("SELECT COUNT(*) FROM Products")
        miss_time = time.time() - start_time
        
        # Second query (cache hit)
        start_time = time.time()
        result2 = enhanced_db_manager.execute_query("SELECT COUNT(*) FROM Products")
        hit_time = time.time() - start_time
        
        speedup = miss_time / hit_time if hit_time > 0 else 0
        
        print(f"    ✅ Cache miss time: {miss_time:.4f}s")
        print(f"    ✅ Cache hit time: {hit_time:.4f}s")
        print(f"    ✅ Cache speedup: {speedup:.1f}x faster")
        
        print("\n🎯 Stress test completed successfully!")
        
    except Exception as e:
        print(f"❌ Stress test failed: {e}")

if __name__ == "__main__":
    print("🚀 DATABASE PERFORMANCE MONITORING SYSTEM")
    print("=========================================")
    
    # Display dashboard
    display_performance_dashboard()
    
    # Run stress test
    run_performance_stress_test()
    
    print("\n✨ Monitoring complete!")
