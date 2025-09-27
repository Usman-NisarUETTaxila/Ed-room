import React, { useState } from 'react';
import { Send, Loader, CheckCircle, XCircle, AlertTriangle, ExternalLink, BookOpen } from 'lucide-react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

const QuizGenerator = () => {
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const difficulties = [
    { value: 'easy', label: 'Easy', description: 'Basic concepts and simple questions' },
    { value: 'medium', label: 'Medium', description: 'Intermediate level with moderate complexity' },
    { value: 'hard', label: 'Hard', description: 'Advanced concepts and challenging questions' }
  ];

  const handleGenerateQuiz = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic for the quiz');
      return;
    }

    if (topic.trim().length > 100) {
      setError('Topic must be 100 characters or less');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE}/api/quiz/generate`, {
        topic: topic.trim(),
        difficulty: difficulty,
        user_id: 'quiz_user'
      });

      if (response.data.success) {
        setResult(response.data);
        setTopic(''); // Clear the topic after successful generation
      } else {
        setError(response.data.error || 'Failed to generate quiz');
      }
    } catch (err) {
      console.error('Quiz generation error:', err);
      if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError('Failed to generate quiz. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGenerateQuiz();
    }
  };

  const resetForm = () => {
    setResult(null);
    setError(null);
    setTopic('');
    setDifficulty('medium');
  };

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-purple-100 rounded-full">
          <BookOpen className="w-6 h-6 text-purple-600" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Quiz Generator</h2>
          <p className="text-gray-600">Create interactive quizzes on Google Forms</p>
        </div>
      </div>

      {/* Quiz Generation Form */}
      {!result && (
        <div className="space-y-6">
          {/* Topic Input */}
          <div>
            <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
              Quiz Topic *
            </label>
            <input
              id="topic"
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter the topic for your quiz (e.g., World War II, Photosynthesis, JavaScript Basics)"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all"
              maxLength={100}
              disabled={isLoading}
            />
            <div className="mt-1 text-xs text-gray-500">
              {topic.length}/100 characters
            </div>
          </div>

          {/* Difficulty Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">
              Difficulty Level *
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {difficulties.map((diff) => (
                <label
                  key={diff.value}
                  className={`relative flex flex-col p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    difficulty === diff.value
                      ? 'border-purple-500 bg-purple-50'
                      : 'border-gray-200 hover:border-gray-300'
                  } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  <input
                    type="radio"
                    name="difficulty"
                    value={diff.value}
                    checked={difficulty === diff.value}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="sr-only"
                    disabled={isLoading}
                  />
                  <div className="flex items-center gap-2 mb-1">
                    <div className={`w-4 h-4 rounded-full border-2 ${
                      difficulty === diff.value
                        ? 'border-purple-500 bg-purple-500'
                        : 'border-gray-300'
                    }`}>
                      {difficulty === diff.value && (
                        <div className="w-2 h-2 bg-white rounded-full mx-auto mt-0.5"></div>
                      )}
                    </div>
                    <span className="font-medium text-gray-800">{diff.label}</span>
                  </div>
                  <span className="text-sm text-gray-600">{diff.description}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
              <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={handleGenerateQuiz}
            disabled={!topic.trim() || isLoading}
            className={`w-full flex items-center justify-center gap-2 py-3 px-6 rounded-lg font-medium transition-all ${
              !topic.trim() || isLoading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-purple-600 text-white hover:bg-purple-700 active:bg-purple-800'
            }`}
          >
            {isLoading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                Generating Quiz...
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                Generate Quiz
              </>
            )}
          </button>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-blue-700">
                <p className="font-medium mb-1">How it works:</p>
                <ul className="space-y-1 text-blue-600">
                  <li>• AI generates 20 multiple-choice questions based on your topic</li>
                  <li>• Quiz is automatically created on Google Forms</li>
                  <li>• Questions are tailored to your selected difficulty level</li>
                  <li>• You'll receive a shareable link to the quiz</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success Result */}
      {result && result.success && (
        <div className="space-y-6">
          <div className="flex items-center gap-2 p-4 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle className="w-6 h-6 text-green-500" />
            <div>
              <h3 className="font-medium text-green-800">Quiz Created Successfully!</h3>
              <p className="text-green-700">{result.message}</p>
            </div>
          </div>

          {/* Quiz Details */}
          <div className="bg-gray-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Quiz Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <span className="text-sm font-medium text-gray-600">Title:</span>
                <p className="text-gray-800">{result.quiz_info?.title}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Difficulty:</span>
                <p className="text-gray-800 capitalize">{result.quiz_info?.difficulty}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Questions:</span>
                <p className="text-gray-800">{result.quiz_info?.question_count} multiple-choice questions</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-600">Form ID:</span>
                <p className="text-gray-800 font-mono text-sm">{result.quiz_info?.form_id}</p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <a
              href={result.quiz_info?.responder_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <ExternalLink className="w-5 h-5" />
              Open Quiz in Google Forms
            </a>
            <button
              onClick={resetForm}
              className="flex items-center justify-center gap-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Create Another Quiz
            </button>
          </div>

          {/* Share Instructions */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-yellow-700">
                <p className="font-medium mb-1">Share your quiz:</p>
                <p>Copy the quiz URL from Google Forms to share with students or participants. The quiz is ready to use immediately!</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuizGenerator;
