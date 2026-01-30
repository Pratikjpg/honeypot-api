"""
Agentic Honey-Pot API - GUVI HCL 2026 Hackathon
CORRECTED VERSION - Matches all professor requirements
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import requests
from typing import Dict, Optional

# Import your modules
from Scam_detector import ScamDetector
from Intelligence_extractor import IntelligenceExtractor
from Conversation_agent import ConversationAgent
from Session_manager import SessionManager

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize components
scam_detector = ScamDetector()
intelligence_extractor = IntelligenceExtractor()
conversation_agent = ConversationAgent()
session_manager = SessionManager()

# Configuration
API_KEY = os.environ.get('API_KEY', 'hackathon-api-key-2026')
GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

# Conversation finalization thresholds
MAX_MESSAGES = 15  # Finalize after 15 messages
MIN_MESSAGES_FOR_FINALIZATION = 5  # Minimum messages before finalizing
CONFIDENCE_THRESHOLD_FOR_FINALIZATION = 0.8  # High confidence to finalize


def check_api_key():
    """Validate API key from request headers"""
    api_key = request.headers.get('x-api-key')
    if not api_key or api_key != API_KEY:
        return False
    return True


def should_finalize_conversation(session: Dict) -> bool:
    """
    Determine if conversation should be finalized
    Based on message count and intelligence gathered
    """
    message_count = session['message_count']
    scam_detected = session['scam_detected']
    intelligence = session['intelligence']
    
    # Don't finalize if scam not detected
    if not scam_detected:
        return False
    
    # Don't finalize too early
    if message_count < MIN_MESSAGES_FOR_FINALIZATION:
        return False
    
    # Finalize if we've gathered substantial intelligence
    has_substantial_intel = (
        len(intelligence.get('bankAccounts', [])) > 0 or
        len(intelligence.get('upiIds', [])) > 0 or
        len(intelligence.get('phishingLinks', [])) > 0 or
        len(intelligence.get('phoneNumbers', [])) > 0
    )
    
    # Finalize if:
    # 1. Reached max messages OR
    # 2. Have substantial intelligence and enough messages
    if message_count >= MAX_MESSAGES:
        return True
    
    if has_substantial_intel and message_count >= MIN_MESSAGES_FOR_FINALIZATION + 3:
        return True
    
    # High confidence scam with good intel
    if session['scam_confidence'] >= CONFIDENCE_THRESHOLD_FOR_FINALIZATION and has_substantial_intel:
        return True
    
    return False


def send_final_result_to_guvi(session_id: str, session: Dict) -> bool:
    """
    Send final extracted intelligence to GUVI evaluation endpoint
    This is MANDATORY per Section 12 of requirements
    """
    try:
        payload = {
            "sessionId": session_id,
            "scamDetected": session['scam_detected'],
            "totalMessagesExchanged": session['message_count'],
            "extractedIntelligence": session['intelligence'],
            "agentNotes": session['agent_notes']
        }
        
        print(f"\n📤 Sending final result to GUVI for session: {session_id}")
        print(f"Payload: {payload}")
        
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"✅ GUVI callback response: {response.status_code}")
        
        if response.status_code == 200:
            return True
        else:
            print(f"⚠️ GUVI callback failed with status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending to GUVI: {e}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Agentic Honey-Pot API',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': '2.0-corrected'
    }), 200


@app.route('/analyze', methods=['POST'])
def analyze_message():
    """
    Main endpoint to analyze incoming messages
    CORRECTED VERSION - Matches professor's requirements exactly
    """
    # Check API authentication
    if not check_api_key():
        return jsonify({
            'status': 'error',
            'message': 'Unauthorized - Invalid or missing API key'
        }), 401
    
    try:
        # Parse request
        data = request.get_json()
        
        # Extract required fields
        session_id = data.get('sessionId')
        message = data.get('message', {})
        conversation_history = data.get('conversationHistory', [])
        metadata = data.get('metadata', {})
        
        # Validate required fields
        if not session_id or not message:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: sessionId and message'
            }), 400
        
        # Get or create session
        session = session_manager.get_or_create_session(session_id)
        
        # Extract message details
        sender = message.get('sender', 'unknown')
        text = message.get('text', '')
        timestamp = message.get('timestamp', datetime.utcnow().isoformat() + 'Z')
        
        # Only process scammer messages
        if sender != 'scammer':
            return jsonify({
                'status': 'success',
                'reply': 'Message acknowledged'
            }), 200
        
        # Increment message count
        session['message_count'] += 1
        session['last_activity'] = datetime.utcnow().isoformat()
        
        # Detect scam intent
        is_scam, confidence, indicators = scam_detector.detect_scam(
            message=text,
            conversation_history=conversation_history
        )
        
        # Update session with scam detection results
        if is_scam and not session['scam_detected']:
            session['scam_detected'] = True
            session['scam_confidence'] = confidence
            session['scam_indicators'] = indicators
        elif is_scam:
            # Update confidence if higher
            if confidence > session['scam_confidence']:
                session['scam_confidence'] = confidence
            # Add new indicators
            session['scam_indicators'].extend(indicators)
            session['scam_indicators'] = list(set(session['scam_indicators']))
        
        # Extract intelligence from this message
        message_intelligence = intelligence_extractor.extract_from_text(text)
        
        # Merge with session intelligence
        for key in session['intelligence']:
            session['intelligence'][key].extend(message_intelligence[key])
            # Deduplicate
            session['intelligence'][key] = list(dict.fromkeys(session['intelligence'][key]))
        
        # Generate agent response
        agent_response = conversation_agent.generate_response(
            scammer_message=text,
            conversation_history=conversation_history,
            scam_detected=session['scam_detected'],
            message_count=session['message_count']
        )
        
        # Generate agent notes
        agent_notes = conversation_agent.generate_agent_notes(
            scam_indicators=session['scam_indicators'],
            intelligence=session['intelligence']
        )
        session['agent_notes'] = agent_notes
        
        # Add to conversation history
        session['conversation'].append({
            'sender': sender,
            'text': text,
            'timestamp': timestamp
        })
        session['conversation'].append({
            'sender': 'user',
            'text': agent_response,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        # Save updated session
        session_manager.update_session(session_id, session)
        
        # Check if conversation should be finalized
        should_finalize = should_finalize_conversation(session)
        
        if should_finalize and not session.get('finalized', False):
            print(f"\n🎯 Finalizing conversation for session: {session_id}")
            
            # Mark as finalized
            session['finalized'] = True
            session_manager.update_session(session_id, session)
            
            # Send final result to GUVI (MANDATORY)
            send_final_result_to_guvi(session_id, session)
        
        # Return response in CORRECT FORMAT (Section 8)
        return jsonify({
            'status': 'success',
            'reply': agent_response
        }), 200
        
    except Exception as e:
        print(f"❌ Error processing message: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500


@app.route('/sessions', methods=['GET'])
def list_sessions():
    """Get all active sessions (for monitoring)"""
    if not check_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        sessions = session_manager.list_sessions()
        stats = session_manager.get_statistics()
        
        return jsonify({
            'total_sessions': len(sessions),
            'sessions': sessions,
            'statistics': stats
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get detailed session information"""
    if not check_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        session = session_manager.get_session(session_id)
        if session:
            return jsonify(session), 200
        else:
            return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/session/<session_id>/finalize', methods=['POST'])
