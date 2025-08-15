"""
映画推薦エンジン
ムードベースの映画推薦システム
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

class MovieRecommendationEngine:
    def __init__(self, movies_data_path: str = None):
        """推薦エンジンを初期化"""
        if movies_data_path is None:
            movies_data_path = os.path.join(os.path.dirname(__file__), '../../data/movies.json')
        
        self.movies = self._load_movies(movies_data_path)
        self.movie_features = self._build_movie_features()
        
        # ムードと映画の関連度重み
        self.mood_weights = {
            'uplifting': 1.0,
            'feel-good': 1.0,
            'comedy': 1.0,
            'melancholic': 1.0,
            'drama': 1.0,
            'emotional': 1.0,
            'intense': 1.0,
            'action': 1.0,
            'thriller': 1.0,
            'calming': 1.0,
            'comfort': 1.0,
            'light': 1.0,
            'adventure': 1.0,
            'energetic': 1.0,
            'peaceful': 1.0,
            'contemplative': 1.0,
            'slow-paced': 1.0,
            'romantic': 1.0,
            'love-story': 1.0,
            'heartwarming': 1.0,
            'classic': 1.0,
            'vintage': 1.0,
            'coming-of-age': 1.0
        }
    
    def _load_movies(self, file_path: str) -> List[Dict]:
        """映画データを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Movie data file not found: {file_path}")
            return []
        except json.JSONDecodeError:
            print(f"Invalid JSON in movie data file: {file_path}")
            return []
    
    def _build_movie_features(self) -> Dict:
        """映画の特徴量を構築"""
        features = {}
        
        for movie in self.movies:
            movie_id = movie['id']
            
            # テキスト特徴量（ジャンル、ムード、説明）
            text_features = ' '.join([
                ' '.join(movie.get('genres', [])),
                ' '.join(movie.get('moods', [])),
                movie.get('description', ''),
                ' '.join(movie.get('emotions', []))
            ])
            
            features[movie_id] = {
                'text': text_features,
                'rating': movie.get('rating', 0),
                'year': movie.get('year', 0),
                'duration': movie.get('duration', 0),
                'genres': movie.get('genres', []),
                'moods': movie.get('moods', []),
                'emotions': movie.get('emotions', [])
            }
        
        return features
    
    def recommend_by_mood(self, mood_scores: Dict[str, float], 
                         num_recommendations: int = 10,
                         exclude_ids: List[int] = None) -> List[Dict]:
        """
        ムードスコアに基づいて映画を推薦
        
        Args:
            mood_scores: ムードスコアの辞書
            num_recommendations: 推薦する映画数
            exclude_ids: 除外する映画ID
            
        Returns:
            推薦映画のリスト
        """
        if not mood_scores:
            return self._get_popular_movies(num_recommendations)
        
        exclude_ids = exclude_ids or []
        movie_scores = []
        
        for movie in self.movies:
            if movie['id'] in exclude_ids:
                continue
            
            score = self._calculate_mood_match_score(movie, mood_scores)
            
            if score > 0:
                movie_scores.append({
                    'movie': movie,
                    'score': score,
                    'match_reasons': self._get_match_reasons(movie, mood_scores)
                })
        
        # スコアでソート
        movie_scores.sort(key=lambda x: x['score'], reverse=True)
        
        # 多様性を考慮した選択
        recommendations = self._apply_diversity_filter(
            movie_scores, num_recommendations
        )
        
        return recommendations
    
    def _calculate_mood_match_score(self, movie: Dict, mood_scores: Dict[str, float]) -> float:
        """映画とムードの適合度スコアを計算"""
        movie_moods = movie.get('moods', [])
        
        if not movie_moods:
            return 0.0
        
        total_score = 0.0
        matched_moods = 0
        
        for mood, score in mood_scores.items():
            if mood in movie_moods:
                weight = self.mood_weights.get(mood, 1.0)
                total_score += score * weight
                matched_moods += 1
        
        # 基本スコア
        base_score = total_score / len(mood_scores) if mood_scores else 0
        
        # ボーナス要因
        rating_bonus = (movie.get('rating', 0) - 7.0) * 0.1  # 高評価ボーナス
        match_bonus = matched_moods * 0.1  # マッチしたムード数ボーナス
        
        final_score = base_score + rating_bonus + match_bonus
        
        return max(0, final_score)
    
    def _get_match_reasons(self, movie: Dict, mood_scores: Dict[str, float]) -> List[str]:
        """マッチした理由を取得"""
        reasons = []
        movie_moods = movie.get('moods', [])
        
        for mood, score in mood_scores.items():
            if mood in movie_moods and score > 0.3:
                reasons.append(f"Matches your {mood} mood")
        
        if movie.get('rating', 0) >= 8.5:
            reasons.append("Highly rated film")
        
        if not reasons:
            reasons.append("Recommended for you")
        
        return reasons
    
    def _apply_diversity_filter(self, movie_scores: List[Dict], 
                               num_recommendations: int) -> List[Dict]:
        """多様性フィルターを適用"""
        if len(movie_scores) <= num_recommendations:
            return movie_scores
        
        selected = []
        used_genres = set()
        used_directors = set()
        
        # 高スコア映画を優先しつつ多様性を確保
        for item in movie_scores:
            movie = item['movie']
            genres = set(movie.get('genres', []))
            director = movie.get('director', '')
            
            # 多様性チェック
            genre_overlap = len(genres & used_genres) / max(len(genres), 1)
            director_used = director in used_directors
            
            # 選択条件
            if (len(selected) < num_recommendations and 
                (genre_overlap < 0.7 or len(selected) < 3) and
                (not director_used or len(selected) < 5)):
                
                selected.append(item)
                used_genres.update(genres)
                used_directors.add(director)
        
        # 足りない場合は残りから追加
        if len(selected) < num_recommendations:
            remaining = [item for item in movie_scores if item not in selected]
            selected.extend(remaining[:num_recommendations - len(selected)])
        
        return selected[:num_recommendations]
    
    def _get_popular_movies(self, num_recommendations: int) -> List[Dict]:
        """人気映画を取得（フォールバック）"""
        sorted_movies = sorted(
            self.movies, 
            key=lambda x: x.get('rating', 0), 
            reverse=True
        )
        
        recommendations = []
        for movie in sorted_movies[:num_recommendations]:
            recommendations.append({
                'movie': movie,
                'score': movie.get('rating', 0) / 10.0,
                'match_reasons': ['Popular highly-rated film']
            })
        
        return recommendations
    
    def get_movie_by_id(self, movie_id: int) -> Optional[Dict]:
        """IDで映画を取得"""
        for movie in self.movies:
            if movie['id'] == movie_id:
                return movie
        return None
    
    def search_movies(self, query: str, limit: int = 10) -> List[Dict]:
        """映画を検索"""
        query = query.lower()
        results = []
        
        for movie in self.movies:
            # タイトル、ジャンル、説明で検索
            searchable_text = ' '.join([
                movie.get('title', '').lower(),
                ' '.join(movie.get('genres', [])).lower(),
                movie.get('description', '').lower(),
                movie.get('director', '').lower(),
                ' '.join(movie.get('cast', [])).lower()
            ])
            
            if query in searchable_text:
                results.append(movie)
        
        # 関連度でソート（簡単な実装）
        results.sort(key=lambda x: x.get('rating', 0), reverse=True)
        
        return results[:limit]
    
    def get_similar_movies(self, movie_id: int, num_recommendations: int = 5) -> List[Dict]:
        """類似映画を取得"""
        target_movie = self.get_movie_by_id(movie_id)
        if not target_movie:
            return []
        
        target_genres = set(target_movie.get('genres', []))
        target_moods = set(target_movie.get('moods', []))
        
        similar_movies = []
        
        for movie in self.movies:
            if movie['id'] == movie_id:
                continue
            
            movie_genres = set(movie.get('genres', []))
            movie_moods = set(movie.get('moods', []))
            
            # 類似度計算
            genre_similarity = len(target_genres & movie_genres) / max(len(target_genres | movie_genres), 1)
            mood_similarity = len(target_moods & movie_moods) / max(len(target_moods | movie_moods), 1)
            
            similarity_score = (genre_similarity + mood_similarity) / 2
            
            if similarity_score > 0.2:
                similar_movies.append({
                    'movie': movie,
                    'score': similarity_score,
                    'match_reasons': [f'Similar to {target_movie["title"]}']
                })
        
        similar_movies.sort(key=lambda x: x['score'], reverse=True)
        return similar_movies[:num_recommendations]
    
    def get_movies_by_genre(self, genre: str, limit: int = 10) -> List[Dict]:
        """ジャンル別映画を取得"""
        genre_movies = []
        
        for movie in self.movies:
            if genre.lower() in [g.lower() for g in movie.get('genres', [])]:
                genre_movies.append(movie)
        
        # 評価順でソート
        genre_movies.sort(key=lambda x: x.get('rating', 0), reverse=True)
        
        return genre_movies[:limit]
    
    def get_mood_statistics(self) -> Dict[str, int]:
        """ムード統計を取得"""
        mood_counts = {}
        
        for movie in self.movies:
            for mood in movie.get('moods', []):
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        return dict(sorted(mood_counts.items(), key=lambda x: x[1], reverse=True))


