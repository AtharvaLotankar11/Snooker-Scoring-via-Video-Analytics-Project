#!/usr/bin/env python3
"""
Logo Integration Test - Snooker Detection Pro
Test script to verify company logo integration
"""

import os
import sys
from pathlib import Path

def test_logo_files():
    """Test if logo files exist"""
    print("🏢 Testing Company Logo Integration")
    print("=" * 40)
    
    logo_dir = Path("common_logo")
    if not logo_dir.exists():
        print("❌ common_logo directory not found")
        return False
    
    required_logos = [
        "primary-logo.png",
        "color-logo1.png", 
        "color-logo2.png",
        "color-logo3.png"
    ]
    
    found_logos = 0
    for logo_file in required_logos:
        logo_path = logo_dir / logo_file
        if logo_path.exists():
            print(f"✅ Found: {logo_file}")
            found_logos += 1
        else:
            print(f"❌ Missing: {logo_file}")
    
    print(f"\n📊 Logo Files: {found_logos}/{len(required_logos)} found")
    return found_logos == len(required_logos)

def test_css_integration():
    """Test if CSS integration is working"""
    print("\n🎨 Testing CSS Integration")
    print("-" * 30)
    
    css_file = Path("static/css/company-logo-integration.css")
    if css_file.exists():
        print("✅ Company logo CSS file exists")
        
        # Check if it's imported in main.css
        main_css = Path("static/css/main.css")
        if main_css.exists():
            with open(main_css, 'r') as f:
                content = f.read()
                if 'company-logo-integration.css' in content:
                    print("✅ Logo CSS imported in main.css")
                    return True
                else:
                    print("❌ Logo CSS not imported in main.css")
                    return False
        else:
            print("❌ main.css not found")
            return False
    else:
        print("❌ Company logo CSS file not found")
        return False

def test_template_integration():
    """Test if templates have logo integration"""
    print("\n🌐 Testing Template Integration")
    print("-" * 30)
    
    templates_to_check = [
        ("templates/base.html", ["navbar-company-logo", "footer-company-logo"]),
        ("templates/index.html", ["hero-logo-backdrop", "powered-by-logo"]),
        ("templates/upload.html", ["card-logo-watermark"])
    ]
    
    all_passed = True
    
    for template_file, expected_classes in templates_to_check:
        template_path = Path(template_file)
        if template_path.exists():
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(template_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                
            found_classes = 0
            for css_class in expected_classes:
                if css_class in content:
                    found_classes += 1
            
            if found_classes == len(expected_classes):
                print(f"✅ {template_file}: All logo classes found ({found_classes}/{len(expected_classes)})")
            else:
                print(f"⚠️ {template_file}: Some logo classes missing ({found_classes}/{len(expected_classes)})")
                all_passed = False
        else:
            print(f"❌ {template_file}: Template not found")
            all_passed = False
    
    return all_passed

def test_javascript_integration():
    """Test if JavaScript integration is working"""
    print("\n📜 Testing JavaScript Integration")
    print("-" * 30)
    
    js_file = Path("static/js/company-logo-manager.js")
    if js_file.exists():
        print("✅ Company logo manager JS exists")
        
        # Check if it's included in base template
        base_template = Path("templates/base.html")
        if base_template.exists():
            with open(base_template, 'r') as f:
                content = f.read()
                if 'company-logo-manager.js' in content:
                    print("✅ Logo manager JS included in base template")
                    return True
                else:
                    print("❌ Logo manager JS not included in base template")
                    return False
        else:
            print("❌ base.html template not found")
            return False
    else:
        print("❌ Company logo manager JS not found")
        return False

def main():
    """Run all logo integration tests"""
    print("🎯 Company Logo Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Logo Files", test_logo_files),
        ("CSS Integration", test_css_integration),
        ("Template Integration", test_template_integration),
        ("JavaScript Integration", test_javascript_integration)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
    
    print(f"\n📊 LOGO INTEGRATION TEST RESULTS")
    print("=" * 40)
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL LOGO INTEGRATION TESTS PASSED!")
        print("🚀 Company logos are ready for display")
        print("\n💡 Next Steps:")
        print("1. Start the Flask application: python web_app.py")
        print("2. Open browser to http://localhost:5000")
        print("3. Check navbar, footer, and page logos")
        print("4. Test hover effects and animations")
        return True
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests failed")
        print("🔧 Please fix the issues before proceeding")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)