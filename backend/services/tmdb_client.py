"""
TMDb API Client
Handles all interactions with The Movie Database API
"""

import time
import requests
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from cachetools import TTLCache
import redis
import json
from config import get_config

logger = logging.getLogger(__name__)
config = get_config()

@dataclass
class MovieData:
    """Movie data structure"""
    id: int
    title: str
    original_title: str
    overview: str
    release_date: str
    poster_path: Optional[str]
    backdrop_path: Optional[str]
    genre_ids: List[int]
    genres: List[str]
    vote_average: float
    vote_count: int
    popularity: float
    runtime: Optional[int]
    adult: bool
    original_language: str
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'original_title': self.original_title,
            'overview': self.overview,
            'release_date': self.release_date,
            'poster_path': self.poster_path,
            'backdrop_path': self.backdrop_path,
            'genre_ids': self.genre_ids,
            'genres': self.genres,
            'vote_average': self.vote_average,
            'vote_count': self.vote_count,
            'popularity': self.popularity,
            'runtime': self.runtime,
            'adult': self.adult,
            'original_language': self.original_language,
            'poster_url': config.get_tmdb_image_url(self.poster_path),
            'backdrop_url': config.get_tmdb_image_url(self.backdrop_path, 'w1280')
        }

class TMDbClient:
    """TMDb API client with caching and rate limiting"""
    
    def __init__(self):
        self.api_key = config.TMDB_API_KEY
        self.base_url = config.TMDB_BASE_URL
        self.session = requests.Session()
        # APIキーはクエリパラメータとして渡す（Bearer認証ではない）
        self.session.headers.update({
            'accept': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.05  # 50ms between requests
        
        # Cache setup
        try:
            self.redis_client = redis.from_url(config.REDIS_URL)
            self.redis_client.ping()  # Test connection
            self.use_redis = True
            logger.info("Connected to Redis for caching")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory cache: {e}")
            self.use_redis = False
            self.memory_cache = TTLCache(maxsize=1000, ttl=config.CACHE_TTL_SECONDS)
        
        # Genre mapping cache
        self.genres_cache = None
        # Force reload genres on initialization
        self._load_genres(force_reload=True)
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return ":".join(key_parts)
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get data from cache"""
        try:
            if self.use_redis:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    def _set_cache(self, key: str, data: Any, ttl: Optional[int] = None):
        """Set data in cache"""
        try:
            if self.use_redis:
                ttl = ttl or config.CACHE_TTL_SECONDS
                self.redis_client.setex(key, ttl, json.dumps(data))
            else:
                self.memory_cache[key] = data
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make API request with error handling"""
        self._rate_limit()
        
        url = f"{self.base_url}/{endpoint}"
        params = params or {}
        
        # APIキーをクエリパラメータとして追加
        params['api_key'] = self.api_key
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 429:
                # Rate limit hit, wait and retry
                retry_after = int(response.headers.get('Retry-After', 1))
                logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
                time.sleep(retry_after)
                return self._make_request(endpoint, params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"TMDb API request failed: {e}")
            raise
    
    def _load_genres(self, force_reload=False):
        """Load genre mapping"""
        cache_key = "tmdb:genres"
        
        if not force_reload:
            cached_genres = self._get_from_cache(cache_key)
            if cached_genres:
                self.genres_cache = cached_genres
                logger.info(f"Loaded {len(self.genres_cache)} genres from cache")
                return
        
        try:
            logger.info("Loading genres from TMDB API...")
            data = self._make_request('genre/movie/list', {'language': 'ja-JP'})
            self.genres_cache = {genre['id']: genre['name'] for genre in data['genres']}
            self._set_cache(cache_key, self.genres_cache, ttl=7*24*3600)  # Cache for 1 week
            logger.info(f"Loaded {len(self.genres_cache)} genres from API")
            logger.debug(f"Genre mapping: {self.genres_cache}")
        except Exception as e:
            logger.error(f"Failed to load genres: {e}")
            self.genres_cache = {}
            # Fallback to basic genre mapping
            self.genres_cache = {
                28: "アクション", 12: "アドベンチャー", 16: "アニメーション", 35: "コメディ",
                80: "犯罪", 99: "ドキュメンタリー", 18: "ドラマ", 10751: "ファミリー",
                14: "ファンタジー", 36: "歴史", 27: "ホラー", 10402: "ミュージカル",
                9648: "ミステリー", 10749: "ロマンス", 878: "SF", 10770: "テレビ映画",
                53: "スリラー", 10752: "戦争", 37: "西部劇"
            }
            logger.info("Using fallback genre mapping")
    
    def _map_genres(self, genre_ids: List[int]) -> List[str]:
        """Map genre IDs to names"""
        if not self.genres_cache:
            logger.warning("No genre cache available")
            return []
        
        mapped_genres = []
        for gid in genre_ids:
            genre_name = self.genres_cache.get(gid, f"Unknown({gid})")
            mapped_genres.append(genre_name)
            if genre_name.startswith("Unknown"):
                logger.warning(f"Unknown genre ID: {gid}")
        
        logger.debug(f"Mapped genres {genre_ids} -> {mapped_genres}")
        return mapped_genres
    
    def search_movies(self, query: str, **kwargs) -> List[MovieData]:
        """Search for movies"""
        cache_key = self._get_cache_key("tmdb:search", query=query, **kwargs)
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result:
            return [MovieData(**movie) for movie in cached_result]
        
        params = {
            'query': query,
            'include_adult': False,
            'language': 'ja-JP',
            'page': 1,
            **kwargs
        }
        
        try:
            data = self._make_request('search/movie', params)
            movies = []
            
            for movie_data in data.get('results', []):
                movie = MovieData(
                    id=movie_data['id'],
                    title=movie_data['title'],
                    original_title=movie_data['original_title'],
                    overview=movie_data['overview'],
                    release_date=movie_data.get('release_date', ''),
                    poster_path=movie_data.get('poster_path'),
                    backdrop_path=movie_data.get('backdrop_path'),
                    genre_ids=movie_data.get('genre_ids', []),
                    genres=self._map_genres(movie_data.get('genre_ids', [])),
                    vote_average=movie_data.get('vote_average', 0),
                    vote_count=movie_data.get('vote_count', 0),
                    popularity=movie_data.get('popularity', 0),
                    runtime=None,  # Not available in search results
                    adult=movie_data.get('adult', False),
                    original_language=movie_data.get('original_language', ''),
                    poster_url=config.get_tmdb_image_url(movie_data.get('poster_path')),
                    backdrop_url=config.get_tmdb_image_url(movie_data.get('backdrop_path'), 'w1280')
                )
                movies.append(movie)
            
            # Cache results
            cache_data = [movie.to_dict() for movie in movies]
            self._set_cache(cache_key, cache_data, ttl=3600)  # Cache for 1 hour
            
            logger.info(f"Found {len(movies)} movies for query: {query}")
            return movies
            
        except Exception as e:
            logger.error(f"Movie search failed: {e}")
            return []
    
    def get_movie_details(self, movie_id: int) -> Optional[MovieData]:
        """Get detailed movie information"""
        cache_key = self._get_cache_key("tmdb:movie", id=movie_id)
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result:
            return MovieData(**cached_result)
        
        try:
            data = self._make_request(f'movie/{movie_id}', {'language': 'ja-JP'})
            
            movie = MovieData(
                id=data['id'],
                title=data['title'],
                original_title=data['original_title'],
                overview=data['overview'],
                release_date=data.get('release_date', ''),
                poster_path=data.get('poster_path'),
                backdrop_path=data.get('backdrop_path'),
                genre_ids=[genre['id'] for genre in data.get('genres', [])],
                genres=[genre['name'] for genre in data.get('genres', [])],
                vote_average=data.get('vote_average', 0),
                vote_count=data.get('vote_count', 0),
                popularity=data.get('popularity', 0),
                runtime=data.get('runtime'),
                adult=data.get('adult', False),
                original_language=data.get('original_language', ''),
                poster_url=config.get_tmdb_image_url(data.get('poster_path')),
                backdrop_url=config.get_tmdb_image_url(data.get('backdrop_path'), 'w1280')
            )
            
            # Cache result
            self._set_cache(cache_key, movie.to_dict())
            
            logger.info(f"Retrieved details for movie: {movie.title}")
            return movie
            
        except Exception as e:
            logger.error(f"Failed to get movie details for ID {movie_id}: {e}")
            return None
    
    def discover_movies(self, **kwargs) -> List[MovieData]:
        """Discover movies with filters"""
        cache_key = self._get_cache_key("tmdb:discover", **kwargs)
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result:
            return [MovieData(**movie) for movie in cached_result]
        
        params = {
            'include_adult': False,
            'language': 'ja-JP',
            'page': 1,
            'sort_by': 'popularity.desc',
            **kwargs
        }
        
        try:
            data = self._make_request('discover/movie', params)
            movies = []
            
            for movie_data in data.get('results', []):
                movie = MovieData(
                    id=movie_data['id'],
                    title=movie_data['title'],
                    original_title=movie_data['original_title'],
                    overview=movie_data['overview'],
                    release_date=movie_data.get('release_date', ''),
                    poster_path=movie_data.get('poster_path'),
                    backdrop_path=movie_data.get('backdrop_path'),
                    genre_ids=movie_data.get('genre_ids', []),
                    genres=self._map_genres(movie_data.get('genre_ids', [])),
                    vote_average=movie_data.get('vote_average', 0),
                    vote_count=movie_data.get('vote_count', 0),
                    popularity=movie_data.get('popularity', 0),
                    runtime=None,
                    adult=movie_data.get('adult', False),
                    original_language=movie_data.get('original_language', ''),
                    poster_url=config.get_tmdb_image_url(movie_data.get('poster_path')),
                    backdrop_url=config.get_tmdb_image_url(movie_data.get('backdrop_path'), 'w1280')
                )
                movies.append(movie)
            
            # Cache results
            cache_data = [movie.to_dict() for movie in movies]
            self._set_cache(cache_key, cache_data, ttl=3600)
            
            logger.info(f"Discovered {len(movies)} movies")
            return movies
            
        except Exception as e:
            logger.error(f"Movie discovery failed: {e}")
            return []
    
    def get_popular_movies(self, page: int = 1) -> List[MovieData]:
        """Get popular movies"""
        return self.discover_movies(page=page, sort_by='popularity.desc')
    
    def get_top_rated_movies(self, page: int = 1) -> List[MovieData]:
        """Get top rated movies"""
        return self.discover_movies(page=page, sort_by='vote_average.desc', 
                                  **{'vote_count.gte': 1000})
    
    def health_check(self) -> bool:
        """Check if TMDb API is accessible"""
        try:
            self._make_request('configuration')
            return True
        except Exception:
            return False