# 使用例とテスト
if __name__ == "__main__":
    # 推薦エンジンを初期化
    engine = MovieRecommendationEngine()
    
    print(f"Loaded {len(engine.movies)} movies")
    
    # テスト用ムードスコア
    test_moods = [
        {'romantic': 1.0, 'heartwarming': 0.8},
        {'action': 1.0, 'intense': 0.9, 'adventure': 0.7},
        {'comedy': 1.0, 'feel-good': 0.8, 'light': 0.6},
        {'drama': 1.0, 'emotional': 0.9, 'contemplative': 0.5}
    ]
    
    for i, mood_scores in enumerate(test_moods):
        print(f"\n--- Test {i+1}: {mood_scores} ---")
        recommendations = engine.recommend_by_mood(mood_scores, num_recommendations=5)
        
        for j, rec in enumerate(recommendations):
            movie = rec['movie']
            score = rec['score']
            reasons = rec['match_reasons']
            
            print(f"{j+1}. {movie['title']} ({movie['year']}) - Score: {score:.2f}")
            print(f"   Genres: {', '.join(movie['genres'])}")
            print(f"   Moods: {', '.join(movie['moods'])}")
            print(f"   Reasons: {', '.join(reasons)}")
    
    # 検索テスト
    print("\n--- Search Test ---")
    search_results = engine.search_movies("love", limit=3)
    for movie in search_results:
        print(f"- {movie['title']} ({movie['year']})")
    
    # 類似映画テスト
    print("\n--- Similar Movies Test ---")
    similar = engine.get_similar_movies(1, num_recommendations=3)  # The Shawshank Redemption
    for rec in similar:
        movie = rec['movie']
        print(f"- {movie['title']} ({movie['year']}) - Similarity: {rec['score']:.2f}")
    
    # ムード統計
    print("\n--- Mood Statistics ---")
    mood_stats = engine.get_mood_statistics()
    for mood, count in list(mood_stats.items())[:10]:
        print(f"- {mood}: {count} movies")

