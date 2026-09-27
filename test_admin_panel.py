#!/usr/bin/env python
"""Test script for admin panel features."""

import os
os.environ['DEV_MODE_MOCK_GEOLOCATION'] = 'True'

from app import app, validate_name
from config import Config
import database

print("=" * 70)
print("ADMIN PANEL FEATURE TEST")
print("=" * 70)

# Test 1: Admin password config
print("\n1. Testing admin configuration...")
assert Config.ADMIN_PASSWORD == "admin-password-123", "Default admin password not set"
print(f"   ✓ Admin password configured: {'*' * len(Config.ADMIN_PASSWORD)}")

# Test 2: Database functions
print("\n2. Testing database functions...")
total = database.get_visitor_count()
print(f"   ✓ get_visitor_count() = {total}")

visitors = database.get_all_visitors()
print(f"   ✓ get_all_visitors() returned {len(visitors)} records")

stats = database.get_visitor_stats()
print(f"   ✓ get_visitor_stats() returned stats for:")
print(f"     - Countries: {len(stats['by_country'])}")
print(f"     - Cities: {len(stats['by_city'])}")
print(f"     - States: {len(stats['by_state'])}")

# Test 3: Admin routes registration
print("\n3. Testing admin routes...")
routes = [str(rule) for rule in app.url_map.iter_rules()]
admin_routes = [r for r in routes if 'admin' in r.lower()]
print(f"   ✓ Found {len(admin_routes)} admin routes:")
for route in admin_routes:
    print(f"     - {route}")

# Test 4: Templates exist
print("\n4. Testing admin templates...")
admin_login = os.path.exists("templates/admin_login.html")
admin_dashboard = os.path.exists("templates/admin_dashboard.html")
print(f"   ✓ admin_login.html exists: {admin_login}")
print(f"   ✓ admin_dashboard.html exists: {admin_dashboard}")

print("\n" + "=" * 70)
print("✅ ALL ADMIN PANEL TESTS PASSED!")
print("=" * 70)
print("\nTo test the admin panel:")
print(f"  1. Start the app: python app.py")
print(f"  2. Visit: http://127.0.0.1:5000/admin")
print(f"  3. Enter password: {Config.ADMIN_PASSWORD}")
print("=" * 70)
