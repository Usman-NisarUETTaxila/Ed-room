"""
Backend cache for EdRoom API responses
Provides in-memory caching with TTL and fallback responses for offline scenarios
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BackendCache:
    def __init__(self, max_entries: int = 200, default_ttl: int = 3600):
        """
        Initialize backend cache
        
        Args:
            max_entries: Maximum number of cached entries
            default_ttl: Default time-to-live in seconds (1 hour)
        """
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.cache = {}  # key -> {value, timestamp, ttl}
        
    def _normalize_key(self, text: str) -> str:
        """Normalize text for consistent cache keys"""
        if not text:
            return ""
        return text.lower().strip().replace('\n', ' ').replace('\r', '')
    
    def _generate_key(self, user_message: str, has_pdf: bool = False) -> str:
        """Generate cache key from user input"""
        normalized = self._normalize_key(user_message)
        key_data = f"{normalized}|pdf:{has_pdf}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, entry in self.cache.items():
            if current_time - entry['timestamp'] > entry['ttl']:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            
        logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _enforce_size_limit(self):
        """Enforce maximum cache size by removing oldest entries"""
        if len(self.cache) <= self.max_entries:
            return
            
        # Sort by timestamp and remove oldest entries
        sorted_items = sorted(self.cache.items(), key=lambda x: x[1]['timestamp'])
        entries_to_remove = len(self.cache) - self.max_entries
        
        for i in range(entries_to_remove):
            key = sorted_items[i][0]
            del self.cache[key]
            
        logger.debug(f"Removed {entries_to_remove} old cache entries to enforce size limit")
    
    def put(self, user_message: str, response_data: Dict[str, Any], has_pdf: bool = False, ttl: Optional[int] = None):
        """
        Store response in cache
        
        Args:
            user_message: User's input message
            response_data: API response data to cache
            has_pdf: Whether the request included a PDF
            ttl: Time-to-live override in seconds
        """
        try:
            key = self._generate_key(user_message, has_pdf)
            cache_ttl = ttl or self.default_ttl
            
            # Store only essential response data to save memory
            cached_response = {
                'bot_response': response_data.get('bot_response', ''),
                'translation_info': response_data.get('translation_info'),
                'explanation_result': response_data.get('explanation_result'),
                'final_approved': response_data.get('final_approved', True),
                'success': response_data.get('success', True)
            }
            
            self.cache[key] = {
                'value': cached_response,
                'timestamp': time.time(),
                'ttl': cache_ttl,
                'original_message': user_message[:100]  # Store truncated for debugging
            }
            
            # Cleanup and size management
            self._cleanup_expired()
            self._enforce_size_limit()
            
            logger.debug(f"Cached response for message: {user_message[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to cache response: {e}")
    
    def get(self, user_message: str, has_pdf: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response
        
        Args:
            user_message: User's input message
            has_pdf: Whether the request includes a PDF
            
        Returns:
            Cached response data or None if not found/expired
        """
        try:
            key = self._generate_key(user_message, has_pdf)
            
            if key not in self.cache:
                return None
                
            entry = self.cache[key]
            current_time = time.time()
            
            # Check if expired
            if current_time - entry['timestamp'] > entry['ttl']:
                del self.cache[key]
                logger.debug(f"Cache entry expired for: {user_message[:50]}...")
                return None
            
            logger.debug(f"Cache hit for message: {user_message[:50]}...")
            return entry['value']
            
        except Exception as e:
            logger.error(f"Failed to retrieve from cache: {e}")
            return None
    
    def get_fallback_response(self, user_message: str, error_context: str = "network") -> Dict[str, Any]:
        """
        Generate a structured fallback response when services are unavailable
        
        Args:
            user_message: User's input message
            error_context: Context of the error (network, service, etc.)
            
        Returns:
            Structured fallback response
        """
        try:
            # Try to find a similar cached response first
            similar_response = self._find_similar_cached_response(user_message)
            if similar_response:
                # Annotate as cached fallback
                similar_response['bot_response'] = f"**[Cached Response]** Service temporarily unavailable. Here's a previous similar response:\n\n{similar_response['bot_response']}"
                return similar_response
            
            # Generate structured canned response
            sections = [
                "**Summary:**",
                "The AI service is temporarily unavailable, but I can still help you with a structured response.",
                "",
                "**Your Request:**",
                f"{user_message}",
                "",
                "**Key Points:**",
                "- Your message has been received and processed locally",
                "- This is a temporary fallback response",
                "- Full AI capabilities will return when the service reconnects",
                "",
                "**Status Information:**",
                "```json",
                json.dumps({
                    "status": "fallback_mode",
                    "reason": error_context,
                    "timestamp": datetime.now().isoformat(),
                    "message_length": len(user_message),
                    "cache_entries": len(self.cache)
                }, indent=2),
                "```",
                "",
                "**Next Steps:**",
                "- Try your request again in a few moments",
                "- The system will automatically reconnect when available",
                "- Your conversation history is preserved"
            ]
            
            return {
                'bot_response': '\n'.join(sections),
                'success': True,
                'final_approved': True,
                'translation_info': None,
                'explanation_result': None,
                'is_fallback': True
            }
            
        except Exception as e:
            logger.error(f"Failed to generate fallback response: {e}")
            return {
                'bot_response': f"**[System Message]** Service temporarily unavailable. Your message: '{user_message[:100]}...' has been received.",
                'success': True,
                'final_approved': True,
                'is_fallback': True
            }
    
    def _find_similar_cached_response(self, user_message: str, similarity_threshold: float = 0.3) -> Optional[Dict[str, Any]]:
        """
        Find a similar cached response using simple text similarity
        
        Args:
            user_message: User's input message
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            Similar cached response or None
        """
        try:
            normalized_input = self._normalize_key(user_message)
            input_words = set(normalized_input.split())
            
            best_match = None
            best_score = 0
            
            for entry in self.cache.values():
                if 'original_message' not in entry:
                    continue
                    
                cached_message = self._normalize_key(entry['original_message'])
                cached_words = set(cached_message.split())
                
                if not cached_words:
                    continue
                
                # Simple Jaccard similarity
                intersection = input_words.intersection(cached_words)
                union = input_words.union(cached_words)
                similarity = len(intersection) / len(union) if union else 0
                
                if similarity > best_score and similarity >= similarity_threshold:
                    best_score = similarity
                    best_match = entry['value'].copy()
            
            if best_match:
                logger.debug(f"Found similar cached response with similarity: {best_score:.2f}")
                
            return best_match
            
        except Exception as e:
            logger.error(f"Error finding similar cached response: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        expired_count = sum(1 for entry in self.cache.values() 
                          if current_time - entry['timestamp'] > entry['ttl'])
        
        return {
            'total_entries': len(self.cache),
            'expired_entries': expired_count,
            'active_entries': len(self.cache) - expired_count,
            'max_entries': self.max_entries,
            'default_ttl': self.default_ttl
        }
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        logger.info("Cache cleared")

# Global cache instance
cache_instance = BackendCache()
