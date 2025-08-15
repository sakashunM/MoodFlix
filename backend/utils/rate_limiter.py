"""
Rate Limiting Utilities
"""

import time
import logging
from typing import Dict, Optional
from functools import wraps
from flask import request, jsonify, g
import redis
import json
from datetime import datetime, timedelta

from config import get_config

logger = logging.getLogger(__name__)
config = get_config()

class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(config.REDIS_URL)
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Rate limiter connected to Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory-based rate limiting: {e}")
            self.use_redis = False
            self.memory_store = {}
    
    def _get_client_id(self) -> str:
        """Get client identifier"""
        # Use IP address as client identifier
        # In production, you might want to use user ID or API key
        return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    def _get_key(self, client_id: str, window: str) -> str:
        """Generate Redis key"""
        return f"rate_limit:{client_id}:{window}"
    
    def _check_redis_limit(self, client_id: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        """Check rate limit using Redis"""
        now = int(time.time())
        window_start = now - window_seconds
        key = self._get_key(client_id, f"{window_seconds}s")
        
        try:
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiry
            pipe.expire(key, window_seconds)
            
            results = pipe.execute()
            current_count = results[1] + 1  # +1 for the request we just added
            
            return current_count <= limit, current_count, limit
            
        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fail open - allow request if Redis is down
            return True, 0, limit
    
    def _check_memory_limit(self, client_id: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        """Check rate limit using memory store"""
        now = time.time()
        window_start = now - window_seconds
        
        if client_id not in self.memory_store:
            self.memory_store[client_id] = []
        
        # Remove old entries
        self.memory_store[client_id] = [
            timestamp for timestamp in self.memory_store[client_id]
            if timestamp > window_start
        ]
        
        # Add current request
        self.memory_store[client_id].append(now)
        
        current_count = len(self.memory_store[client_id])
        return current_count <= limit, current_count, limit
    
    def check_limit(self, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        """Check if request is within rate limit"""
        if not config.RATE_LIMIT_ENABLED:
            return True, 0, limit
        
        client_id = self._get_client_id()
        
        if self.use_redis:
            return self._check_redis_limit(client_id, limit, window_seconds)
        else:
            return self._check_memory_limit(client_id, limit, window_seconds)

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(per_minute: Optional[int] = None, per_day: Optional[int] = None):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if config.EMERGENCY_STOP:
                return jsonify({
                    'error': 'Service temporarily unavailable',
                    'message': 'The service is currently under maintenance.'
                }), 503
            
            # Check per-minute limit
            if per_minute:
                allowed, current, limit = rate_limiter.check_limit(per_minute, 60)
                if not allowed:
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': f'Too many requests. Limit: {limit} per minute.',
                        'current_count': current,
                        'limit': limit,
                        'window': '1 minute'
                    }), 429
            
            # Check per-day limit
            if per_day:
                allowed, current, limit = rate_limiter.check_limit(per_day, 86400)
                if not allowed:
                    return jsonify({
                        'error': 'Daily limit exceeded',
                        'message': f'Daily request limit exceeded. Limit: {limit} per day.',
                        'current_count': current,
                        'limit': limit,
                        'window': '24 hours'
                    }), 429
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class OpenAIUsageTracker:
    """Track OpenAI API usage and costs"""
    
    def __init__(self):
        try:
            self.redis_client = redis.from_url(config.REDIS_URL)
            self.redis_client.ping()
            self.use_redis = True
        except Exception:
            self.use_redis = False
            self.memory_usage = {}
    
    def _get_month_key(self) -> str:
        """Get current month key"""
        now = datetime.now()
        return f"openai_usage:{now.year}:{now.month:02d}"
    
    def track_usage(self, tokens_used: int, estimated_cost: float):
        """Track OpenAI usage"""
        month_key = self._get_month_key()
        
        usage_data = {
            'tokens': tokens_used,
            'cost': estimated_cost,
            'timestamp': time.time()
        }
        
        try:
            if self.use_redis:
                # Get current usage
                current_data = self.redis_client.get(month_key)
                if current_data:
                    current = json.loads(current_data)
                    current['total_tokens'] += tokens_used
                    current['total_cost'] += estimated_cost
                    current['requests'] += 1
                else:
                    current = {
                        'total_tokens': tokens_used,
                        'total_cost': estimated_cost,
                        'requests': 1,
                        'month': month_key
                    }
                
                # Store updated usage
                self.redis_client.setex(
                    month_key, 
                    timedelta(days=32).total_seconds(),  # Keep for 32 days
                    json.dumps(current)
                )
            else:
                # Memory-based tracking
                if month_key not in self.memory_usage:
                    self.memory_usage[month_key] = {
                        'total_tokens': 0,
                        'total_cost': 0.0,
                        'requests': 0
                    }
                
                self.memory_usage[month_key]['total_tokens'] += tokens_used
                self.memory_usage[month_key]['total_cost'] += estimated_cost
                self.memory_usage[month_key]['requests'] += 1
                
        except Exception as e:
            logger.error(f"Failed to track OpenAI usage: {e}")
    
    def get_monthly_usage(self) -> Dict:
        """Get current month's usage"""
        month_key = self._get_month_key()
        
        try:
            if self.use_redis:
                data = self.redis_client.get(month_key)
                if data:
                    return json.loads(data)
            else:
                return self.memory_usage.get(month_key, {})
        except Exception as e:
            logger.error(f"Failed to get OpenAI usage: {e}")
        
        return {
            'total_tokens': 0,
            'total_cost': 0.0,
            'requests': 0
        }
    
    def check_monthly_limit(self) -> tuple[bool, float, float]:
        """Check if monthly limit is exceeded"""
        usage = self.get_monthly_usage()
        current_cost = usage.get('total_cost', 0.0)
        limit = config.OPENAI_MONTHLY_LIMIT
        
        return current_cost < limit, current_cost, limit

# Global usage tracker
usage_tracker = OpenAIUsageTracker()

def openai_usage_limit(estimated_tokens: int = 1000):
    """OpenAI usage limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Estimate cost (rough estimate: $0.002 per 1K tokens for GPT-4)
            estimated_cost = (estimated_tokens / 1000) * 0.002
            
            # Check monthly limit
            within_limit, current_cost, limit = usage_tracker.check_monthly_limit()
            
            if not within_limit:
                return jsonify({
                    'error': 'Monthly OpenAI limit exceeded',
                    'message': f'Monthly spending limit of ${limit} exceeded.',
                    'current_cost': current_cost,
                    'limit': limit
                }), 429
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Track actual usage (you might want to get actual token count from OpenAI response)
            usage_tracker.track_usage(estimated_tokens, estimated_cost)
            
            return result
        return decorated_function
    return decorator

