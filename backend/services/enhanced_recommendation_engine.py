"""
Enhanced Movie Recommendation Engine with TMDb Integration
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np
from datetime import datetime, timedelta
import re

from .tmdb_client import TMDbClient, MovieData
from .gpt_emotion_analyzer import GPTEmotionAnalyzer
from config import get_config

logger = logging.getLogger(__name__)
config = get_config()

@dataclass
class RecommendationResult:
    """Recommendation result structure"""
    movie: MovieData
    score: float
    match_reasons: List[str]
    mood_matches: Dict[str, float]
    emotion_matches: Dict[str, float]

class EnhancedRecommendationEngine:
    """Enhanced recommendation engine with TMDb integration"""
    
    def __init__(self):
        self.tmdb_client = TMDbClient()
        # OpenAI client issue resolved - re-enable emotion analyzer
        self.emotion_analyzer = GPTEmotionAnalyzer()
        
        # Genre mood mapping
        self.genre_mood_mapping = {
            'Action': {'action': 0.9, 'intense': 0.8, 'energetic': 0.7, 'adventure': 0.6},
            'Adventure': {'adventure': 0.9, 'energetic': 0.7, 'uplifting': 0.6, 'feel-good': 0.5},
            'Animation': {'feel-good': 0.8, 'uplifting': 0.7, 'heartwarming': 0.6, 'comedy': 0.5},
            'Comedy': {'comedy': 0.9, 'feel-good': 0.8, 'uplifting': 0.7, 'heartwarming': 0.6},
            'Crime': {'intense': 0.8, 'thriller': 0.7, 'drama': 0.6, 'action': 0.5},
            'Documentary': {'educational': 0.9, 'thoughtful': 0.8, 'drama': 0.6},
            'Drama': {'drama': 0.9, 'emotional': 0.8, 'thoughtful': 0.7, 'intense': 0.6},
            'Family': {'feel-good': 0.9, 'heartwarming': 0.8, 'uplifting': 0.7, 'comedy': 0.6},
            'Fantasy': {'adventure': 0.8, 'magical': 0.9, 'uplifting': 0.6, 'feel-good': 0.5},
            'History': {'drama': 0.7, 'thoughtful': 0.8, 'educational': 0.6},
            'Horror': {'scary': 0.9, 'intense': 0.8, 'thriller': 0.7},
            'Music': {'uplifting': 0.8, 'feel-good': 0.7, 'emotional': 0.6, 'heartwarming': 0.5},
            'Mystery': {'thriller': 0.8, 'intense': 0.7, 'thoughtful': 0.6},
            'Romance': {'romance': 0.9, 'heartwarming': 0.8, 'feel-good': 0.7, 'emotional': 0.6},
            'Science Fiction': {'sci-fi': 0.9, 'adventure': 0.7, 'thoughtful': 0.6, 'action': 0.5},
            'TV Movie': {'drama': 0.6, 'feel-good': 0.5},
            'Thriller': {'thriller': 0.9, 'intense': 0.8, 'action': 0.6},
            'War': {'intense': 0.8, 'drama': 0.7, 'action': 0.6, 'thoughtful': 0.5},
            'Western': {'action': 0.7, 'adventure': 0.6, 'drama': 0.5}
        }
        
        # Emotion to mood mapping
        self.emotion_mood_mapping = {
            'joy': {'feel-good': 0.9, 'uplifting': 0.8, 'comedy': 0.7, 'heartwarming': 0.6},
            'sadness': {'drama': 0.8, 'emotional': 0.9, 'melancholic': 0.7, 'thoughtful': 0.6},
            'anger': {'intense': 0.8, 'action': 0.7, 'thriller': 0.6},
            'fear': {'scary': 0.9, 'thriller': 0.8, 'intense': 0.7},
            'surprise': {'adventure': 0.7, 'thriller': 0.6, 'comedy': 0.5},
            'excitement': {'action': 0.8, 'adventure': 0.7, 'energetic': 0.9, 'uplifting': 0.6},
            'calmness': {'calming': 0.9, 'peaceful': 0.8, 'thoughtful': 0.7, 'drama': 0.5},
            'nostalgia': {'nostalgic': 0.9, 'heartwarming': 0.7, 'drama': 0.6, 'feel-good': 0.5}
        }
    
    def _calculate_mood_score(self, movie: MovieData, target_moods: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """Calculate how well a movie matches target moods"""
        movie_moods = {}
        
        # Calculate mood scores based on genres
        for genre in movie.genres:
            if genre in self.genre_mood_mapping:
                for mood, score in self.genre_mood_mapping[genre].items():
                    movie_moods[mood] = max(movie_moods.get(mood, 0), score)
        
        # Calculate match score
        total_score = 0
        mood_matches = {}
        
        for mood, target_score in target_moods.items():
            movie_mood_score = movie_moods.get(mood, 0)
            match_score = min(target_score, movie_mood_score)
            mood_matches[mood] = match_score
            total_score += match_score * target_score  # Weight by target importance
        
        # Normalize by total target mood strength
        total_target = sum(target_moods.values())
        if total_target > 0:
            total_score /= total_target
        
        return total_score, mood_matches
    
    def _calculate_emotion_score(self, movie: MovieData, target_emotions: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """Calculate how well a movie matches target emotions"""
        emotion_matches = {}
        total_score = 0
        
        for emotion, target_score in target_emotions.items():
            if emotion in self.emotion_mood_mapping:
                emotion_mood_score = 0
                for mood, mood_score in self.emotion_mood_mapping[emotion].items():
                    # Check if movie has this mood (from genres)
                    for genre in movie.genres:
                        if genre in self.genre_mood_mapping:
                            genre_mood_score = self.genre_mood_mapping[genre].get(mood, 0)
                            emotion_mood_score = max(emotion_mood_score, genre_mood_score * mood_score)
                
                emotion_matches[emotion] = emotion_mood_score
                total_score += emotion_mood_score * target_score
        
        # Normalize
        total_target = sum(target_emotions.values())
        if total_target > 0:
            total_score /= total_target
        
        return total_score, emotion_matches
    
    def _calculate_quality_score(self, movie: MovieData) -> float:
        """Calculate movie quality score"""
        # Base score from rating
        rating_score = min(movie.vote_average / 10.0, 1.0)
        
        # Popularity boost (but not too much)
        popularity_score = min(movie.popularity / 100.0, 0.3)
        
        # Vote count reliability
        vote_reliability = min(movie.vote_count / 1000.0, 0.2)
        
        return rating_score + popularity_score + vote_reliability
    
    def _generate_match_reasons(self, movie: MovieData, mood_matches: Dict[str, float], 
                              emotion_matches: Dict[str, float], target_moods: Dict[str, float],
                              target_emotions: Dict[str, float]) -> List[str]:
        """Generate human-readable match reasons"""
        reasons = []
        
        # Top mood matches
        top_moods = sorted(mood_matches.items(), key=lambda x: x[1], reverse=True)[:3]
        for mood, score in top_moods:
            if score > 0.3 and mood in target_moods:
                reasons.append(f"Matches your {mood.replace('-', ' ')} mood")
        
        # Top emotion matches
        top_emotions = sorted(emotion_matches.items(), key=lambda x: x[1], reverse=True)[:2]
        for emotion, score in top_emotions:
            if score > 0.3 and emotion in target_emotions:
                reasons.append(f"Suits your {emotion} feeling")
        
        # Genre matches
        if movie.genres:
            primary_genre = movie.genres[0]
            reasons.append(f"Great {primary_genre.lower()} film")
        
        # Quality indicators
        if movie.vote_average >= 7.5:
            reasons.append("Highly rated film")
        elif movie.vote_average >= 6.5:
            reasons.append("Well-reviewed movie")
        
        if movie.popularity > 50:
            reasons.append("Popular choice")
        
        # Fallback
        if not reasons:
            reasons.append("Recommended for you")
        
        return reasons[:4]  # Limit to 4 reasons
    
    def recommend_by_mood_analysis(self, analysis_result: Dict[str, Any], 
                                 num_recommendations: int = 8) -> List[RecommendationResult]:
        """Recommend movies based on emotion analysis result"""
        target_moods = analysis_result.get('moods', {})
        target_emotions = analysis_result.get('emotions', {})
        
        # Get candidate movies from multiple sources
        candidates = []
        
        # Search by top moods
        top_moods = sorted(target_moods.items(), key=lambda x: x[1], reverse=True)[:3]
        for mood, score in top_moods:
            if score > 0.3:
                # Convert mood to search terms
                search_terms = self._mood_to_search_terms(mood)
                for term in search_terms:
                    movies = self.tmdb_client.search_movies(term)
                    candidates.extend(movies[:10])  # Limit per search
        
        # Get popular movies as fallback
        if len(candidates) < 20:
            popular_movies = self.tmdb_client.get_popular_movies()
            candidates.extend(popular_movies[:20])
        
        # Remove duplicates
        seen_ids = set()
        unique_candidates = []
        for movie in candidates:
            if movie.id not in seen_ids:
                seen_ids.add(movie.id)
                unique_candidates.append(movie)
        
        # Score and rank candidates
        recommendations = []
        for movie in unique_candidates:
            mood_score, mood_matches = self._calculate_mood_score(movie, target_moods)
            emotion_score, emotion_matches = self._calculate_emotion_score(movie, target_emotions)
            quality_score = self._calculate_quality_score(movie)
            
            # Combined score
            total_score = (mood_score * 0.4 + emotion_score * 0.4 + quality_score * 0.2)
            
            # Generate reasons
            reasons = self._generate_match_reasons(movie, mood_matches, emotion_matches, 
                                                 target_moods, target_emotions)
            
            recommendation = RecommendationResult(
                movie=movie,
                score=total_score,
                match_reasons=reasons,
                mood_matches=mood_matches,
                emotion_matches=emotion_matches
            )
            recommendations.append(recommendation)
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:num_recommendations]
    
    def recommend_by_text_search(self, search_text: str, 
                               num_recommendations: int = 8) -> List[RecommendationResult]:
        """Recommend movies based on free text search"""
        # Emotion analysis is now working - re-enable
        analysis_result = self.emotion_analyzer.analyze_emotion(search_text)
        
        # Extract specific search criteria from text
        search_criteria = self._extract_search_criteria(search_text)
        
        # Get candidate movies
        candidates = []
        
        # Direct search with the text
        direct_search = self.tmdb_client.search_movies(search_text)
        candidates.extend(direct_search[:15])
        
        # Search with extracted keywords
        for keyword in search_criteria.get('keywords', []):
            keyword_search = self.tmdb_client.search_movies(keyword)
            candidates.extend(keyword_search[:10])
        
        # Genre-based discovery
        if search_criteria.get('genres'):
            for genre_id in search_criteria['genres']:
                genre_movies = self.tmdb_client.discover_movies(with_genres=genre_id)
                candidates.extend(genre_movies[:10])
        
        # Year-based discovery
        if search_criteria.get('year'):
            year_movies = self.tmdb_client.discover_movies(year=search_criteria['year'])
            candidates.extend(year_movies[:10])
        
        # Runtime-based discovery
        if search_criteria.get('runtime'):
            runtime_movies = self.tmdb_client.discover_movies(
                **search_criteria['runtime']
            )
            candidates.extend(runtime_movies[:10])
        
        # Remove duplicates
        seen_ids = set()
        unique_candidates = []
        for movie in unique_candidates:
            if movie.id not in seen_ids:
                seen_ids.add(movie.id)
                unique_candidates.append(movie)
        
        # If we have analysis results, use mood-based scoring
        if analysis_result.get('moods') or analysis_result.get('emotions'):
            return self.recommend_by_mood_analysis(analysis_result, num_recommendations)
        
        # Otherwise, use text relevance scoring
        recommendations = []
        for movie in unique_candidates:
            relevance_score = self._calculate_text_relevance(movie, search_text, search_criteria)
            quality_score = self._calculate_quality_score(movie)
            
            total_score = relevance_score * 0.7 + quality_score * 0.3
            
            reasons = self._generate_text_match_reasons(movie, search_text, search_criteria)
            
            recommendation = RecommendationResult(
                movie=movie,
                score=total_score,
                match_reasons=reasons,
                mood_matches={},
                emotion_matches={}
            )
            recommendations.append(recommendation)
        
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:num_recommendations]
    
    def _mood_to_search_terms(self, mood: str) -> List[str]:
        """Convert mood to search terms"""
        mood_search_map = {
            'action': ['action', 'adventure', 'superhero'],
            'romance': ['romance', 'love', 'romantic'],
            'comedy': ['comedy', 'funny', 'humor'],
            'drama': ['drama', 'emotional'],
            'thriller': ['thriller', 'suspense'],
            'horror': ['horror', 'scary'],
            'sci-fi': ['science fiction', 'sci-fi', 'future'],
            'fantasy': ['fantasy', 'magic'],
            'feel-good': ['feel good', 'uplifting', 'heartwarming'],
            'intense': ['intense', 'action', 'thriller'],
            'calming': ['peaceful', 'calm', 'relaxing'],
            'nostalgic': ['classic', 'vintage', 'nostalgic']
        }
        return mood_search_map.get(mood, [mood])
    
    def _extract_search_criteria(self, text: str) -> Dict[str, Any]:
        """Extract specific search criteria from text"""
        criteria = {
            'keywords': [],
            'genres': [],
            'year': None,
            'runtime': {}
        }
        
        text_lower = text.lower()
        
        # Extract year patterns
        year_patterns = [
            r'(\d{4})年',  # Japanese year format
            r'(\d{4})s',   # 1990s format
            r'(\d{4})',    # Simple year
        ]
        
        for pattern in year_patterns:
            match = re.search(pattern, text)
            if match:
                year = int(match.group(1))
                if 1900 <= year <= 2030:
                    criteria['year'] = year
                    break
        
        # Extract runtime patterns
        runtime_patterns = [
            r'(\d+)分',  # Japanese minutes
            r'(\d+)\s*minutes?',
            r'(\d+)\s*mins?',
        ]
        
        for pattern in runtime_patterns:
            match = re.search(pattern, text_lower)
            if match:
                runtime = int(match.group(1))
                criteria['runtime'] = {
                    'with_runtime.gte': max(runtime - 15, 0),
                    'with_runtime.lte': runtime + 15
                }
                break
        
        # Extract genre keywords
        genre_keywords = {
            'action': ['action', 'アクション'],
            'comedy': ['comedy', 'funny', 'コメディ', '笑える'],
            'romance': ['romance', 'romantic', 'ロマンス', '恋愛'],
            'drama': ['drama', 'ドラマ'],
            'horror': ['horror', 'scary', 'ホラー', '怖い'],
            'thriller': ['thriller', 'suspense', 'スリラー'],
            'sci-fi': ['sci-fi', 'science fiction', 'SF'],
            'fantasy': ['fantasy', 'ファンタジー'],
            'animation': ['animation', 'animated', 'アニメ'],
            'documentary': ['documentary', 'ドキュメンタリー']
        }
        
        for genre, keywords in genre_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    criteria['keywords'].append(genre)
                    break
        
        # Extract general keywords
        keywords = re.findall(r'\b\w+\b', text_lower)
        criteria['keywords'].extend([kw for kw in keywords if len(kw) > 3])
        
        return criteria
    
    def _calculate_text_relevance(self, movie: MovieData, search_text: str, 
                                criteria: Dict[str, Any]) -> float:
        """Calculate how relevant a movie is to the search text"""
        score = 0
        search_lower = search_text.lower()
        
        # Title match
        if search_lower in movie.title.lower():
            score += 0.8
        if search_lower in movie.original_title.lower():
            score += 0.6
        
        # Overview match
        overview_words = movie.overview.lower().split()
        search_words = search_lower.split()
        word_matches = sum(1 for word in search_words if word in overview_words)
        score += (word_matches / len(search_words)) * 0.4
        
        # Genre match
        for keyword in criteria.get('keywords', []):
            for genre in movie.genres:
                if keyword.lower() in genre.lower():
                    score += 0.3
        
        # Year match
        if criteria.get('year') and movie.release_date:
            try:
                movie_year = int(movie.release_date[:4])
                if movie_year == criteria['year']:
                    score += 0.5
                elif abs(movie_year - criteria['year']) <= 2:
                    score += 0.2
            except (ValueError, IndexError):
                pass
        
        return min(score, 1.0)
    
    def _generate_text_match_reasons(self, movie: MovieData, search_text: str, 
                                   criteria: Dict[str, Any]) -> List[str]:
        """Generate match reasons for text search"""
        reasons = []
        
        # Direct text matches
        if search_text.lower() in movie.title.lower():
            reasons.append("Title matches your search")
        
        # Genre matches
        if movie.genres:
            for keyword in criteria.get('keywords', []):
                for genre in movie.genres:
                    if keyword.lower() in genre.lower():
                        reasons.append(f"Matches {genre} genre")
                        break
        
        # Year match
        if criteria.get('year') and movie.release_date:
            try:
                movie_year = int(movie.release_date[:4])
                if movie_year == criteria['year']:
                    reasons.append(f"From {movie_year}")
            except (ValueError, IndexError):
                pass
        
        # Quality indicators
        if movie.vote_average >= 7.5:
            reasons.append("Highly rated")
        
        if not reasons:
            reasons.append("Recommended based on your search")
        
        return reasons[:4]

