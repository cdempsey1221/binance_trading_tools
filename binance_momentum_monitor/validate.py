#!/usr/bin/env python3
"""
Validation script for Phase 1 implementation
Checks that all components are properly configured and functional
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def check_imports():
    """Verify all imports work correctly"""
    print("🔍 Checking imports...")
    try:
        from src.core.config import Config, load_config
        from src.core.types import KlineBar, MomentumSignal, SymbolInfo
        from src.core.universe import SymbolUniverse
        from src.data.rest_client import BinanceRestClient
        from src.signals.momentum import MomentumDetector
        from src.alerts.manager import AlertManager
        from src.alerts.discord import DiscordNotifier
        from src.alerts.deduplication import AlertDeduplicationDB, AlertDeduplicationMySQL
        from src.monitoring.logger import get_logger
        print("  ✅ All imports successful")
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return False


def check_config():
    """Verify configuration system works"""
    print("\n🔍 Checking configuration system...")
    try:
        from src.core.config import Config
        
        # Test environment-based config
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://test.webhook.url'
        config = Config.from_env()
        
        assert config.signals.timeframe == '15m'
        assert config.universe.min_hourly_volume == 1000
        
        # Test validation
        config.validate()
        
        print("  ✅ Configuration system working")
        return True
    except Exception as e:
        print(f"  ❌ Configuration check failed: {e}")
        return False


def check_database():
    """Verify database operations work"""
    print("\n🔍 Checking database operations...")
    
    # Check if DATABASE_URL is set (production MySQL)
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        print("  → Testing MySQL database...")
        try:
            from src.alerts.deduplication import AlertDeduplicationMySQL
            from src.core.types import MomentumSignal
            from datetime import datetime
            
            db = AlertDeduplicationMySQL(database_url)
            
            # Create a test signal
            test_signal = MomentumSignal(
                symbol='BTCUSDT',
                timeframe='15m',
                candle_timestamp=int(datetime.now().timestamp()),
                volume_spike=1.5,
                price_change=2.5,
                volume_z_score=2.0,
                quote_volume=1000000.0,
                volume_building=True,
                higher_timeframe_alignment=True,
                momentum_score=6,
                signal_time=datetime.now()
            )
            
            # Test storage
            result = db.store_alert(test_signal)
            assert result is True, "First alert should be stored"
            
            # Test duplicate prevention
            result = db.store_alert(test_signal)
            assert result is False, "Duplicate alert should be rejected"
            
            # Test existence check
            exists = db.alert_exists(test_signal.symbol, test_signal.timeframe, test_signal.candle_timestamp)
            assert exists is True, "Alert should exist"
            
            print("  ✅ MySQL database operations working")
            return True
        except Exception as e:
            print(f"  ❌ MySQL database check failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("  → DATABASE_URL not set, testing SQLite fallback...")
        try:
            from src.alerts.deduplication import AlertDeduplicationDB
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
                db_path = f.name
            
            try:
                db = AlertDeduplicationDB(db_path)
                
                # Test storage
                result = db.store_alert('BTCUSDT', '15m', 1234567890, 'test_sig')
                assert result is True
                
                # Test duplicate prevention
                result = db.store_alert('BTCUSDT', '15m', 1234567890, 'test_sig')
                assert result is False
                
                # Test existence check
                exists = db.alert_exists('BTCUSDT', '15m', 1234567890)
                assert exists is True
                
                print("  ✅ SQLite database operations working")
                return True
            finally:
                os.unlink(db_path)
        except Exception as e:
            print(f"  ❌ SQLite database check failed: {e}")
            return False


def check_logging():
    """Verify logging system works"""
    print("\n🔍 Checking logging system...")
    try:
        from src.monitoring.logger import get_logger
        
        logger = get_logger('test_component', 'INFO')
        logger.info('test_event', 'Test message', data={'test': 'value'})
        
        print("  ✅ Logging system working")
        return True
    except Exception as e:
        print(f"  ❌ Logging check failed: {e}")
        return False


def check_file_structure():
    """Verify all expected files exist"""
    print("\n🔍 Checking file structure...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'MIGRATION.md',
        'PHASE1_SUMMARY.md',
        '.env.example',
        'start.sh',
        'config/default.yaml',
        'docker/Dockerfile',
        'docker/docker-compose.yml',
        'src/core/config.py',
        'src/core/types.py',
        'src/core/universe.py',
        'src/data/rest_client.py',
        'src/signals/momentum.py',
        'src/alerts/manager.py',
        'src/alerts/discord.py',
        'src/alerts/deduplication.py',
        'src/monitoring/logger.py',
        'tests/test_config.py',
        'tests/test_deduplication.py',
    ]
    
    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print(f"  ❌ Missing files:")
        for f in missing:
            print(f"     - {f}")
        return False
    else:
        print(f"  ✅ All {len(required_files)} required files present")
        return True


def check_rest_client():
    """Verify REST client basic functionality"""
    print("\n🔍 Checking REST client...")
    try:
        from src.data.rest_client import BinanceRestClient
        
        client = BinanceRestClient(rate_limit=1200)
        
        # Just verify initialization works
        assert client.rate_limit == 1200
        assert client.BASE_URL == "https://fapi.binance.com/fapi/v1"
        
        print("  ✅ REST client initialized")
        return True
    except Exception as e:
        print(f"  ❌ REST client check failed: {e}")
        return False


def main():
    """Run all validation checks"""
    print("="*60)
    print("Phase 1 Implementation Validation")
    print("="*60)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Imports", check_imports),
        ("Configuration", check_config),
        ("Database", check_database),
        ("Logging", check_logging),
        ("REST Client", check_rest_client),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"  ❌ Unexpected error in {name}: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20s} {status}")
    
    print("="*60)
    print(f"Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All validation checks passed!")
        print("Phase 1 implementation is complete and functional.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} check(s) failed.")
        print("Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
