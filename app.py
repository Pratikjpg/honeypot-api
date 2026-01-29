"""
Agentic Honey-Pot for Scam Detection & Intelligence Extraction
GUVI HCL 2026 Hackathon - Problem Statement 2
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
import logging
import sys
from functools import wraps
import requests

# Import custom modules
from Scam_detector import ScamDetector
from Conversation_agent import ConversationAgent
from Intelligence_extractor import IntelligenceExtractor
from Session_manager import SessionManager

# ============================================================================
# CONFIGURATION
# ============================================================================

app = Flask(__name__, static_folder='.')
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Configuration
API_KEY = os.getenv('API_KEY', 'hackathon-api-key-2026')
GUVI_CALLBACK_URL = os.getenv('GUVI_CALLBACK_URL', 'https://hackathon.guvi.in/api/updateHoneyPotFinalResult')
PORT = int(os.getenv('PORT', 5000))

# Initialize components
try:
    scam_detector = ScamDetector()
    conversation_agent = ConversationAgent()
    intelligence_extractor = IntelligenceExtractor()
    session_manager = SessionManager()
    logger.info("✅ All components initialized")
except Exception as e:
    logger.error(f"❌ Initialization error: {e}", exc_info=True)
    raise

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def verify_api_key():
    """Verify API key from request headers"""
    provided_key = request.headers.get('x-api-key', '').strip()
    if not provided_key or provided_key != API_KEY:
        logger.warning("❌ Invalid API key attempted")
        return False
    return True

def validate_request(f):
    """Decorator to validate incoming requests"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Check Content-Type
            if request.content_type != 'application/json':
                return jsonify({'status': 'error', 'message': 'Content-Type must be application/json'}), 400

            # Check API key
            if not verify_api_key():
                return jsonify({'status': 'error', 'message': 'Invalid or missing API key'}), 401

            # Parse JSON
            try:
                data = request.get_json(force=True)
            except:
                return jsonify({'status': 'error', 'message': 'Invalid JSON format'}), 400

            if not data:
                return jsonify({'status': 'error', 'message': 'No data provided'}), 400

            # Validate required fields
            if 'sessionId' not in data or 'message' not in data:
                return jsonify({'status': 'error', 'message': 'Missing required fields: sessionId, message'}), 400

            message = data.get('message', {})
            message_text = str(message.get('text', '')).strip()
            
            if not message_text:
                return jsonify({'status': 'error', 'message': 'message.text cannot be empty'}), 400

            if len(message_text) > 5000:
                return jsonify({'status': 'error', 'message': 'message.text exceeds 5000 characters'}), 400

            return f(*args, **kwargs)

        except Exception as e:
            logger.error(f"❌ Validation error: {e}", exc_info=True)
            return jsonify({'status': 'error', 'message': 'Request validation failed'}), 500

    return decorated_function

def send_final_result_to_guvi(session_id, session_data):
    """Send final results to GUVI evaluation endpoint"""
    if not session_data.get('scam_detected'):
        return True

    try:
        payload = {
            "sessionId": session_id,
            "scamDetected": session_data.get('scam_detected', False),
            "totalMessagesExchanged": session_data.get('message_count', 0),
            "extractedIntelligence": session_data.get('intelligence', {}),
            "agentNotes": session_data.get('agent_notes', '')
        }

        logger.info(f"📤 Sending GUVI callback for session {session_id}")
        response = requests.post(GUVI_CALLBACK_URL, json=payload, timeout=10, headers={'Content-Type': 'application/json'})

        if response.status_code in [200, 201, 202]:
            logger.info(f"✅ GUVI callback SUCCESS for {session_id}")
            return True
        else:
            logger.error(f"❌ GUVI callback FAILED (Status: {response.status_code})")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"❌ GUVI callback TIMEOUT")
        return False
    except Exception as e:
        logger.error(f"❌ GUVI callback ERROR: {e}", exc_info=True)
        return False

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def serve_dashboard():
    """Serve the main dashboard HTML"""
    try:
        return send_from_directory('.', 'index.html')
    except:
        return jsonify({
            'status': 'running',
            'service': 'Agentic Honey-Pot API',
            'version': '1.0.0',
            'message': 'Dashboard not found. Please ensure index.html is in the project root.',
            'endpoints': {
                'health': '/health',
                'analyze': '/analyze',
                'sessions': '/sessions'
            }
        }), 200

