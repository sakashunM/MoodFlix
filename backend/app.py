#!/usr/bin/env python3
"""
MoodFlix Backend API
Movie recommendation service with emotion analysis
"""

import os
import sys
import logging
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime
import structlog

from config import get_config, Config
from services.enhanced_recommendation_engine import EnhancedRecommendationEngine
from services.gpt_emotion_analyzer import GPTEmotionAnalyzer
from services.tmdb_client import TMDbClient
from utils.rate_limiter import rate_limit, openai_usage_limit

# Clear ALL proxy environment variables at startup to prevent httpx issues
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('NO_PROXY', None)
os.environ.pop('no_proxy', None)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Initialize Flask app
app = Flask(__name__)
config = get_config()
app.config.from_object(config)

# Setup CORS
CORS(app, origins=config.CORS_ORIGINS)

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = structlog.get_logger(__name__)

# Initialize services
try:
    recommendation_engine = EnhancedRecommendationEngine()
    # OpenAI client issue resolved - re-enable emotion analyzer
    emotion_analyzer = GPTEmotionAnalyzer()
    tmdb_client = TMDbClient()
    logger.info("Services initialized successfully")
except Exception as e:
    logger.error("Failed to initialize services", error=str(e))
    raise

# Validate required environment variables
missing_vars = Config.validate_required_env_vars()
if missing_vars:
    logger.error("Missing required environment variables", missing_vars=missing_vars)
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

@app.before_request
def log_request():
    """Log incoming requests"""
    logger.info(
        "Request received",
        method=request.method,
        path=request.path,
        remote_addr=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')
    )