def finalize_session_manually(session_id):
    """Manually finalize a session and send to GUVI"""
    if not check_api_key():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        session = session_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        if session.get('finalized', False):
            return jsonify({'message': 'Session already finalized'}), 200
        
        # Mark as finalized
        session['finalized'] = True
        session_manager.update_session(session_id, session)
        
        # Send to GUVI
        success = send_final_result_to_guvi(session_id, session)
        
        return jsonify({
            'message': 'Session finalized',
            'guvi_callback_success': success
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    """Serve dashboard"""
    try:
        with open('index.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({
            'service': 'Agentic Honey-Pot API',
            'status': 'running',
            'endpoints': {
                'health': '/health',
                'analyze': '/analyze',
                'sessions': '/sessions',
                'session_detail': '/session/<id>',
                'finalize': '/session/<id>/finalize'
            }
        }), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🍯 AGENTIC HONEY-POT API - CORRECTED VERSION           ║
    ║                                                           ║
    ║   ✅ Scam Detection Engine                               ║
    ║   ✅ Multi-turn AI Agent                                 ║
    ║   ✅ Intelligence Extraction                             ║
    ║   ✅ GUVI Callback (Section 12) - IMPLEMENTED            ║
    ║   ✅ Correct Response Format (Section 8)                 ║
    ║   ✅ Auto Conversation Finalization                      ║
    ║                                                           ║
    ║   Port: {port}                                              ║
    ║   API Key Required: Yes                                  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=False)