@app.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        'status': 'running',
        'service': 'Agentic Honey-Pot API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'analyze': '/analyze',
            'sessions': '/sessions'
        }
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'service': 'Agentic Honey-Pot API',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'scam_detector': 'ready',
                'conversation_agent': 'ready',
                'intelligence_extractor': 'ready',
                'session_manager': 'ready'
            }
        }), 200
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/analyze', methods=['POST'])
@validate_request
def analyze_message():
    """Main API endpoint for scam detection and engagement"""
    start_time = datetime.utcnow()

    try:
        data = request.get_json(force=True)
        session_id = str(data.get('sessionId')).strip()
        message = data.get('message', {})
        conversation_history = data.get('conversationHistory', [])
        metadata = data.get('metadata', {})

        message_text = str(message.get('text', '')).strip()
        sender = str(message.get('sender', 'scammer')).strip()
        message_timestamp = message.get('timestamp', datetime.utcnow().isoformat())

        logger.info(f"📨 [Session: {session_id}] Processing message from {sender}")

        # Get or create session
        session_data = session_manager.get_or_create_session(session_id)
        session_data['message_count'] += 1
        session_data['last_activity'] = datetime.utcnow().isoformat()

        # Build conversation history
        full_conversation = [
            {'sender': str(m.get('sender', '')), 'text': str(m.get('text', '')), 'timestamp': m.get('timestamp', '')}
            for m in (conversation_history or [])
        ]

        full_conversation.append({
            'sender': sender,
            'text': message_text,
            'timestamp': message_timestamp
        })

        session_data['conversation'].append({
            'sender': sender,
            'text': message_text,
            'timestamp': message_timestamp
        })

        # SCAM DETECTION (first 5 messages only)
        if session_data['message_count'] <= 5 and not session_data['scam_detected']:
            try:
                is_scam, confidence, indicators = scam_detector.detect_scam(message_text, full_conversation)
                
                if is_scam and confidence > 0.5:
                    session_data['scam_detected'] = True
                    session_data['scam_confidence'] = float(confidence)
                    session_data['scam_indicators'] = indicators or []
                    logger.info(f"🚨 [Session: {session_id}] SCAM DETECTED (Confidence: {confidence:.2%})")

            except Exception as e:
                logger.error(f"❌ Scam detection error: {e}", exc_info=True)

        # INTELLIGENCE EXTRACTION
        try:
            intelligence = intelligence_extractor.extract_from_text(message_text)
            for key in ['bankAccounts', 'upiIds', 'phishingLinks', 'phoneNumbers', 'suspiciousKeywords']:
                if key in intelligence:
                    session_data['intelligence'][key].extend(intelligence[key])
            
            for key in session_data['intelligence']:
                session_data['intelligence'][key] = list(dict.fromkeys(session_data['intelligence'][key]))

            logger.info(f"✅ [Session: {session_id}] Intelligence extracted")

        except Exception as e:
            logger.error(f"❌ Intelligence extraction error: {e}", exc_info=True)

        # AGENT RESPONSE GENERATION
        try:
            agent_response = conversation_agent.generate_response(
                message_text,
                full_conversation,
                session_data['scam_detected'],
                session_data['message_count']
            )
            
            if not agent_response or len(agent_response) > 500:
                agent_response = "I'm sorry, I didn't understand that. Could you please explain more?"
            
            logger.info(f"💬 [Session: {session_id}] Agent response generated")

        except Exception as e:
            logger.error(f"❌ Agent response error: {e}", exc_info=True)
            agent_response = "I'm having trouble understanding. Can you repeat that?"

        session_data['conversation'].append({
            'sender': 'user',
            'text': agent_response,
            'timestamp': datetime.utcnow().isoformat()
        })

        # AGENT NOTES
        try:
            if session_data['scam_detected']:
                agent_notes = conversation_agent.generate_agent_notes(
                    session_data.get('scam_indicators', []),
                    session_data['intelligence']
                )
                session_data['agent_notes'] = agent_notes or ''
        except Exception as e:
            logger.warning(f"⚠️ Agent notes error: {e}")

        # Calculate engagement metrics
        try:
            start_dt = datetime.fromisoformat(session_data['start_time'].replace('Z', '+00:00'))
            current_dt = datetime.utcnow()
            engagement_seconds = int((current_dt - start_dt).total_seconds())
        except:
            engagement_seconds = 0

        # Update session
        session_manager.update_session(session_id, session_data)

        # Prepare response
        response_data = {
            'status': 'success',
            'sessionId': session_id,
            'scamDetected': session_data['scam_detected'],
            'scamConfidence': session_data.get('scam_confidence', 0.0),
            'agentResponse': agent_response,
            'engagementMetrics': {
                'engagementDurationSeconds': engagement_seconds,
                'totalMessagesExchanged': session_data['message_count']
            },
            'extractedIntelligence': session_data['intelligence'],
            'agentNotes': session_data.get('agent_notes', ''),
            'timestamp': datetime.utcnow().isoformat()
        }

        # Send GUVI callback
        if session_data['scam_detected'] and session_data['message_count'] >= 3:
            send_final_result_to_guvi(session_id, session_data)

        response_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"✅ [Session: {session_id}] Response in {response_time:.2f}s")

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"❌ /analyze error: {e}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/sessions', methods=['GET'])
def get_sessions():
    """Get all active sessions and statistics"""
    try:
        if not verify_api_key():
            return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401

        sessions = session_manager.list_sessions()
        stats = session_manager.get_statistics()

        return jsonify({
            'status': 'success',
            'sessions': sessions,
            'statistics': stats,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"❌ /sessions error: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': 'Failed to retrieve sessions'}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found',
        'available_endpoints': ['/', '/api', '/health', '/analyze', '/sessions']
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'status': 'error', 'message': 'Method not allowed'}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Internal error: {error}", exc_info=True)
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 80)
    logger.info("🚀 AGENTIC HONEY-POT API - PRODUCTION START")
    logger.info("=" * 80)
    logger.info(f"API Key: {API_KEY[:20]}...")
    logger.info(f"GUVI Callback: {GUVI_CALLBACK_URL}")
    logger.info(f"Port: {PORT}")
    logger.info(f"Dashboard: http://localhost:{PORT}/")
    logger.info("=" * 80)

    try:
        app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("👋 Shutdown complete")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise
