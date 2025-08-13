#!/usr/bin/env python3
"""
Performance testing script for database indexes.
Tests query performance before and after index creation.
"""

import logging
import time
import sys
from pathlib import Path
from sqlalchemy import text, func
from typing import List, Dict, Tuple

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / "app"))

from app.core.config import settings
from app.db.database import engine, get_db
from app.db.models import User, Document, Query, EmailAccount, Email, EmailAttachment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PerformanceTestSuite:
    """Performance testing for database queries."""
    
    def __init__(self):
        self.engine = engine
        self.test_queries = self._define_test_queries()
    
    def _define_test_queries(self) -> List[Dict]:
        """Define test queries that benefit from indexing."""
        return [
            {
                'name': 'User Email Count',
                'query': 'SELECT COUNT(*) FROM emails WHERE user_id = 1',
                'description': 'Count emails for a specific user (very common)'
            },
            {
                'name': 'Account Email Filtering',
                'query': 'SELECT COUNT(*) FROM emails WHERE email_account_id = 1',
                'description': 'Filter emails by account (common)'
            },
            {
                'name': 'Email Type Filtering',
                'query': 'SELECT COUNT(*) FROM emails WHERE email_type = \'business\'',
                'description': 'Filter emails by type (common)'
            },
            {
                'name': 'Unread Email Count',
                'query': 'SELECT COUNT(*) FROM emails WHERE user_id = 1 AND is_read = 0',
                'description': 'Count unread emails for user (very common)'
            },
            {
                'name': 'User + Account Composite',
                'query': 'SELECT COUNT(*) FROM emails WHERE user_id = 1 AND email_account_id = 1',
                'description': 'User + account filtering (most common pattern)'
            },
            {
                'name': 'Recent Emails Timeline',
                'query': '''SELECT id, subject, sent_at FROM emails 
                           WHERE user_id = 1 
                           ORDER BY sent_at DESC LIMIT 20''',
                'description': 'Recent emails timeline (very common)'
            },
            {
                'name': 'User Documents',
                'query': 'SELECT COUNT(*) FROM documents WHERE owner_id = 1',
                'description': 'User document queries'
            },
            {
                'name': 'User Query History',
                'query': 'SELECT COUNT(*) FROM queries WHERE user_id = 1',
                'description': 'User query history'
            },
            {
                'name': 'Email Attachments',
                'query': 'SELECT COUNT(*) FROM email_attachments WHERE email_id IN (SELECT id FROM emails WHERE user_id = 1 LIMIT 10)',
                'description': 'Email attachment lookups'
            },
            {
                'name': 'Active Email Accounts',
                'query': 'SELECT COUNT(*) FROM email_accounts WHERE user_id = 1 AND is_active = 1',
                'description': 'Active email accounts for user'
            },
            {
                'name': 'Complex Multi-Join',
                'query': '''SELECT e.subject, ea.email_address, COUNT(att.id) as attachment_count
                           FROM emails e 
                           JOIN email_accounts ea ON e.email_account_id = ea.id
                           LEFT JOIN email_attachments att ON e.id = att.email_id
                           WHERE e.user_id = 1 AND e.email_type = 'business'
                           GROUP BY e.id, e.subject, ea.email_address
                           LIMIT 10''',
                'description': 'Complex query with multiple joins and grouping'
            }
        ]
    
    def execute_query_with_timing(self, query: str, description: str) -> Tuple[float, int]:
        """Execute a query and measure its performance."""
        try:
            with self.engine.connect() as conn:
                start_time = time.time()
                result = conn.execute(text(query))
                end_time = time.time()
                
                # Get result count if it's a COUNT query
                if 'COUNT(*)' in query.upper():
                    count = result.fetchone()[0] if result.rowcount != -1 else 0
                else:
                    rows = result.fetchall()
                    count = len(rows)
                
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                return execution_time, count
                
        except Exception as e:
            logger.error(f"Error executing query '{description}': {e}")
            return -1, 0
    
    def run_performance_test(self, test_name: str = "Performance Test") -> Dict:
        """Run all performance tests and return results."""
        logger.info(f"🚀 Starting {test_name}")
        logger.info("=" * 60)
        
        results = {
            'test_name': test_name,
            'queries': [],
            'total_time': 0,
            'avg_time': 0
        }
        
        total_time = 0
        
        for i, test_query in enumerate(self.test_queries, 1):
            name = test_query['name']
            query = test_query['query']
            description = test_query['description']
            
            logger.info(f"[{i}/{len(self.test_queries)}] Testing: {name}")
            logger.info(f"  Description: {description}")
            
            # Run query multiple times for better average
            times = []
            record_count = 0
            
            for run in range(3):  # Run each query 3 times
                exec_time, count = self.execute_query_with_timing(query, description)
                if exec_time >= 0:
                    times.append(exec_time)
                    record_count = count
            
            if times:
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                
                logger.info(f"  Records: {record_count:,}")
                logger.info(f"  Avg Time: {avg_time:.2f}ms")
                logger.info(f"  Min Time: {min_time:.2f}ms") 
                logger.info(f"  Max Time: {max_time:.2f}ms")
                
                results['queries'].append({
                    'name': name,
                    'description': description,
                    'avg_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'record_count': record_count
                })
                
                total_time += avg_time
            else:
                logger.error(f"  ❌ Failed to execute query")
                results['queries'].append({
                    'name': name,
                    'description': description,
                    'avg_time': -1,
                    'min_time': -1,
                    'max_time': -1,
                    'record_count': 0
                })
            
            logger.info("")  # Blank line for readability
        
        results['total_time'] = total_time
        results['avg_time'] = total_time / len(self.test_queries) if self.test_queries else 0
        
        logger.info("=" * 60)
        logger.info(f"📊 {test_name} Summary")
        logger.info(f"Total execution time: {total_time:.2f}ms")
        logger.info(f"Average query time: {results['avg_time']:.2f}ms")
        logger.info("")
        
        return results
    
    def compare_performance(self, before_results: Dict, after_results: Dict) -> None:
        """Compare performance results before and after optimization."""
        logger.info("📈 Performance Comparison Report")
        logger.info("=" * 80)
        
        logger.info(f"{'Query Name':<25} {'Before (ms)':<12} {'After (ms)':<12} {'Improvement':<15} {'Records':<10}")
        logger.info("-" * 80)
        
        total_improvement = 0
        improved_queries = 0
        
        for before_q, after_q in zip(before_results['queries'], after_results['queries']):
            if before_q['avg_time'] > 0 and after_q['avg_time'] > 0:
                improvement_ratio = before_q['avg_time'] / after_q['avg_time']
                improvement_pct = ((before_q['avg_time'] - after_q['avg_time']) / before_q['avg_time']) * 100
                
                if improvement_ratio > 1.1:  # At least 10% improvement
                    improvement_str = f"{improvement_ratio:.1f}x faster"
                    improved_queries += 1
                elif improvement_pct > 5:
                    improvement_str = f"{improvement_pct:.1f}% faster"
                    improved_queries += 1
                elif improvement_pct < -5:
                    improvement_str = f"{abs(improvement_pct):.1f}% slower"
                else:
                    improvement_str = "~same"
                
                total_improvement += improvement_ratio
                
                logger.info(f"{before_q['name']:<25} {before_q['avg_time']:<12.2f} {after_q['avg_time']:<12.2f} {improvement_str:<15} {after_q['record_count']:<10,}")
            else:
                logger.info(f"{before_q['name']:<25} {'ERROR':<12} {'ERROR':<12} {'N/A':<15} {'N/A':<10}")
        
        logger.info("-" * 80)
        
        # Overall summary
        if improved_queries > 0:
            avg_improvement = total_improvement / len(before_results['queries'])
            overall_before = before_results['total_time']
            overall_after = after_results['total_time']
            overall_improvement = overall_before / overall_after if overall_after > 0 else 1
            
            logger.info(f"📊 Overall Performance Summary:")
            logger.info(f"  Queries improved: {improved_queries}/{len(before_results['queries'])}")
            logger.info(f"  Average improvement: {avg_improvement:.1f}x faster")
            logger.info(f"  Total time before: {overall_before:.2f}ms")
            logger.info(f"  Total time after: {overall_after:.2f}ms")
            logger.info(f"  Overall improvement: {overall_improvement:.1f}x faster")
            
            if overall_improvement > 2:
                logger.info("🎉 Excellent performance improvement!")
            elif overall_improvement > 1.5:
                logger.info("✅ Good performance improvement!")
            elif overall_improvement > 1.1:
                logger.info("👍 Moderate performance improvement")
            else:
                logger.info("📝 Minor performance change")
        else:
            logger.info("⚠️  No significant performance improvements detected")
    
    def analyze_database_stats(self) -> Dict:
        """Analyze current database statistics."""
        stats = {}
        
        try:
            with self.engine.connect() as conn:
                # Get table sizes
                tables = ['users', 'documents', 'queries', 'email_accounts', 'emails', 'email_attachments', 'oauth_sessions']
                
                for table in tables:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.fetchone()[0]
                    stats[table] = count
                
                # Get index information (SQLite specific)
                result = conn.execute(text("""
                    SELECT name, tbl_name 
                    FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                    ORDER BY tbl_name, name
                """))
                
                indexes = result.fetchall()
                stats['indexes'] = [{'name': idx[0], 'table': idx[1]} for idx in indexes]
                
        except Exception as e:
            logger.error(f"Error analyzing database stats: {e}")
        
        return stats
    
    def print_database_summary(self) -> None:
        """Print a summary of the current database state."""
        stats = self.analyze_database_stats()
        
        logger.info("📊 Database Summary")
        logger.info("=" * 40)
        
        logger.info("Table Sizes:")
        total_records = 0
        for table, count in stats.items():
            if table != 'indexes':
                logger.info(f"  {table}: {count:,} records")
                total_records += count
        
        logger.info(f"  Total: {total_records:,} records")
        logger.info("")
        
        if 'indexes' in stats:
            logger.info(f"Current Indexes: {len(stats['indexes'])}")
            by_table = {}
            for idx in stats['indexes']:
                table = idx['table']
                if table not in by_table:
                    by_table[table] = []
                by_table[table].append(idx['name'])
            
            for table, indexes in by_table.items():
                logger.info(f"  {table}: {len(indexes)} indexes")
        
        logger.info("")


def main():
    """Main function to run performance tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test database query performance")
    parser.add_argument("--before", action="store_true", help="Run before migration test")
    parser.add_argument("--after", action="store_true", help="Run after migration test")
    parser.add_argument("--compare", action="store_true", help="Compare before/after results from files")
    
    args = parser.parse_args()
    
    suite = PerformanceTestSuite()
    
    if args.before:
        suite.print_database_summary()
        results = suite.run_performance_test("Before Index Migration")
        
        # Save results to file
        import json
        with open("performance_before.json", "w") as f:
            json.dump(results, f, indent=2)
        logger.info("💾 Results saved to performance_before.json")
    
    elif args.after:
        suite.print_database_summary()
        results = suite.run_performance_test("After Index Migration")
        
        # Save results to file
        import json
        with open("performance_after.json", "w") as f:
            json.dump(results, f, indent=2)
        logger.info("💾 Results saved to performance_after.json")
    
    elif args.compare:
        import json
        try:
            with open("performance_before.json", "r") as f:
                before_results = json.load(f)
            with open("performance_after.json", "r") as f:
                after_results = json.load(f)
            
            suite.compare_performance(before_results, after_results)
        except FileNotFoundError as e:
            logger.error(f"Could not find results files: {e}")
            logger.error("Run with --before and --after first")
    
    else:
        # Run both tests for immediate comparison
        suite.print_database_summary()
        
        logger.info("Running performance test with current database state...")
        current_results = suite.run_performance_test("Current Performance")
        
        # Show recommendations
        logger.info("🎯 Performance Optimization Recommendations:")
        logger.info("1. Run: python migrate_add_performance_indexes.py")
        logger.info("2. Run: python test_performance_indexes.py --after")
        logger.info("3. Compare results to see improvements")


if __name__ == "__main__":
    main()