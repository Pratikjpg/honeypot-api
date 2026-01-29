"""
Scam Detection Module - IMPROVED VERSION
Better UPI and payment detection
"""

import re
from typing import Tuple, List, Dict


class ScamDetector:
    """Detect scam messages using heuristic rules"""
    
    def __init__(self):
        # High-priority scam keywords (urgency, threats)
        self.critical_keywords = [
            'urgent', 'immediately', 'suspended', 'blocked', 'expire',
            'verify now', 'act now', 'limited time', 'last chance',
            'account locked', 'unauthorized', 'security alert',
            'confirm identity', 'update payment', 'verify account'
        ]
        
        # Medium-priority keywords (common in scams)
        self.warning_keywords = [
            'verify', 'confirm', 'click here', 'link', 'prize', 'won',
            'congratulations', 'selected', 'winner', 'free', 'claim',
            'refund', 'reward', 'bonus', 'offer', 'discount',
            'bank', 'account', 'password', 'otp', 'pin', 'cvv',
            'upi', 'payment', 'transfer', 'credit card', 'debit card',
            'send money', 'send amount', 'pay now', 'unlock'
        ]
        
        # Scam patterns
        self.suspicious_patterns = [
            r'\bhttp[s]?://\S+',  # URLs
            r'\b\d{10,16}\b',  # Account numbers / card numbers
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Card format
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',  # Email with domain
            r'\b[a-zA-Z0-9._-]+@[a-zA-Z0-9]+\b',  # UPI IDs (without domain extension)
            r'\+?\d{10,15}',  # Phone numbers
            r'\b\d{6}\b',  # OTP pattern
            r'₹\s?\d+',  # Indian rupee amounts
            r'Rs\.?\s?\d+',  # Rs amounts
        ]
    
    def detect_scam(
        self,
        message: str,
        conversation_history: List[Dict] = None
    ) -> Tuple[bool, float, List[str]]:
        """
        Detect if a message is a scam
        
        Returns:
            (is_scam, confidence, indicators)
        """
        message_lower = message.lower()
        indicators = []
        score = 0
        
        # Check critical keywords (high weight)
        for keyword in self.critical_keywords:
            if keyword in message_lower:
                score += 25
                indicators.append(f"Critical keyword: '{keyword}'")
        
        # Check warning keywords (medium weight)
        for keyword in self.warning_keywords:
            if keyword in message_lower:
                score += 10
                indicators.append(f"Warning keyword: '{keyword}'")
        
        # Check suspicious patterns
        for pattern in self.suspicious_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                score += 15
                pattern_name = self._pattern_name(pattern)
                indicators.append(f"Suspicious pattern: {pattern_name}")
        
        # Check for urgency indicators
        if self._has_urgency(message_lower):
            score += 20
            indicators.append("Urgency detected")
        
        # Check for threat language
        if self._has_threats(message_lower):
            score += 25
            indicators.append("Threat language detected")
        
        # Check for payment requests (NEW)
        if self._has_payment_request(message_lower):
            score += 20
            indicators.append("Payment request detected")
        
        # Check message length (very short or very long can be suspicious)
        word_count = len(message.split())
        if word_count < 5:
            score += 5
            indicators.append("Very short message")
        elif word_count > 100:
            score += 10
            indicators.append("Very long message")
        
        # Check for multiple exclamation marks
        if message.count('!') >= 3:
            score += 10
            indicators.append("Multiple exclamation marks")
        
        # Normalize score to 0-1 confidence
        confidence = min(score / 100, 1.0)
        
        # Threshold: Consider it a scam if confidence > 0.5
        is_scam = confidence >= 0.5
        
        return is_scam, round(confidence, 2), indicators
    
    def _pattern_name(self, pattern: str) -> str:
        """Get human-readable pattern name"""
        pattern_map = {
            r'\bhttp[s]?://\S+': 'URL',
            r'\b\d{10,16}\b': 'Account/Card number',
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b': 'Card format',
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b': 'Email',
            r'\b[a-zA-Z0-9._-]+@[a-zA-Z0-9]+\b': 'UPI ID',
            r'\+?\d{10,15}': 'Phone number',
            r'\b\d{6}\b': 'OTP pattern',
            r'₹\s?\d+': 'Rupee amount',
            r'Rs\.?\s?\d+': 'Rs amount'
        }
        return pattern_map.get(pattern, 'Unknown pattern')
    
    def _has_urgency(self, message: str) -> bool:
        """Check for urgency indicators"""
        urgency_phrases = [
            'within 24 hours', 'within 48 hours', 'today', 'right now',
            'expires soon', 'limited time', 'hurry', 'quick', 'fast',
            'immediately', 'urgent', 'asap', 'right away'
        ]
        return any(phrase in message for phrase in urgency_phrases)
    
    def _has_threats(self, message: str) -> bool:
        """Check for threatening language"""
        threat_phrases = [
            'will be blocked', 'will be suspended', 'will be closed',
            'will be locked', 'will expire', 'lose access', 'lose account',
            'legal action', 'penalized', 'charged', 'fine'
        ]
        return any(phrase in message for phrase in threat_phrases)
    
    def _has_payment_request(self, message: str) -> bool:
        """Check for payment/money requests (NEW)"""
        payment_phrases = [
            'send money', 'send amount', 'send ₹', 'send rs', 
            'pay now', 'payment to', 'transfer to', 'deposit to',
            'send to upi', 'send to account'
        ]
        return any(phrase in message for phrase in payment_phrases)


# Test the improved detector
if __name__ == '__main__':
    detector = ScamDetector()
    
    # Test cases
    test_messages = [
        "Your bank account will be blocked today. Verify immediately.",
        "Hi, how are you doing today?",
        "URGENT! You have won ₹50,000. Click here to claim: http://fake-site.com",
        "Your OTP is 123456. Do not share with anyone.",
        "Share your account number and UPI ID to receive refund.",
        "Send ₹100 to verify@paytm to unlock account"  # This should now be detected!
    ]
    
    print("\n🧪 Testing IMPROVED Scam Detector\n")
    print("=" * 80)
    
    for msg in test_messages:
        is_scam, confidence, indicators = detector.detect_scam(msg)
        
        print(f"\nMessage: {msg}")
        print(f"Scam: {'YES' if is_scam else 'NO'} (Confidence: {confidence})")
        if indicators:
            print("Indicators:")
            for indicator in indicators:
                print(f"  - {indicator}")
        print("-" * 80)