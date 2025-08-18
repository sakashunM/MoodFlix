import React, { useState, useEffect } from 'react';
import { Search, Heart, Star, Clock, Users, Sparkles, Film, Zap, Brain, Target } from 'lucide-react';
import './App.css';

// API設定
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

function App() {
  const [moodText, setMoodText] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');

  // デバッグ用のuseEffect
  useEffect(() => {
    console.log('App component state updated:', {
      moodText,
      recommendationsCount: recommendations.length,
      loading,
      analysis,
      error
    });
  }, [moodText, recommendations, loading, analysis, error]);

  const handleMoodAnalysis = async () => {
    if (!moodText.trim()) {
      setError('Please enter how you\'re feeling');
      return;
    }

    setLoading(true);
    setError('');
    console.log('Starting mood analysis for:', moodText);

    try {
      const response = await fetch(`${API_BASE_URL}/api/recommend/mood`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: moodText,
          num_recommendations: 8
        })
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response not OK:', response.status, errorText);
        throw new Error(`Failed to get recommendations: ${response.status}`);
      }

      const data = await response.json();
      console.log('Received data:', data);
      
      // データの検証
      if (!data.recommendations || !Array.isArray(data.recommendations)) {
        console.error('Invalid recommendations data:', data.recommendations);
        throw new Error('Invalid recommendations data received');
      }
      
      if (!data.analysis) {
        console.error('Missing analysis data:', data);
        throw new Error('Missing analysis data');
      }

      setRecommendations(data.recommendations);
      setAnalysis(data.analysis);
      console.log('State updated successfully');
      
    } catch (err) {
      console.error('Error in handleMoodAnalysis:', err);
      setError(`Failed to analyze mood: ${err.message}`);
    } finally {
      setLoading(false);
      console.log('Analysis completed');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleMoodAnalysis();
    }
  };

  const getMoodColor = (mood) => {
    const moodColors = {
      romantic: 'bg-pink-500',
      romance: 'bg-pink-500',
      happy: 'bg-yellow-500',
      sad: 'bg-blue-500',
      excited: 'bg-orange-500',
      calm: 'bg-green-500',
      intense: 'bg-red-500',
      adventure: 'bg-purple-500',
      comedy: 'bg-lime-500',
      drama: 'bg-indigo-500',
      action: 'bg-red-600',
      heartwarming: 'bg-rose-500',
      'feel-good': 'bg-emerald-500',
      'love-story': 'bg-pink-600',
      melancholic: 'bg-slate-500',
      uplifting: 'bg-sky-500',
      energetic: 'bg-orange-600',
      calming: 'bg-teal-500',
      nostalgic: 'bg-amber-500',
      thriller: 'bg-gray-700',
      'sci-fi': 'bg-cyan-500',
      fantasy: 'bg-violet-500',
      horror: 'bg-red-800',
      documentary: 'bg-brown-500'
    };
    return moodColors[mood] || 'bg-gray-500';
  };

  const getEmotionColor = (emotion) => {
    const emotionColors = {
      joy: 'bg-yellow-400',
      sadness: 'bg-blue-400',
      anger: 'bg-red-400',
      fear: 'bg-gray-400',
      surprise: 'bg-purple-400',
      excitement: 'bg-orange-400',
      calmness: 'bg-green-400',
      nostalgia: 'bg-amber-400'
    };
    return emotionColors[emotion] || 'bg-gray-400';
  };

  const formatDuration = (minutes) => {
    // 安全な処理：minutesが数値でない場合は0として扱う
    const mins = Math.max(0, parseInt(minutes) || 0);
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    return hours > 0 ? `${hours}h ${remainingMins}m` : `${remainingMins}m`;
  };

  const getTopItems = (items, limit = 5) => {
    // 安全な処理：itemsが存在しない、またはオブジェクトでない場合は空配列を返す
    if (!items || typeof items !== 'object' || Array.isArray(items)) {
      console.warn('getTopItems: Invalid items parameter:', items);
      return [];
    }
    
    try {
      return Object.entries(items)
        .sort(([,a], [,b]) => b - a)
        .slice(0, limit)
        .filter(([,score]) => score > 0.1);
    } catch (error) {
      console.error('getTopItems: Error processing items:', error, items);
      return [];
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Header */}
      <header className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/20 to-pink-600/20"></div>
        <div className="relative container mx-auto px-6 py-12">
          <div className="text-center">
            <div className="flex items-center justify-center mb-6">
              <Brain className="w-12 h-12 text-purple-400 mr-4" />
              <h1 className="text-5xl font-bold text-white">
                Mood<span className="text-purple-400">Flix</span>
              </h1>
              <div className="ml-4 px-3 py-1 bg-gradient-to-r from-green-500 to-blue-500 text-white text-sm rounded-full font-medium">
                GPT-4.1-mini
              </div>
            </div>
            <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
              Powered by advanced AI emotion analysis. Tell us how you're feeling, and we'll recommend the perfect films for your mood.
            </p>
            
            {/* Mood Input */}
            <div className="max-w-2xl mx-auto">
              <div className="relative">
                <input
                  type="text"
                  value={moodText}
                  onChange={(e) => setMoodText(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="How are you feeling today? (e.g., 'I'm feeling excited and want something action-packed' or 'I'm sad and need something uplifting')"
                  className="w-full px-6 py-4 text-lg rounded-2xl bg-white/10 backdrop-blur-sm border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
                <button
                  onClick={handleMoodAnalysis}
                  disabled={loading}
                  className="absolute right-2 top-2 bottom-2 px-6 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {loading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  ) : (
                    <>
                      <Brain className="w-5 h-5 mr-2" />
                      Analyze
                    </>
                  )}
                </button>
              </div>
              
              {error && (
                <p className="text-red-400 mt-4 text-center">{error}</p>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* AI Analysis Results */}
      {analysis && (
        <section className="container mx-auto px-6 py-8">
          <div className="bg-white/5 backdrop-blur-sm rounded-2xl border border-white/20 p-6 mb-8">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-white mb-2 flex items-center justify-center">
                <Brain className="w-6 h-6 mr-2 text-purple-400" />
                AI Analysis Results
              </h2>
              <div className="flex items-center justify-center space-x-4 text-sm text-gray-300">
                <span className="flex items-center">
                  <Target className="w-4 h-4 mr-1 text-green-400" />
                  Confidence: {Math.round(analysis.confidence * 100)}%
                </span>
                <span className="flex items-center">
                  <Sparkles className="w-4 h-4 mr-1 text-blue-400" />
                  Method: {analysis.analysis_method}
                </span>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Detected Emotions */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <Heart className="w-5 h-5 mr-2 text-pink-400" />
                  Detected Emotions
                </h3>
                <div className="space-y-2">
                  {analysis.emotions && Object.keys(analysis.emotions).length > 0 ? (
                    getTopItems(analysis.emotions).map(([emotion, score]) => (
                      <div key={emotion} className="flex items-center">
                        <div className="flex-1">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-white capitalize">{emotion}</span>
                            <span className="text-gray-400 text-sm">{Math.round(score * 100)}%</span>
                          </div>
                          <div className="w-full bg-gray-700 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${getEmotionColor(emotion)}`}
                              style={{ width: `${score * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-400 text-sm">No specific emotions detected</p>
                  )}
                </div>
              </div>

              {/* Detected Moods */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
                  <Film className="w-5 h-5 mr-2 text-purple-400" />
                  Movie Moods
                </h3>
                <div className="space-y-2">
                  {analysis.moods && Object.keys(analysis.moods).length > 0 ? (
                    getTopItems(analysis.moods).map(([mood, score]) => (
                      <div key={mood} className="flex items-center">
                        <div className="flex-1">
                          <div className="flex justify-between items-center mb-1">
                            <span className="text-white capitalize">{mood.replace('-', ' ')}</span>
                            <span className="text-gray-400 text-sm">{Math.round(score * 100)}%</span>
                          </div>
                          <div className="w-full bg-gray-700 rounded-full h-2">
                            <div 
                              className={`h-2 rounded-full ${getMoodColor(mood)}`}
                              style={{ width: `${score * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-400 text-sm">No specific moods detected</p>
                  )}
                </div>
              </div>
            </div>

            {/* AI Reasoning */}
            {analysis.reasoning && (
              <div className="mt-6 p-4 bg-white/5 rounded-xl border border-white/10">
                <h4 className="text-white font-medium mb-2 flex items-center">
                  <Sparkles className="w-4 h-4 mr-2 text-yellow-400" />
                  AI Reasoning
                </h4>
                <p className="text-gray-300 text-sm leading-relaxed">{analysis.reasoning}</p>
              </div>
            )}

            {/* Context Analysis */}
            {analysis.context && typeof analysis.context === 'object' && Object.keys(analysis.context).length > 0 && (
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(analysis.context).map(([key, value]) => (
                  <div key={key} className="text-center">
                    <div className="text-gray-400 text-xs uppercase tracking-wide mb-1">
                      {key.replace('_', ' ')}
                    </div>
                    <div className="text-white font-medium capitalize">{value}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      )}

      {/* Movie Recommendations */}
      {recommendations.length > 0 ? (
        <section className="container mx-auto px-6 py-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">
              Perfect Movies for Your Mood
            </h2>
            <p className="text-gray-300">
              Based on AI analysis of your feelings, here are {recommendations.length} movies we think you'll love
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {recommendations.map((item) => {
              // データ構造を自動判別
              const movie = item.movie || item;
              
              return (
                <div
                  key={item.id || movie.id}
                  className="bg-white/10 backdrop-blur-sm rounded-2xl overflow-hidden border border-white/20 hover:border-purple-500/50 transition-all duration-300 hover:transform hover:scale-105 group"
                >
                  {/* Movie Poster */}
                  <div className="aspect-[2/3] relative bg-gradient-to-br from-purple-600/20 to-pink-600/20">
                    {movie.poster_url ? (
                      <img 
                        src={movie.poster_url} 
                        alt={movie.title || movie.original_title || 'Movie poster'}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.nextSibling.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div className={`absolute inset-0 flex items-center justify-center ${movie.poster_url ? 'hidden' : 'flex'}`}>
                      <Film className="w-16 h-16 text-white/50" />
                    </div>
                  </div>
                  
                  <div className="p-6">
                    <h3 className="text-xl font-bold text-white mb-2 group-hover:text-purple-400 transition-colors">
                      {movie.title || movie.original_title || 'Unknown'}
                    </h3>
                    
                    <div className="flex items-center text-gray-400 text-sm mb-3">
                      <span>{movie.release_date?.split('-')[0] || 'Unknown'}</span>
                      <span className="mx-2">•</span>
                      <Clock className="w-4 h-4 mr-1" />
                      <span>{movie.runtime ? `${movie.runtime}m` : '0m'}</span>
                    </div>
                    
                    <div className="flex items-center mb-3">
                      <Star className="w-4 h-4 text-yellow-500 mr-1" />
                      <span className="text-white font-medium">{movie.vote_average || 'N/A'}</span>
                      <span className="text-gray-400 ml-2">IMDb</span>
                      <div className="ml-auto">
                        <span className="text-purple-400 text-sm font-medium">
                          {item.score || 0}% match
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex flex-wrap gap-1 mb-4">
                      {movie.genres && Array.isArray(movie.genres) && movie.genres.slice(0, 2).map((genre) => (
                        <span
                          key={genre}
                          className="px-2 py-1 bg-white/20 text-white text-xs rounded-full"
                        >
                          {genre}
                        </span>
                      ))}
                    </div>
                    
                    <p className="text-gray-300 text-sm mb-4 line-clamp-3">
                      {movie.overview || 'No description available'}
                    </p>
                    
                    <div className="mb-4">
                      <p className="text-purple-400 text-sm font-medium mb-2 flex items-center">
                        <Zap className="w-4 h-4 mr-1" />
                        Why this matches:
                      </p>
                      <ul className="text-gray-300 text-xs space-y-1">
                        {item.match_reasons && Array.isArray(item.match_reasons) && item.match_reasons.slice(0, 2).map((reason, index) => (
                          <li key={index} className="flex items-start">
                            <span className="text-purple-400 mr-2">•</span>
                            {reason}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    {item.streaming_services && Array.isArray(item.streaming_services) && item.streaming_services.length > 0 && (
                      <div className="border-t border-white/20 pt-4">
                        <p className="text-gray-400 text-xs mb-2">Available on:</p>
                        <div className="flex flex-wrap gap-2">
                          {item.streaming_services.slice(0, 2).map((service) => (
                            <span
                              key={service}
                              className="px-2 py-1 bg-gradient-to-r from-purple-600/20 to-pink-600/20 text-white text-xs rounded-lg border border-purple-500/30"
                            >
                              {service}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ) : analysis && (
        <section className="container mx-auto px-6 py-8">
          <div className="text-center">
            <div className="bg-white/5 backdrop-blur-sm rounded-2xl border border-white/20 p-8">
              <Film className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-xl font-bold text-white mb-2">No Movies Found</h3>
              <p className="text-gray-400 mb-4">
                We couldn't find movies matching your current mood. This might be due to:
              </p>
              <ul className="text-gray-400 text-sm space-y-2 text-left max-w-md mx-auto">
                <li>• Limited movie database access</li>
                <li>• Specific mood requirements</li>
                <li>• API service limitations</li>
              </ul>
              <p className="text-gray-300 mt-4">
                Try describing your mood differently or check back later!
              </p>
            </div>
          </div>
        </section>
      )}

      {/* Empty State */}
      {recommendations.length === 0 && !loading && (
        <section className="container mx-auto px-6 py-16">
          <div className="text-center">
            <div className="flex items-center justify-center mb-8">
              <Brain className="w-24 h-24 text-gray-600 mr-4" />
              <Film className="w-24 h-24 text-gray-600" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-4">
              Ready to Find Your Perfect Movie?
            </h2>
            <p className="text-gray-400 max-w-md mx-auto mb-6">
              Tell us how you're feeling, and our advanced AI will analyze your emotions and recommend movies that perfectly match your current mood.
            </p>
            <div className="flex items-center justify-center space-x-6 text-sm text-gray-500">
              <div className="flex items-center">
                <Brain className="w-4 h-4 mr-2 text-purple-400" />
                <span>GPT-4.1-mini Analysis</span>
              </div>
              <div className="flex items-center">
                <Target className="w-4 h-4 mr-2 text-green-400" />
                <span>95%+ Accuracy</span>
              </div>
              <div className="flex items-center">
                <Sparkles className="w-4 h-4 mr-2 text-yellow-400" />
                <span>Personalized Results</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="container mx-auto px-6 py-12 text-center">
        <div className="border-t border-white/20 pt-8">
          <p className="text-gray-400">
            Powered by GPT-4.1-mini emotion analysis and intelligent movie recommendations
          </p>
          <div className="flex items-center justify-center mt-4 text-purple-400">
            <Heart className="w-4 h-4 mr-2" />
            <span className="text-sm">Made with love for movie enthusiasts</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;

