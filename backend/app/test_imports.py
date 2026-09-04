#!/usr/bin/env python3
"""
Test backend imports without running server.
This tests all modules can be imported correctly.
"""

import sys
from pathlib import Path

# Set Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("BACKEND IMPORT TEST")
print("=" * 80)

# Test core modules
print("\n[1] Testing Core Modules...")
core_modules = [
    "app.core.config",
    "app.core.database",
    "app.core.security",
    "app.core.dependencies",
    "app.core.logging",
]

for mod in core_modules:
    try:
        __import__(mod)
        print(f"  [OK] {mod}")
    except Exception as e:
        print(f"  [FAIL] {mod}: {e}")

# Test db models
print("\n[2] Testing DB Models...")
db_models = [
    "app.db.models.user",
    "app.db.models.patient",
    "app.db.models.asha",
    "app.db.models.hospital",
    "app.db.models.alert",
    "app.db.models.risk",
    "app.db.models.checkin",
    "app.db.models.response",
    "app.db.models.notification",
    "app.db.models.assignment",
    "app.db.models.call",
    "app.db.models.escalation",
    "app.db.models.reminder",
    "app.db.models.medication",
    "app.db.models.prescription",
    "app.db.models.document",
    "app.db.models.consent",
    "app.db.models.audit",
    "app.db.models.chat_message",
    "app.db.models.rag_document",
    "app.db.models.rag_chunk",
]

for mod in db_models:
    try:
        __import__(mod)
        print(f"  [OK] {mod}")
    except Exception as e:
        print(f"  [FAIL] {mod}: {e}")

# Test modules
print("\n[3] Testing Service Modules...")
service_modules = [
    "app.modules.auth.service",
    "app.modules.patients.service",
    "app.modules.asha.service",
    "app.modules.hospitals.service",
    "app.modules.checkins.service",
    "app.modules.risk.service",
    "app.modules.alerts.service",
    "app.modules.escalation.service",
    "app.modules.calls.service",
    "app.modules.ivr.service",
    "app.modules.speech.service",
    "app.modules.extraction.service",
    "app.modules.reminders.service",
    "app.modules.notifications.service",
    "app.modules.maps.service",
    "app.modules.analytics.service",
    "app.modules.reports.service",
    "app.modules.prescriptions.service",
    "app.modules.documents.service",
    "app.modules.chat.service",
    "app.modules.audit.service",
]

for mod in service_modules:
    try:
        __import__(mod)
        print(f"  [OK] {mod}")
    except Exception as e:
        print(f"  [FAIL] {mod}: {e}")

# Test main
print("\n[4] Testing Main App...")
try:
    from app.main import app
    print(f"  [OK] app.main imported")
    print(f"  [OK] {len(app.routes)} routes registered")
except Exception as e:
    print(f"  [FAIL] app.main: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("IMPORT TEST COMPLETE")
print("=" * 80)
