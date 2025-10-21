#!/usr/bin/env python3
"""
Theme System Testing Script - Snooker Detection Pro
Comprehensive testing and validation of the UI theming system
"""

import os
import sys
import json
import time
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and report status"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description} MISSING: {file_path}")
        return False

def check_css_imports(css_file):
    """Check CSS imports in a file"""
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        imports = []
        for line in content.split('\n'):
            if '@import' in line:
                imports.append(line.strip())
                
        return imports
    except Exception as e:
        print(f"❌ Error reading {css_file}: {e}")
        return []

def validate_css_syntax(css_file):
    """Basic CSS syntax validation"""
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Basic checks
        open_braces = content.count('{')
        close_braces = content.count('}')
        
        if open_braces != close_braces:
            print(f"⚠️ CSS syntax warning in {css_file}: Mismatched braces ({open_braces} open, {close_braces} close)")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error validating {css_file}: {e}")
        return False

def check_brand_colors(css_file):
    """Check if brand colors are properly defined"""
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        required_colors = {
            '--brand-blue-primary': '#0B405B',
            '--brand-green-secondary': '#94D82A'
        }
        
        found_colors = {}
        for color_var, expected_value in required_colors.items():
            if color_var in content:
                # Extract the value (basic extraction)
                lines = content.split('\n')
                for line in lines:
                    if color_var in line and ':' in line:
                        value = line.split(':')[1].strip().rstrip(';')
                        found_colors[color_var] = value
                        break
                        
        return found_colors
    except Exception as e:
        print(f"❌ Error checking brand colors in {css_file}: {e}")
        return {}

def validate_javascript_syntax(js_file):
    """Basic JavaScript syntax validation"""
    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Basic checks
        open_parens = content.count('(')
        close_parens = content.count(')')
        open_braces = content.count('{')
        close_braces = content.count('}')
        open_brackets = content.count('[')
        close_brackets = content.count(']')
        
        issues = []
        if open_parens != close_parens:
            issues.append(f"Mismatched parentheses ({open_parens} open, {close_parens} close)")
        if open_braces != close_braces:
            issues.append(f"Mismatched braces ({open_braces} open, {close_braces} close)")
        if open_brackets != close_brackets:
            issues.append(f"Mismatched brackets ({open_brackets} open, {close_brackets} close)")
            
        if issues:
            for issue in issues:
                print(f"⚠️ JavaScript syntax warning in {js_file}: {issue}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error validating {js_file}: {e}")
        return False

def check_template_syntax(template_file):
    """Basic template syntax validation"""
    try:
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for unclosed tags
        open_tags = content.count('<script')
        close_tags = content.count('</script>')
        
        if open_tags != close_tags:
            print(f"⚠️ Template warning in {template_file}: Mismatched script tags ({open_tags} open, {close_tags} close)")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error validating {template_file}: {e}")
        return False

def test_project_structure():
    """Test basic project structure"""
    print("📁 Testing project structure...")
    
    required_dirs = [
        'src', 'static', 'templates', 'models', 'dataset'
    ]
    
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")

def test_core_imports():
    """Test core Python imports"""
    print("🐍 Testing core imports...")
    
    try:
        import cv2
        print("✅ OpenCV imported successfully")
    except ImportError:
        print("❌ OpenCV import failed")
    
    try:
        import numpy as np
        print("✅ NumPy imported successfully")
    except ImportError:
        print("❌ NumPy import failed")
    
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError:
        print("❌ Flask import failed")

