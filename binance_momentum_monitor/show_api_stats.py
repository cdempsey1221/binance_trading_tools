#!/usr/bin/env python3
"""
Convenience script to display current API performance statistics
Usage: python show_api_stats.py
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.monitoring.reporter import print_api_stats, get_api_reporter
from src.monitoring.metrics import get_metrics_collector


def main():
    """Display current API statistics"""
    
    try:
        collector = get_metrics_collector()
        stats = collector.get_basic_stats()
        
        if stats['total_calls'] == 0:
            print("📊 No API calls recorded yet...")
            print("💡 Run the momentum scanner first to see API metrics.")
            return
        
        # Use the reporter to show detailed stats
        print_api_stats()
        
    except Exception as e:
        print(f"❌ Error displaying API stats: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
