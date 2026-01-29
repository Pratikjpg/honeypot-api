"""
Test Script for Agentic Honey-Pot
Tests all components locally
"""

import requests
import json
import time

# Configuration
API_URL = "http://localhost:5000"
API_KEY = "hackathon-api-key-2026"  # Change this to match your .env

def test_health():
    """Test health endpoint"""
    print("\n🔍 Testing Health Endpoint...")
    response = requests.get(f"{API_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_scam_detection():
    """Test full scam detection flow"""
    print("\n🚨 Testing Scam Detection Flow...")
    
    session_id = f"test-session-{int(time.time())}"
    
    # Message 1: Initial scam message
    print("\n--- Message 1 ---")
    payload1 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "URGENT! Your bank account will be blocked in 24 hours. Verify immediately at http://fake-bank.tk/verify",
            "timestamp": "2026-01-27T10:00:00Z"
        },
        "conversationHistory": [],
        "metadata": {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    }
    
    response1 = requests.post(
        f"{API_URL}/analyze",
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        json=payload1
    )
    
    print(f"Status: {response1.status_code}")
    result1 = response1.json()
    print(f"Scam Detected: {result1.get('scamDetected')}")
    print(f"Agent Response: {result1.get('agentResponse')}")
    print(f"Extracted Intelligence: {json.dumps(result1.get('extractedIntelligence'), indent=2)}")
    
    if not result1.get('scamDetected'):
        print("❌ Failed to detect scam!")
        return False
    
    # Message 2: Scammer asks for account number
    print("\n--- Message 2 ---")
    payload2 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Share your account number: 9876543210 to unlock your account.",
            "timestamp": "2026-01-27T10:02:00Z"
        },
        "conversationHistory": [
            {
                "sender": "scammer",
                "text": payload1["message"]["text"],
                "timestamp": "2026-01-27T10:00:00Z"
            },
            {
                "sender": "user",
                "text": result1.get('agentResponse'),
                "timestamp": "2026-01-27T10:01:00Z"
            }
        ],
        "metadata": payload1["metadata"]
    }
    
    response2 = requests.post(
        f"{API_URL}/analyze",
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        json=payload2
    )
    
    result2 = response2.json()
    print(f"Status: {response2.status_code}")
    print(f"Agent Response: {result2.get('agentResponse')}")
    print(f"Extracted Intelligence: {json.dumps(result2.get('extractedIntelligence'), indent=2)}")
    
    # Check if bank account was extracted
    bank_accounts = result2.get('extractedIntelligence', {}).get('bankAccounts', [])
    if '9876543210' in bank_accounts:
        print("✅ Successfully extracted bank account!")
    else:
        print("⚠️ Bank account extraction may need improvement")
    
    # Message 3: Scammer provides UPI ID
    print("\n--- Message 3 ---")
    payload3 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": "Send ₹100 to scammer@paytm to verify your account.",
            "timestamp": "2026-01-27T10:04:00Z"
        },
        "conversationHistory": payload2["conversationHistory"] + [
            {
                "sender": "scammer",
                "text": payload2["message"]["text"],
                "timestamp": "2026-01-27T10:02:00Z"
            },
            {
                "sender": "user",
                "text": result2.get('agentResponse'),
                "timestamp": "2026-01-27T10:03:00Z"
            }
        ],
        "metadata": payload1["metadata"]
    }
    
    response3 = requests.post(
        f"{API_URL}/analyze",
        headers={
            "x-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        json=payload3
    )
    
    result3 = response3.json()
    print(f"Status: {response3.status_code}")
    print(f"Agent Response: {result3.get('agentResponse')}")
    print(f"Extracted Intelligence: {json.dumps(result3.get('extractedIntelligence'), indent=2)}")
    
    # Check if UPI was extracted
    upi_ids = result3.get('extractedIntelligence', {}).get('upiIds', [])
    if 'scammer@paytm' in upi_ids:
        print("✅ Successfully extracted UPI ID!")
    else:
        print("⚠️ UPI extraction may need improvement")
    
    return True

def test_authentication():
    """Test API authentication"""
    print("\n🔐 Testing Authentication...")
    
    # Test without API key
    print("\nTest 1: No API key")
    response = requests.post(f"{API_URL}/analyze", json={})
    print(f"Status: {response.status_code} (Expected: 401)")
    
    # Test with wrong API key
    print("\nTest 2: Wrong API key")
    response = requests.post(
        f"{API_URL}/analyze",
        headers={"x-api-key": "wrong-key"},
        json={}
    )
    print(f"Status: {response.status_code} (Expected: 401)")
    
    # Test with correct API key
    print("\nTest 3: Correct API key")
    response = requests.post(
        f"{API_URL}/analyze",
        headers={"x-api-key": API_KEY},
        json={"sessionId": "test", "message": {"sender": "test", "text": "test"}}
    )
    print(f"Status: {response.status_code} (Expected: 200)")
    
    return True

def main():
    """Run all tests"""
    print("=" * 80)
    print("🧪 AGENTIC HONEY-POT TESTING SUITE")
    print("=" * 80)
    
    tests = [
        ("Health Check", test_health),
        ("Authentication", test_authentication),
        ("Scam Detection Flow", test_scam_detection),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'=' * 80}")
            print(f"Running: {test_name}")
            print('=' * 80)
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "=" * 80)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80)

if __name__ == '__main__':
    print("\n⚠️  Make sure the API is running first!")
    print("Run: python honeypot_app.py")
    input("\nPress Enter when ready...")
    
    main()