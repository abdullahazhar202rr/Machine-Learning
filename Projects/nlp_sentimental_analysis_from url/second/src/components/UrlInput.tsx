import { useState } from 'react';
import { Link2, Sparkles } from 'lucide-react';
import { supabase } from '../lib/supabase';
import { useAuth } from '../contexts/AuthContext';

interface UrlInputProps {
  onAnalysisStart: (jobId: string) => void;
}

export function UrlInput({ onAnalysisStart }: UrlInputProps) {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { user } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError('');

    try {
      const { data: job, error: jobError } = await supabase
        .from('analysis_jobs')
        .insert({
          user_id: user?.id,
          url: url.trim(),
          status: 'pending',
        })
        .select()
        .single();

      if (jobError) throw jobError;

      const response = await fetch(
        `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/analyze-url`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ url: url.trim(), jobId: job.id }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to start analysis');
      }

      onAnalysisStart(job.id);
      setUrl('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start analysis');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-3 rounded-xl">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Analyze Any URL</h2>
          <p className="text-gray-600 text-sm">Enter a website, YouTube, Twitter, or any web page</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Link2 className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com or youtube.com/watch?v=..."
              className="w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition text-lg"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading || !url.trim()}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-semibold px-8 py-4 rounded-xl transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
            {error}
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <span className="text-sm text-gray-500">Try:</span>
          {[
            'https://news.ycombinator.com',
            'https://www.reddit.com/r/technology',
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
          ].map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setUrl(example)}
              className="text-sm text-blue-600 hover:text-blue-700 hover:underline"
            >
              {example.replace('https://', '').substring(0, 30)}...
            </button>
          ))}
        </div>
      </form>
    </div>
  );
}
