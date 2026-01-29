"""
Conversation Agent Module
Generates believable victim responses
"""

import random
from typing import List, Dict


class ConversationAgent:
    """Generate human-like responses to engage scammers"""
    
    def __init__(self):
        # Response templates by conversation stage
        self.initial_responses = [
            "What? I don't understand. What's happening?",
            "Is this real? I'm worried now.",
            "Oh no! What should I do?",
            "I'm scared. Can you help me?",
            "This is urgent? What do I need to do?",
            "I didn't know about this. Please tell me more.",
        ]
        
        self.curious_responses = [
            "Why is this happening?",
            "How did this happen?",
            "What went wrong?",
            "I don't remember doing anything wrong.",
            "Can you explain this to me?",
            "I'm confused. What exactly is the problem?",
        ]
        
        self.compliance_responses = [
            "Okay, what information do you need from me?",
            "I want to fix this. What should I send you?",
            "Please help me. What details do you need?",
            "I'll do whatever is needed. What do you want?",
            "Tell me exactly what I need to share.",
            "I'm ready to cooperate. What's the next step?",
        ]
        
        self.hesitant_responses = [
            "Are you sure this is safe?",
            "Should I really share that information?",
            "Is this the official way to do this?",
            "Can I verify this first?",
            "This seems unusual. Is everything okay?",
            "I want to make sure this is legitimate.",
        ]
        
        self.information_seeking = [
            "What account number should I use?",
            "Which UPI ID exactly?",
            "What's the link I should click?",
            "Where should I send the payment?",
            "What amount should I transfer?",
            "What OTP are you talking about?",
        ]
        
        self.stalling_responses = [
            "Let me find that information. One moment.",
            "I'm checking my records. Give me a second.",
            "I need to look for that. Can you wait?",
            "Let me grab my phone/documents.",
            "I'm trying to remember. Hold on.",
            "I'm not near my computer right now.",
        ]
    
    def generate_response(
        self,
        scammer_message: str,
        conversation_history: List[Dict],
        scam_detected: bool,
        message_count: int
    ) -> str:
        """
        Generate appropriate response based on conversation context
        """
        if not scam_detected:
            # If scam not yet detected, be neutral
            return random.choice([
                "I'm not sure I understand.",
                "Can you explain what this is about?",
                "Who is this?",
            ])
        
        scammer_message_lower = scammer_message.lower()
        
        # Stage 1: Initial shock (messages 1-2)
        if message_count <= 2:
            return random.choice(self.initial_responses)
        
        # Stage 2: Curiosity (messages 3-4)
        elif message_count <= 4:
            return random.choice(self.curious_responses)
        
        # Stage 3: Compliance (messages 5-7)
        elif message_count <= 7:
            # Check if scammer is asking for specific information
            if any(keyword in scammer_message_lower for keyword in ['account', 'number', 'upi', 'otp', 'password']):
                # Mix compliance with information seeking
                if random.random() > 0.5:
                    return random.choice(self.information_seeking)
                else:
                    return random.choice(self.compliance_responses)
            else:
                return random.choice(self.compliance_responses)
        
        # Stage 4: Hesitation (messages 8-10)
        elif message_count <= 10:
            if random.random() > 0.6:
                return random.choice(self.hesitant_responses)
            else:
                return random.choice(self.information_seeking)
        
        # Stage 5: Stalling or re-engaging (messages 11+)
        else:
            if random.random() > 0.5:
                return random.choice(self.stalling_responses)
            else:
                return random.choice(self.information_seeking)
    
    def generate_agent_notes(
        self,
        scam_indicators: List[str],
        intelligence: Dict
    ) -> str:
        """
        Generate summary notes about the scammer's behavior
        """
        notes = []
        
        # Analyze indicators
        if any('urgent' in indicator.lower() for indicator in scam_indicators):
            notes.append("Used urgency tactics")
        
        if any('threat' in indicator.lower() for indicator in scam_indicators):
            notes.append("Made threats about account suspension/blocking")
        
        if any('url' in indicator.lower() or 'link' in indicator.lower() for indicator in scam_indicators):
            notes.append("Included suspicious links")
        
        # Analyze extracted intelligence
        if intelligence.get('bankAccounts'):
            notes.append("Requested bank account information")
        
        if intelligence.get('upiIds'):
            notes.append("Attempted UPI payment redirection")
        
        if intelligence.get('phishingLinks'):
            notes.append("Shared phishing URLs")
        
        if intelligence.get('phoneNumbers'):
            notes.append("Shared contact numbers")
        
        # Default note
        if not notes:
            notes.append("Standard scam pattern detected")
        
        return "; ".join(notes)


# Test the agent
if __name__ == '__main__':
    agent = ConversationAgent()
    
    print("\n🤖 Testing Conversation Agent\n")
    print("=" * 80)
    
    # Simulate conversation
    test_messages = [
        "Your account will be blocked!",
        "Share your account number immediately.",
        "We need your UPI ID to process refund.",
        "Click this link: http://fake-bank.com"
    ]
    
    conversation = []
    
    for i, msg in enumerate(test_messages, 1):
        response = agent.generate_response(
            scammer_message=msg,
            conversation_history=conversation,
            scam_detected=True,
            message_count=i
        )
        
        print(f"\nTurn {i}:")
        print(f"Scammer: {msg}")
        print(f"Agent: {response}")
        print("-" * 80)
        
        conversation.append({'sender': 'scammer', 'text': msg})
        conversation.append({'sender': 'user', 'text': response})
    
    # Test agent notes
    print("\n📝 Agent Notes:")
    indicators = [
        "Critical keyword: 'urgent'",
        "Threat language detected",
        "Suspicious pattern: URL"
    ]
    intelligence = {
        'bankAccounts': ['1234567890'],
        'upiIds': ['scammer@paytm'],
        'phishingLinks': ['http://fake-bank.com']
    }
    
    notes = agent.generate_agent_notes(indicators, intelligence)
    print(notes)