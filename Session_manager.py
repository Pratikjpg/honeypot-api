"""
Session Manager Module
Manage conversation sessions and state
"""

from datetime import datetime
from typing import Dict, Optional, List
import json


class SessionManager:
    """Manage conversation sessions"""
    
    def __init__(self):
        self.sessions = {}
    
    def get_or_create_session(self, session_id: str) -> Dict:
        """
        Get existing session or create new one
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'session_id': session_id,
                'start_time': datetime.utcnow().isoformat(),
                'last_activity': datetime.utcnow().isoformat(),
                'message_count': 0,
                'scam_detected': False,
                'scam_confidence': 0.0,
                'scam_indicators': [],
                'conversation': [],
                'intelligence': {
                    'bankAccounts': [],
                    'upiIds': [],
                    'phishingLinks': [],
                    'phoneNumbers': [],
                    'suspiciousKeywords': []
                },
                'agent_notes': '',
                'finalized': False
            }
        
        return self.sessions[session_id]
    
    def update_session(self, session_id: str, session_data: Dict) -> None:
        """Update session data"""
        self.sessions[session_id] = session_data
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> List[Dict]:
        """List all sessions (summary)"""
        summaries = []
        for session_id, session_data in self.sessions.items():
            summaries.append({
                'session_id': session_id,
                'start_time': session_data['start_time'],
                'message_count': session_data['message_count'],
                'scam_detected': session_data['scam_detected'],
                'finalized': session_data.get('finalized', False)
            })
        return summaries
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up sessions older than max_age_hours
        Returns number of sessions deleted
        """
        from datetime import timedelta
        
        current_time = datetime.utcnow()
        to_delete = []
        
        for session_id, session_data in self.sessions.items():
            start_time = datetime.fromisoformat(session_data['start_time'].replace('Z', '+00:00'))
            age = current_time - start_time
            
            if age > timedelta(hours=max_age_hours):
                to_delete.append(session_id)
        
        for session_id in to_delete:
            del self.sessions[session_id]
        
        return len(to_delete)
    
    def export_session(self, session_id: str) -> Optional[str]:
        """Export session as JSON string"""
        session = self.get_session(session_id)
        if session:
            return json.dumps(session, indent=2)
        return None
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        total_sessions = len(self.sessions)
        scam_sessions = sum(1 for s in self.sessions.values() if s['scam_detected'])
        finalized_sessions = sum(1 for s in self.sessions.values() if s.get('finalized', False))
        
        total_messages = sum(s['message_count'] for s in self.sessions.values())
        
        return {
            'total_sessions': total_sessions,
            'scam_detected': scam_sessions,
            'finalized_sessions': finalized_sessions,
            'total_messages': total_messages,
            'avg_messages_per_session': round(total_messages / total_sessions, 2) if total_sessions > 0 else 0
        }


# Test the session manager
if __name__ == '__main__':
    manager = SessionManager()
    
    print("\n📊 Testing Session Manager\n")
    print("=" * 80)
    
    # Create some test sessions
    session1 = manager.get_or_create_session('test-session-1')
    session1['message_count'] = 5
    session1['scam_detected'] = True
    manager.update_session('test-session-1', session1)
    
    session2 = manager.get_or_create_session('test-session-2')
    session2['message_count'] = 3
    session2['scam_detected'] = False
    manager.update_session('test-session-2', session2)
    
    # List sessions
    print("\nActive Sessions:")
    for session in manager.list_sessions():
        print(f"  - {session['session_id']}: {session['message_count']} messages, "
              f"Scam: {session['scam_detected']}")
    
    # Get statistics
    print("\nStatistics:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Export session
    print("\nExported Session 1:")
    exported = manager.export_session('test-session-1')
    print(exported)