def run_comprehensive_tests():
    """Run comprehensive theme system tests"""
    print("🚀 Starting Theme System Comprehensive Tests")
    print("=" * 50)
    
    # Test results
    results = {
        'files_checked': 0,
        'files_passed': 0,
        'files_failed': 0,
        'warnings': 0,
        'errors': 0
    }
    
    # Test project structure
    test_project_structure()
    
    # Test core imports
    test_core_imports()
    
    # 1. Check CSS Files
    print("\n📄 Checking CSS Files...")
    css_files = [
        'static/css/main.css',
        'static/css/themes/brand-colors.css',
        'static/css/themes/light-theme.css',
        'static/css/themes/dark-theme.css',
        'static/css/themes/theme-components.css',
        'static/css/theme-transitions.css',
        'static/css/responsive-theming.css',
        'static/css/components/navigation.css',
        'static/css/components/cards.css',
        'static/css/components/buttons.css',
        'static/css/components/forms.css',
        'static/css/components/data-viz.css'
    ]
    
    for css_file in css_files:
        results['files_checked'] += 1
        if check_file_exists(css_file, "CSS File"):
            if validate_css_syntax(css_file):
                results['files_passed'] += 1
            else:
                results['files_failed'] += 1
                results['warnings'] += 1
        else:
            results['files_failed'] += 1
            results['errors'] += 1
    
    # 2. Check JavaScript Files
    print("\n📜 Checking JavaScript Files...")
    js_files = [
        'static/js/theme-manager.js',
        'static/js/theme-switcher.js',
        'static/js/theme-persistence.js',
        'static/js/logo-manager.js',
        'static/js/accessibility-enhancer.js',
        'static/js/theme-performance-optimizer.js',
        'static/js/brand-compliance-validator.js',
        'static/js/theme-system-debugger.js'
    ]
    
    for js_file in js_files:
        results['files_checked'] += 1
        if check_file_exists(js_file, "JavaScript File"):
            if validate_javascript_syntax(js_file):
                results['files_passed'] += 1
            else:
                results['files_failed'] += 1
                results['warnings'] += 1
        else:
            results['files_failed'] += 1
            results['errors'] += 1
    
    # 3. Check Template Files
    print("\n🌐 Checking Template Files...")
    template_files = [
        'templates/base.html',
        'templates/index.html',
        'templates/upload.html',
        'templates/results.html'
    ]
    
    for template_file in template_files:
        results['files_checked'] += 1
        if check_file_exists(template_file, "Template File"):
            if check_template_syntax(template_file):
                results['files_passed'] += 1
            else:
                results['files_failed'] += 1
                results['warnings'] += 1
        else:
            results['files_failed'] += 1
            results['errors'] += 1
    
    # 4. Check Logo Assets
    print("\n🖼️ Checking Logo Assets...")
    logo_files = [
        'static/assets/logos/logo-light.svg',
        'static/assets/logos/logo-dark.svg',
        'static/assets/logos/icon-light.svg',
        'static/assets/logos/icon-dark.svg'
    ]
    
    for logo_file in logo_files:
        results['files_checked'] += 1
        if check_file_exists(logo_file, "Logo Asset"):
            results['files_passed'] += 1
        else:
            results['files_failed'] += 1
            results['errors'] += 1
    
    # 5. Check Brand Colors
    print("\n🎨 Checking Brand Colors...")
    if os.path.exists('static/css/themes/brand-colors.css'):
        brand_colors = check_brand_colors('static/css/themes/brand-colors.css')
        
        expected_colors = {
            '--brand-blue-primary': '#0B405B',
            '--brand-green-secondary': '#94D82A'
        }
        
        for color_var, expected_value in expected_colors.items():
            if color_var in brand_colors:
                if expected_value in brand_colors[color_var]:
                    print(f"✅ Brand color {color_var}: {brand_colors[color_var]}")
                else:
                    print(f"⚠️ Brand color {color_var} incorrect: expected {expected_value}, got {brand_colors[color_var]}")
                    results['warnings'] += 1
            else:
                print(f"❌ Brand color {color_var} not found")
                results['errors'] += 1
    
    # 6. Generate Report
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    print(f"📁 Files Checked: {results['files_checked']}")
    print(f"✅ Files Passed: {results['files_passed']}")
    print(f"❌ Files Failed: {results['files_failed']}")
    print(f"⚠️ Warnings: {results['warnings']}")
    print(f"🚨 Errors: {results['errors']}")
    
    # Calculate success rate
    success_rate = (results['files_passed'] / results['files_checked']) * 100 if results['files_checked'] > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    # Overall status
    if results['errors'] == 0 and results['warnings'] == 0:
        print("\n🎉 ALL TESTS PASSED! Theme system is ready for production.")
        return True
    elif results['errors'] == 0:
        print("\n✅ TESTS PASSED with warnings. Theme system is functional but could be improved.")
        return True
    else:
        print("\n❌ TESTS FAILED. Please fix the errors before proceeding.")
        return False

if __name__ == "__main__":
    print("🎨 Snooker Detection Pro - Theme System Validator")
    print("=" * 50)
    
    # Run comprehensive tests
    success = run_comprehensive_tests()
    
    print("\n💡 NEXT STEPS:")
    if success:
        print("1. Start the Flask application: python web_app.py")
        print("2. Open browser and navigate to http://localhost:5000")
        print("3. Run debugThemeSystem() in browser console")
        print("4. Test theme switching and all features")
    else:
        print("1. Fix all reported errors")
        print("2. Re-run this test script")
        print("3. Proceed only when all tests pass")
    
    print("\n🔍 For browser testing:")
    print("   - Open Developer Tools (F12)")
    print("   - Run: debugThemeSystem()")
    print("   - Run: quickHealthCheck()")
    print("   - Check console for any errors")
    
    sys.exit(0 if success else 1)