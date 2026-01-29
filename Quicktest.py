#!/usr/bin/env python3
"""
GUVI HCL 2026 Hackathon - Quick Test Script
Tests your honeypot API locally before deployment
"""

import requests
import json
import time
from datetime import datetime

# ============================
# CONFIGURATION
# ============================
API_URL = "http://localhost:5000"
API_KEY = "hackathon-api-key-2026"

COLORS = {
    'GREEN': '\033[92m',
    'RED': '\033[91m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'END': '\033[0m',
    'BOLD': '\033[1m'
}

def print_colored(text, color='END'):
    print(f"{COLORS[color]}{text}{COLORS['END']}")

def print_section(title):
    print("\n" + "="*80)
    print_colored(f"  {title}", 'BOLD')
    print("="*80)

# ============================
# TEST FUNCTIONS
# ============================

def test_1_health_check():
    """Test 1: Health Check"""
    print_section("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            print_colored("✅ PASS - Server is running!", 'GREEN')
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print_colored(f"❌ FAIL - Status: {response.status_code}", 'RED')
            return False
    except requests.exceptions.ConnectionError:
        print_colored("❌ FAIL - Cannot connect to server!", 'RED')
        print_colored("Make sure you run: python app.py", 'YELLOW')
        return False
    except Exception as e:
        print_colored(f"❌ FAIL - Error: {e}", 'RED')
        return False


def test_2_authentication():
    """Test 2: API Authentication"""
    print_section("TEST 2: API Authentication")
    
    results = []
    
    # Test 2.1: No API key
    print("\n2.1 - Testing without API key...")
    response = requests.post(
        f"{API_URL}/analyze",
        headers={"Content-Type": "application/json"},
        json={"sessionId": "test", "message": {"sender": "test", "text": "test"}}
    )
    
    if response.status_code == 401:
        print_colored("  ✅ Correctly rejected (401)", 'GREEN')
        results.append(True)
    else:
        print_colored(f"  ❌ Wrong status: {response.status_code}", 'RED')
        results.append(False)
    
    # Test 2.2: Wrong API key
    print("\n2.2 - Testing with wrong API key...")
    response = requests.post(
        f"{API_URL}/analyze",
        headers={"x-api-key": "wrong-key", "Content-Type": "application/json"},
        json={"sessionId": "test", "message": {"sender": "test", "text": "test"}}
    )
    
    if response.status_code == 401:
        print_colored("  ✅ Correctly rejected (401)", 'GREEN')
        results.append(True)
    else:
        print_colored(f"  ❌ Wrong status: {response.status_code}", 'RED')
        results.append(False)
    
    # Test 2.3: Correct API key
    print("\n2.3 - Testing with correct API key...")
    response = requests.post(
        f"{API_URL}/analyze",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json={"sessionId": "test", "message": {"sender": "test", "text": "test"}}
    )
    
    if response.status_code == 200:
        print_colored("  ✅ Accepted (200)", 'GREEN')
        results.append(True)
    else:
        print_colored(f"  ❌ Wrong status: {response.status_code}", 'RED')
        results.append(False)
    
    return all(results)


def test_3_scam_detection():
    """Test 3: Scam Detection"""
    print_section("TEST 3: Scam Detection")
    
    session_id = f"test-scam-{int(time.time())}"
    
    # Test message with clear scam indicators
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "URGENT! Your bank account 1234567890 will be blocked in 24 hours. Click here: http://fake-bank.tk/verify",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    print("\nScammer message:")
    print_colored(f'  "{payload["message"]["text"]}"', 'YELLOW')
    
    response = requests.post(
        f"{API_URL}/analyze",
        headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
        json=payload
    )
    
    if response.status_code != 200:
        print_colored(f"❌ FAIL - Status: {response.status_code}", 'RED')
        return False
    
    result = response.json()
    
    # Verify scam detection
    if result.get('scamDetected'):
        print_colored("\n✅ Scam correctly detected!", 'GREEN')
    else:
        print_colored("\n❌ Failed to detect scam!", 'RED')
        return False
    
    # Check agent response
    agent_response = result.get('agentResponse', '')
    print(f"\nAgent response:")
    print_colored(f'  "{agent_response}"', 'BLUE')
    
    # Check extracted intelligence
    intel = result.get('extractedIntelligence', {})
    print("\nExtracted intelligence:")
    print(f"  Bank Accounts: {intel.get('bankAccounts', [])}")
    print(f"  UPI IDs: {intel.get('upiIds', [])}")
    print(f"  Phishing Links: {intel.get('phishingLinks', [])}")
    print(f"  Suspicious Keywords: {intel.get('suspiciousKeywords', [])}")
    
    # Verify bank account extraction
    if '1234567890' in intel.get('bankAccounts', []):
        print_colored("  ✅ Bank account extracted!", 'GREEN')
    else:
        print_colored("  ⚠️  Bank account not extracted", 'YELLOW')
    
    # Verify URL extraction
    if any('fake-bank.tk' in url for url in intel.get('phishingLinks', [])):
        print_colored("  ✅ Phishing link extracted!", 'GREEN')
    else:
        print_colored("  ⚠️  Phishing link not extracted", 'YELLOW')
    
    return True


def test_4_multi_turn_conversation():
    """Test 4: Multi-turn Conversation"""
    print_section("TEST 4: Multi-turn Conversation (UPI Scam)")
    
    session_id = f"test-upi-{int(time.time())}"
    conversation_history = []
    
    messages = [
        "Your bank account will be suspended today. Verify immediately.",
        "Share your account number to unlock.",
        "Send ₹1 to scammer@paytm for verification.",
        "Also provide your phone number +919876543210 for confirmation."
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n--- Turn {i} ---")
        print_colored(f"Scammer: {msg}", 'YELLOW')
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": msg,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            },
            "conversationHistory": conversation_history.copy(),
            "metadata": {
                "channel": "WhatsApp",
                "language": "English",
                "locale": "IN"
            }
        }
        
        response = requests.post(
            f"{API_URL}/analyze",
            headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
            json=payload
        )
        
        if response.status_code != 200:
            print_colored(f"❌ FAIL - Status: {response.status_code}", 'RED')
            return False
        
        result = response.json()
        agent_response = result.get('agentResponse', '')
        
        print_colored(f"Agent: {agent_response}", 'BLUE')
        
        # Update conversation history
        conversation_history.append({
            "sender": "scammer",
            "text": msg,
            "timestamp": payload["message"]["timestamp"]
        })
        conversation_history.append({
            "sender": "user",
            "text": agent_response,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        
        # Show extracted intelligence after last message
        if i == len(messages):
            print("\n" + "-"*80)
            print("FINAL EXTRACTED INTELLIGENCE:")
            print("-"*80)
            intel = result.get('extractedIntelligence', {})
            
            print(f"  Bank Accounts: {intel.get('bankAccounts', [])}")
            print(f"  UPI IDs: {intel.get('upiIds', [])}")
            print(f"  Phone Numbers: {intel.get('phoneNumbers', [])}")
            print(f"  Phishing Links: {intel.get('phishingLinks', [])}")
            print(f"  Suspicious Keywords: {intel.get('suspiciousKeywords', [])}")
            
            # Check if UPI was extracted
            if 'scammer@paytm' in intel.get('upiIds', []):
                print_colored("\n✅ UPI ID successfully extracted!", 'GREEN')
            else:
                print_colored("\n⚠️  UPI ID not extracted", 'YELLOW')
            
            # Check agent notes
            notes = result.get('agentNotes', '')
            if notes:
                print(f"\nAgent Notes: {notes}")
    
    print_colored("\n✅ Multi-turn conversation completed!", 'GREEN')
    return True


def test_5_session_management():
    """Test 5: Session Management"""
    print_section("TEST 5: Session Management")
    
    # Get all sessions
    response = requests.get(
        f"{API_URL}/sessions",
        headers={"x-api-key": API_KEY}
    )
    
    if response.status_code != 200:
        print_colored(f"❌ FAIL - Status: {response.status_code}", 'RED')
        return False
    
    data = response.json()
    total_sessions = data.get('total_sessions', 0)
    stats = data.get('statistics', {})
    
    print(f"\nTotal Sessions: {total_sessions}")
    print(f"Scam Detected: {stats.get('scam_detected', 0)}")
    print(f"Finalized: {stats.get('finalized_sessions', 0)}")
    print(f"Total Messages: {stats.get('total_messages', 0)}")
    
    if total_sessions > 0:
        print_colored("\n✅ Session management working!", 'GREEN')
        return True
    else:
        print_colored("\n⚠️  No sessions found (run other tests first)", 'YELLOW')
        return True


# ============================
# MAIN TEST RUNNER
# ============================

def main():
    print("\n")
    print("="*80)
    print_colored("  🧪 GUVI HCL 2026 - HONEYPOT API TEST SUITE", 'BOLD')
    print("="*80)
    print("\n⚡ This will test your honeypot API before hackathon submission")
    print("🌐 Make sure your server is running: python app.py")
    input("\n👉 Press Enter to start testing...")
    
    tests = [
        ("Health Check", test_1_health_check),
        ("API Authentication", test_2_authentication),
        ("Scam Detection", test_3_scam_detection),
        ("Multi-turn Conversation", test_4_multi_turn_conversation),
        ("Session Management", test_5_session_management),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(0.5)  # Small delay between tests
        except KeyboardInterrupt:
            print_colored("\n\n⚠️  Testing interrupted by user", 'YELLOW')
            break
        except Exception as e:
            print_colored(f"\n❌ Test '{test_name}' crashed: {e}", 'RED')
            results.append((test_name, False))
    
    # Summary
    print_section("📊 TEST SUMMARY")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if result:
            print_colored(f"  ✅ PASS - {test_name}", 'GREEN')
            passed += 1
        else:
            print_colored(f"  ❌ FAIL - {test_name}", 'RED')
            failed += 1
    
    total = len(results)
    
    print("\n" + "="*80)
    if failed == 0:
        print_colored(f"  🎉 ALL TESTS PASSED! ({passed}/{total})", 'GREEN')
        print_colored("  Your honeypot is ready for deployment!", 'GREEN')
    elif passed > failed:
        print_colored(f"  ⚠️  MOSTLY PASSED ({passed}/{total})", 'YELLOW')
        print_colored("  Check failed tests above", 'YELLOW')
    else:
        print_colored(f"  ❌ TESTS FAILED ({passed}/{total})", 'RED')
        print_colored("  Fix the issues before deployment", 'RED')
    print("="*80)
    
    # Next steps
    print("\n📋 NEXT STEPS:")
    print("  1. Fix any failed tests")
    print("  2. Deploy to Heroku: heroku create your-app-name")
    print("  3. Test deployed API with same test URLs")
    print("  4. Submit API URL to GUVI platform")
    print("\n")


if __name__ == '__main__':
    main()