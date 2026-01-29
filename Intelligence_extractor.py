"""
Intelligence Extraction Module - FIXED VERSION
Fixed regex group handling and UPI validation
"""

import re
from typing import Dict, List


class IntelligenceExtractor:
    """Extract intelligence from scammer messages"""
    
    def __init__(self):
        # Regex patterns for different types of intelligence
        self.patterns = {
            'bank_account': [
                r'\b\d{9,18}\b',
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                r'account[:\s]+(\d+)',
                r'A/C[:\s]+(\d+)',
                r'acc[:\s]+(\d+)',
            ],
            'upi_id': [
                r'\b[a-zA-Z0-9._-]+@[a-zA-Z0-9]+\b',
                r'\b\w+@paytm\b',
                r'\b\w+@ybl\b',
                r'\b\w+@oksbi\b',
                r'\b\w+@okaxis\b',
                r'\b\w+@upi\b',
                r'\b\w+@gpay\b',
                r'\b\w+@phonepe\b',
                r'\b\w+@sbi\b',
                r'\b\w+@hdfc\b',
                r'\b\w+@icici\b',
            ],
            'phishing_link': [
                r'http[s]?://[^\s]+',
                r'www\.[^\s]+',
                r'\b\w+\.(tk|ml|ga|cf|gq|club|xyz)\b',
            ],
            'phone_number': [
                r'\+?\d{10,15}',
                r'\b\d{10}\b',
                r'\b91\d{10}\b',
            ],
        }
        
        # Suspicious keywords
        self.suspicious_keywords = [
            'urgent', 'immediately', 'verify', 'confirm', 'suspended',
            'blocked', 'expires', 'act now', 'click here', 'limited time',
            'winner', 'prize', 'congratulations', 'won', 'claim',
            'refund', 'reward', 'bonus', 'free', 'offer', 'update',
            'security alert', 'authorize', 'approve', 'confirm identity'
        ]
    
    def _is_valid_upi(self, text: str) -> bool:
        """Validate UPI ID format"""
        if '@' not in text:
            return False
        
        valid_banks = [
            'paytm', 'ybl', 'oksbi', 'okaxis', 'upi', 'gpay', 'phonepe',
            'hdfc', 'icici', 'sbi', 'axis', 'airtel', 'aubank'
        ]
        
        try:
            parts = text.split('@')
            if len(parts) != 2:
                return False
            
            username, bank = parts
            
            # Validate username
            if not re.match(r'^[a-zA-Z0-9._-]+$', username):
                return False
            
            if len(username) < 2:
                return False
            
            # Validate bank
            if bank.lower() in valid_banks:
                return True
            
            if re.match(r'^[a-zA-Z0-9]+$', bank) and len(bank) >= 3:
                return True
            
            return False
        except:
            return False
    
    def _extract_with_pattern(self, pattern: str, text: str) -> List[str]:
        """Extract with proper handling of regex groups"""
        matches = re.findall(pattern, text, re.IGNORECASE)
        extracted = []
        
        for match in matches:
            if isinstance(match, tuple):
                # Pattern has capturing groups
                extracted.extend([m.strip() for m in match if m and m.strip()])
            else:
                # No groups - use full match
                if match and str(match).strip():
                    extracted.append(str(match).strip())
        
        return extracted
    
    def extract_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract all intelligence from a text message"""
        result = {
            'bankAccounts': [],
            'upiIds': [],
            'phishingLinks': [],
            'phoneNumbers': [],
            'suspiciousKeywords': []
        }
        
        # Extract bank accounts
        for pattern in self.patterns['bank_account']:
            matches = self._extract_with_pattern(pattern, text)
            result['bankAccounts'].extend(matches)
        
        # Extract UPI IDs
        for pattern in self.patterns['upi_id']:
            matches = self._extract_with_pattern(pattern, text)
            valid_upi = [m for m in matches if self._is_valid_upi(m)]
            result['upiIds'].extend(valid_upi)
        
        # Extract phishing links
        for pattern in self.patterns['phishing_link']:
            matches = self._extract_with_pattern(pattern, text)
            result['phishingLinks'].extend(matches)
        
        # Extract phone numbers
        for pattern in self.patterns['phone_number']:
            matches = self._extract_with_pattern(pattern, text)
            valid_phones = [
                m for m in matches 
                if 10 <= len(re.sub(r'\D', '', m)) <= 15
            ]
            result['phoneNumbers'].extend(valid_phones)
        
        # Extract suspicious keywords
        text_lower = text.lower()
        for keyword in self.suspicious_keywords:
            if keyword in text_lower:
                result['suspiciousKeywords'].append(keyword)
        
        # Deduplicate
        for key in result:
            result[key] = list(dict.fromkeys(result[key]))
        
        # Clean up results
        result = self._clean_results(result)
        
        return result
    
    def _clean_results(self, result: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Clean and validate extracted data"""
        
        # Remove invalid bank accounts
        result['bankAccounts'] = [
            acc for acc in result['bankAccounts']
            if 9 <= len(re.sub(r'\D', '', acc)) <= 18
        ]
        
        # Remove invalid UPI IDs
        result['upiIds'] = [
            upi for upi in result['upiIds']
            if self._is_valid_upi(upi)
        ]
        
        # Validate URLs
        result['phishingLinks'] = [
            link for link in result['phishingLinks']
            if 5 <= len(link) <= 500 and (
                link.startswith('http://') or 
                link.startswith('https://') or 
                link.startswith('www.')
            )
        ]
        
        # Remove invalid phone numbers
        result['phoneNumbers'] = [
            phone for phone in result['phoneNumbers']
            if 10 <= len(re.sub(r'\D', '', phone)) <= 15
        ]
        
        # Remove duplicate suspicious keywords
        result['suspiciousKeywords'] = list(dict.fromkeys(result['suspiciousKeywords']))
        
        return result
    
    def extract_from_conversation(self, conversation: List[Dict]) -> Dict[str, List[str]]:
        """Extract intelligence from entire conversation history"""
        combined_result = {
            'bankAccounts': [],
            'upiIds': [],
            'phishingLinks': [],
            'phoneNumbers': [],
            'suspiciousKeywords': []
        }
        
        # Extract from each message
        for message in conversation:
            text = message.get('text', '')
            if not text:
                continue
            
            extraction = self.extract_from_text(text)
            
            # Merge results
            for key in combined_result:
                combined_result[key].extend(extraction[key])
        
        # Deduplicate final results
        for key in combined_result:
            combined_result[key] = list(dict.fromkeys(combined_result[key]))
        
        return combined_result