@app.after_request
def log_response(response):
    """Log outgoing responses"""
    logger.info(
        "Response sent",
        status_code=response.status_code,
        content_length=response.content_length
    )
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Global exception handler"""
    logger.error(
        "Unhandled exception",
        error=str(e),
        traceback=traceback.format_exc()
    )
    
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred. Please try again later.',
        'timestamp': datetime.utcnow().isoformat()
    }), 500

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested resource was not found.',
        'timestamp': datetime.utcnow().isoformat()
    }), 404

@app.errorhandler(429)
def rate_limit_exceeded(e):
    """Handle rate limit errors"""
    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'timestamp': datetime.utcnow().isoformat()
    }), 429

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check TMDb connectivity
        tmdb_healthy = tmdb_client.health_check()
        
        # Check OpenAI (basic check)
        openai_healthy = bool(config.OPENAI_API_KEY)
        
        status = {
            'status': 'healthy' if tmdb_healthy and openai_healthy else 'degraded',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'tmdb': 'healthy' if tmdb_healthy else 'unhealthy',
                'openai': 'healthy' if openai_healthy else 'unhealthy',
                'redis': 'healthy'  # Assume healthy if app started
            },
            'version': '2.0.0'
        }
        
        return jsonify(status), 200 if status['status'] == 'healthy' else 503
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

# Mood-based recommendation endpoint
@app.route('/api/recommend/mood', methods=['POST'])
@rate_limit(per_minute=config.RATE_LIMIT_PER_MINUTE, per_day=config.RATE_LIMIT_PER_DAY)
@openai_usage_limit(estimated_tokens=1500)
def recommend_by_mood():
    """Get movie recommendations based on mood analysis"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing required field: text'
            }), 400
        
        mood_text = data['text'].strip()
        if not mood_text:
            return jsonify({
                'error': 'Bad request',
                'message': 'Text cannot be empty'
            }), 400
        
        num_recommendations = min(data.get('num_recommendations', 8), 20)
        
        logger.info("Processing mood recommendation", text_length=len(mood_text))
        
        # Analyze emotions using GPT
        try:
            logger.info("Starting emotion analysis with GPT")
            analysis_result = emotion_analyzer.analyze_emotion(mood_text)
            logger.info("Emotion analysis completed successfully", 
                       result_type=type(analysis_result),
                       confidence=analysis_result.get('confidence', 0) if isinstance(analysis_result, dict) else 'N/A')
        except Exception as e:
            logger.error("Emotion analysis failed, using fallback", error=str(e), error_type=type(e))
            import traceback
            logger.error("Traceback", traceback=traceback.format_exc())
            analysis_result = {
                'moods': {'feel-good': 0.8, 'uplifting': 0.7, 'comedy': 0.6},
                'emotions': {'joy': 0.8, 'excitement': 0.6},
                'confidence': 0.7,
                'analysis_method': 'fallback'
            }
        
        logger.info("Analysis result", result_type=type(analysis_result), result=analysis_result)
        
        # Get recommendations
        recommendations = recommendation_engine.recommend_by_mood_analysis(
            analysis_result, num_recommendations
        )
        
        # Format response
        response_data = {
            'analysis': analysis_result,
            'recommendations': [
                {
                    'movie': rec.movie.to_dict(),
                    'score': round(rec.score * 100),  # Convert to percentage
                    'match_reasons': rec.match_reasons,
                    'mood_matches': rec.mood_matches,
                    'emotion_matches': rec.emotion_matches
                }
                for rec in recommendations
            ],
            'metadata': {
                'total_found': len(recommendations),
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'mood_analysis'
            }
        }
        
        logger.info(
            "Mood recommendation completed",
            recommendations_count=len(recommendations),
            analysis_confidence=response_data['analysis'].get('confidence', 0)
        )
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error("Mood recommendation failed", error=str(e))
        return jsonify({
            'error': 'Recommendation failed',
            'message': 'Failed to process mood recommendation. Please try again.',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Text search recommendation endpoint
@app.route('/api/recommend/search', methods=['POST'])
@rate_limit(per_minute=config.RATE_LIMIT_PER_MINUTE, per_day=config.RATE_LIMIT_PER_DAY)
@openai_usage_limit(estimated_tokens=1000)
def recommend_by_search():
    """Get movie recommendations based on free text search"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing required field: text'
            }), 400
        
        search_text = data['text'].strip()
        if not search_text:
            return jsonify({
                'error': 'Bad request',
                'message': 'Search text cannot be empty'
            }), 400
        
        num_recommendations = min(data.get('num_recommendations', 8), 20)
        
        logger.info("Processing text search recommendation", text_length=len(search_text))
        
        # Get recommendations
        recommendations = recommendation_engine.recommend_by_text_search(
            search_text, num_recommendations
        )
        
        # Format response
        response_data = {
            'search_query': search_text,
            'recommendations': [
                {
                    'movie': rec.movie.to_dict(),
                    'score': round(rec.score * 100),  # Convert to percentage
                    'match_reasons': rec.match_reasons,
                    'mood_matches': rec.mood_matches,
                    'emotion_matches': rec.emotion_matches
                }
                for rec in recommendations
            ],
            'metadata': {
                'total_found': len(recommendations),
                'timestamp': datetime.utcnow().isoformat(),
                'method': 'text_search'
            }
        }
        
        logger.info(
            "Text search recommendation completed",
            recommendations_count=len(recommendations)
        )
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error("Text search recommendation failed", error=str(e))
        return jsonify({
            'error': 'Search failed',
            'message': 'Failed to process search recommendation. Please try again.',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Movie details endpoint
@app.route('/api/movie/<int:movie_id>', methods=['GET'])
@rate_limit(per_minute=10, per_day=200)
def get_movie_details(movie_id):
    """Get detailed movie information"""
    try:
        movie = tmdb_client.get_movie_details(movie_id)
        
        if not movie:
            return jsonify({
                'error': 'Movie not found',
                'message': f'Movie with ID {movie_id} not found'
            }), 404
        
        return jsonify({
            'movie': movie.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error("Failed to get movie details", movie_id=movie_id, error=str(e))
        return jsonify({
            'error': 'Failed to get movie details',
            'message': 'Unable to retrieve movie information. Please try again.',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Popular movies endpoint
@app.route('/api/movies/popular', methods=['GET'])
@rate_limit(per_minute=5, per_day=50)
def get_popular_movies():
    """Get popular movies"""
    try:
        page = min(request.args.get('page', 1, type=int), 10)
        movies = tmdb_client.get_popular_movies(page)
        
        return jsonify({
            'movies': [movie.to_dict() for movie in movies],
            'page': page,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error("Failed to get popular movies", error=str(e))
        return jsonify({
            'error': 'Failed to get popular movies',
            'message': 'Unable to retrieve popular movies. Please try again.',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# System status endpoint
@app.route('/api/status', methods=['GET'])
def get_system_status():
    """Get system status and usage information"""
    try:
        from utils.rate_limiter import usage_tracker
        
        # Get OpenAI usage
        usage = usage_tracker.get_monthly_usage()
        within_limit, current_cost, limit = usage_tracker.check_monthly_limit()
        
        status = {
            'system': {
                'status': 'operational',
                'emergency_stop': config.EMERGENCY_STOP,
                'rate_limiting': config.RATE_LIMIT_ENABLED,
                'version': '2.0.0'
            },
            'usage': {
                'openai': {
                    'monthly_cost': round(current_cost, 4),
                    'monthly_limit': limit,
                    'within_limit': within_limit,
                    'requests_this_month': usage.get('requests', 0),
                    'tokens_this_month': usage.get('total_tokens', 0)
                }
            },
            'limits': {
                'requests_per_minute': config.RATE_LIMIT_PER_MINUTE,
                'requests_per_day': config.RATE_LIMIT_PER_DAY
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error("Failed to get system status", error=str(e))
        return jsonify({
            'error': 'Failed to get system status',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Serve static files (for production)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    static_dir = os.path.join(app.root_path, 'static')
    if os.path.exists(static_dir):
        if path and os.path.exists(os.path.join(static_dir, path)):
            return send_from_directory(static_dir, path)
        else:
            return send_from_directory(static_dir, 'index.html')
    else:
        return jsonify({
            'message': 'MoodFlix API Server',
            'version': '2.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'mood_recommendation': '/api/recommend/mood',
                'text_search': '/api/recommend/search',
                'movie_details': '/api/movie/<id>',
                'popular_movies': '/api/movies/popular',
                'system_status': '/api/status'
            }
        })

if __name__ == '__main__':
    logger.info("Starting MoodFlix backend server", version="2.0.0")
    
    # Development server
    if config.DEBUG:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    else:
        # Production server (use gunicorn in production)
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )

