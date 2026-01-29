"""
Agentic Honey-Pot for Scam Detection & Intelligence Extraction
FIXED VERSION - All critical bugs resolved
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime
import logging
from functools import wraps

from Scam_detector import ScamDetector
from Conversation_agent import ConversationAgent
from Intelligence_extractor import IntelligenceExtractor
from Session_manager import SessionManager
import requests

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
API_KEY = os.getenv('API_KEY', 'hackathon-api-key-2026')
GUVI_CALLBACK_URL = os.getenv('GUVI_CALLBACK_URL', "https://hackathon.guvi.in/api/updateHoneyPotFinalResult")

# Initialize components
scam_detector = ScamDetector()
conversation_agent = ConversationAgent()
intelligence_extractor = IntelligenceExtractor()
session_manager = SessionManager()


def verify_api_key():
    """Verify API key from request headers"""
    provided_key = request.headers.get('x-api-key')
    if not provided_key or provided_key != API_KEY:
        return False
    return True


def validate_request(f):
    """Decorator to validate incoming requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check Content-Type
        if request.content_type != 'application/json':
            return jsonify({'status': 'error', 'message': 'Content-Type must be application/json'}), 400
        
        # Check API key
        if not verify_api_key():
            return jsonify({'status': 'error', 'message': 'Invalid or missing API key'}), 401
        
        # Parse JSON
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400
        
        # Validate required fields
        if 'sessionId' not in data or 'message' not in data:
            return jsonify({'status': 'error', 'message': 'Missing required fields: sessionId, message'}), 400
        
        # Validate message object
        message = data.get('message', {})
        if 'text' not in message or not message['text']:
            return jsonify({'status': 'error', 'message': 'message.text is required and cannot be empty'}), 400
        
        if len(message['text']) > 5000:
            return jsonify({'status': 'error', 'message': 'message.text exceeds 5000 characters'}), 400
        
        return f(*args, **kwargs)
    
    return decorated_function


def send_final_result_to_guvi(session_id, session_data):
    """Send final results to GUVI evaluation endpoint with enhanced logging"""
    try:
        payload = {
            "sessionId": session_id,
            "scamDetected": session_data['scam_detected'],
            "totalMessagesExchanged": session_data['message_count'],
            "extractedIntelligence": session_data['intelligence'],
            "agentNotes": session_data['agent_notes']
        }
        
        logger.info(f"📤 Preparing GUVI callback for session {session_id}")
        logger.info(f"   Scam Detected: {payload['scamDetected']}")
        logger.info(f"   Total Messages: {payload['totalMessagesExchanged']}")
        logger.info(f"   Bank Accounts: {len(payload['extractedIntelligence'].get('bankAccounts', []))}")
        logger.info(f"   UPI IDs: {len(payload['extractedIntelligence'].get('upiIds', []))}")
        logger.info(f"   Phishing Links: {len(payload['extractedIntelligence'].get('phishingLinks', []))}")
        
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            logger.info(f"✅ GUVI callback SUCCESS for {session_id}")
            return True
        else:
            logger.error(f"❌ GUVI callback FAILED: Status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"❌ GUVI callback TIMEOUT for {session_id}")
        return False
    except Exception as e:
        logger.error(f"❌ GUVI callback ERROR: {e}", exc_info=True)
        return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Agentic Honey-Pot API',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/analyze', methods=['POST'])
@validate_request
def analyze_message():
    """
    Main API endpoint for scam detection and engagement
    FIXED: Better conversation history handling, proper finalization logic
    """
    
    try:
        # Parse request (validation done by decorator)
        data = request.get_json()
        
        # Extract fields
        session_id = data.get('sessionId')
        message = data.get('message', {})
        conversation_history = data.get('conversationHistory', [])
        metadata = data.get('metadata', {})
        
        # Get message text
        message_text = message.get('text', '').strip()
        sender = message.get('sender', 'scammer')
        message_timestamp = message.get('timestamp', datetime.utcnow().isoformat())
        
        logger.info(f"📨 Session {session_id}: {message_text[:50]}...")
        
        # Get or create session
        session_data = session_manager.get_or_create_session(session_id)
        
        # Update message count
        session_data['message_count'] += 1
        session_data['last_activity'] = datetime.utcnow().isoformat()
        
        # Build complete conversation history
        full_conversation = conversation_history.copy() if conversation_history else []
        
        # Add current message to tracking
        full_conversation.append({
            'sender': sender,
            'text': message_text,
            'timestamp': message_timestamp
        })
        
        # Also add to session conversation for state tracking
        session_data['conversation'].append({
            'sender': sender,
            'text': message_text,
            'timestamp': message_timestamp
        })
        
        # Detect scam (only on first 3 messages to avoid re-detection)
        if session_data['message_count'] <= 3 and not session_data['scam_detected']:
            is_scam, confidence, scam_indicators = scam_detector.detect_scam(
                message_text,
                conversation_history
            )
            
            if is_scam:
                session_data['scam_detected'] = True
                session_data['scam_confidence'] = confidence
                session_data['scam_indicators'] = scam_indicators
                logger.info(f"🚨 SCAM DETECTED in session {session_id} (confidence: {confidence})")
        
        # Extract intelligence from current message
        intelligence = intelligence_extractor.extract_from_text(message_text)
        
        # Merge intelligence into session
        for key in ['bankAccounts', 'upiIds', 'phishingLinks', 'phoneNumbers', 'suspiciousKeywords']:
            session_data['intelligence'][key].extend(intelligence.get(key, []))
        
        # Deduplicate intelligence
        for key in session_data['intelligence']:
            session_data['intelligence'][key] = list(set(session_data['intelligence'][key]))
        
        # Generate agent response using full conversation history
        agent_response = conversation_agent.generate_response(
            message_text,
            full_conversation,
            session_data['scam_detected'],
            session_data['message_count']
        )
        
        # Add agent response to session conversation
        session_data['conversation'].append({
            'sender': 'user',
            'text': agent_response,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Update agent notes
        if session_data['scam_detected']:
            session_data['agent_notes'] = conversation_agent.generate_agent_notes(
                session_data['scam_indicators'],
                session_data['intelligence']
            )
        
        # Calculate engagement duration
        start_time = datetime.fromisoformat(session_data['start_time'].replace('Z', '+00:00'))
        current_time = datetime.utcnow()
        engagement_seconds = int((current_time - start_time).total_seconds())
        
        # Prepare response
        response_data = {
            'status': 'success',
            'scamDetected': session_data['scam_detected'],
            'agentResponse': agent_response,
            'engagementMetrics': {
                'engagementDurationSeconds': engagement_seconds,
                'totalMessagesExchanged': session_data['message_count']
            },
            'extractedIntelligence': session_data['intelligence'],
            'agentNotes': session_data['agent_notes']
        }
        
        # Save session
        session_manager.update_session(session_id, session_data)
        
        # FIXED: Proper finalization logic with correct parentheses
        should_finalize = (
            session_data['scam_detected'] and (
                session_data['message_count'] >= 8 or
                len(session_data['intelligence']['bankAccounts']) > 0 or
                len(session_data['intelligence']['upiIds']) > 0 or
                len(session_data['intelligence']['phishingLinks']) > 0
            )
        )
        
        if should_finalize and not session_data.get('finalized', False):
            logger.info(f"🎯 Finalizing session {session_id}")
            success = send_final_result_to_guvi(session_id, session_data)
            
            if success:
                session_data['finalized'] = True
                session_manager.update_session(session_id, session_data)
                logger.info(f"✅ Session {session_id} finalized")
        
        logger.info(f"✅ Response sent for session {session_id}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500


@app.route('/session/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session details"""
    if not verify_api_key():
        return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401
    
    session_data = session_manager.get_session(session_id)
    
    if not session_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    
    return jsonify({
        'status': 'success',
        'session': session_data
    }), 200


@app.route('/sessions', methods=['GET'])
def list_sessions():
    """List all active sessions"""
    if not verify_api_key():
        return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401
    
    sessions = session_manager.list_sessions()
    stats = session_manager.get_statistics()
    
    return jsonify({
        'status': 'success',
        'total_sessions': len(sessions),
        'statistics': stats,
        'sessions': sessions
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info("=" * 80)
    logger.info("🚀 Starting Agentic Honey-Pot API [FIXED VERSION]")
    logger.info("=" * 80)
    logger.info(f"🔑 API Key configured: {'✅' if API_KEY != 'hackathon-api-key-2026' else '⚠️'}")
    logger.info(f"📡 GUVI Callback: {GUVI_CALLBACK_URL}")
    logger.info(f"🌐 Server: http://0.0.0.0:{port}")
    logger.info("=" * 80)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
