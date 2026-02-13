#!/usr/bin/env python3
"""
Test script to verify CostMinimizer module import and App functionality.
"""

import sys
import os
import logging

def test_costminimizer_import():
    """Test importing CostMinimizer module and App class."""
    print("Testing CostMinimizer module import...")
    
    try:
        # Add src directory to Python path
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # Test basic import
        from CostMinimizer import App
        print("✅ Successfully imported CostMinimizer.App")
        
        # Test App instantiation
        app = App(mode='module')
        print("✅ Successfully created App instance in module mode")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error creating App instance: {e}")
        return False

def test_app_initialization():
    """Test App class initialization with different modes."""
    try:
        from CostMinimizer import App
        
        # Test module mode
        app_module = App(mode='module')
        print("✅ App initialized in module mode")
        
        # Test default mode
        app_default = App()
        print("✅ App initialized in default mode")
        
        return True
        
    except Exception as e:
        print(f"❌ App initialization failed: {e}")
        return False

def test_costminimizer_ce_launch():
    """Test launching CostMinimizer with --ce --checks ALL parameters."""
    try:
        from CostMinimizer import App
        
        # Backup original sys.argv
        original_argv = sys.argv.copy()
        
        # Set command line arguments for CE report with all checks
        sys.argv = ['CostMinimizer', '--ce', '--checks', 'ALL']
        print(f"🚀 Testing CostMinimizer launch with: {sys.argv[1:]}")
        
        # Create and run app in module mode
        app = App(mode='module')
        result = app.main()
        
        print("✅ CostMinimizer launched successfully with --ce --checks ALL")
        return True
        
    except Exception as e:
        print(f"❌ CostMinimizer launch failed: {e}")
        return False
    finally:
        # Restore original sys.argv
        sys.argv = original_argv

def test_costminimizer_cur_launch():
    """Test launching CostMinimizer with --cur --checks ALL parameters."""
    try:
        from CostMinimizer import App
        
        # Backup original sys.argv
        original_argv = sys.argv.copy()
        
        # Set command line arguments for CUR report with all checks
        sys.argv = ['CostMinimizer', '--cur', '--checks', 'ALL']
        print(f"🚀 Testing CostMinimizer launch with: {sys.argv[1:]}")
        
        # Create and run app in module mode
        app = App(mode='module')
        result = app.main()
        
        print("✅ CostMinimizer launched successfully with --cur --checks ALL")
        return True
        
    except Exception as e:
        print(f"❌ CostMinimizer CUR launch failed: {e}")
        return False
    finally:
        # Restore original sys.argv
        sys.argv = original_argv

def test_costminimizer_ta_launch():
    """Test launching CostMinimizer with --ta --checks ALL parameters."""
    try:
        from CostMinimizer import App
        
        # Backup original sys.argv
        original_argv = sys.argv.copy()
        
        # Set command line arguments for TA report with all checks
        sys.argv = ['CostMinimizer', '--ta', '--checks', 'ALL']
        print(f"🚀 Testing CostMinimizer launch with: {sys.argv[1:]}")
        
        # Create and run app in module mode
        app = App(mode='module')
        result = app.main()
        
        print("✅ CostMinimizer launched successfully with --ta --checks ALL")
        return True
        
    except Exception as e:
        print(f"❌ CostMinimizer TA launch failed: {e}")
        return False
    finally:
        # Restore original sys.argv
        sys.argv = original_argv

def test_costminimizer_co_launch():
    """Test launching CostMinimizer with --co --checks ALL parameters."""
    try:
        from CostMinimizer import App
        
        # Backup original sys.argv
        original_argv = sys.argv.copy()
        
        # Set command line arguments for CO report with all checks
        sys.argv = ['CostMinimizer', '--co', '--checks', 'ALL']
        print(f"🚀 Testing CostMinimizer launch with: {sys.argv[1:]}")
        
        # Create and run app in module mode
        app = App(mode='module')
        result = app.main()
        
        print("✅ CostMinimizer launched successfully with --co --checks ALL")
        return True
        
    except Exception as e:
        print(f"❌ CostMinimizer CO launch failed: {e}")
        return False
    finally:
        # Restore original sys.argv
        sys.argv = original_argv

def main():
    """Run all tests."""
    print("=" * 50)
    print("CostMinimizer Module Import Test")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    tests = [
        ("Import Test", test_costminimizer_import),
        ("App Initialization Test", test_app_initialization),
        ("CostMinimizer Launch Test", test_costminimizer_ce_launch),
        ("CostMinimizer CUR Launch Test", test_costminimizer_cur_launch),
        ("CostMinimizer TA Launch Test", test_costminimizer_ta_launch),
        ("CostMinimizer CO Launch Test", test_costminimizer_co_launch)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! CostMinimizer module is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())