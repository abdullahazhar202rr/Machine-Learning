import { useEffect, useState } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, Users, MessageSquare, Download } from 'lucide-react';
import { supabase, AnalysisJob, AnalysisSummary, ScrapedContent, SentimentResult } from '../lib/supabase';
import { WordCloud } from './WordCloud';
import { exportToCSV, exportToPDF } from '../utils/export';

interface DashboardProps {
  jobId: string;
}

const SENTIMENT_COLORS = {
  positive: '#10b981',
  negative: '#ef4444',
  neutral: '#6b7280',
};

export function Dashboard({ jobId }: DashboardProps) {
  const [job, setJob] = useState<AnalysisJob | null>(null);
  const [summary, setSummary] = useState<AnalysisSummary | null>(null);
  const [content, setContent] = useState<ScrapedContent[]>([]);
  const [sentiments, setSentiments] = useState<SentimentResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'positive' | 'negative' | 'neutral'>('all');

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, [jobId]);

  const loadData = async () => {
    const { data: jobData } = await supabase
      .from('analysis_jobs')
      .select('*')
      .eq('id', jobId)
      .maybeSingle();

    if (jobData) {
      setJob(jobData);

      if (jobData.status === 'completed') {
        const [summaryRes, contentRes, sentimentRes] = await Promise.all([
          supabase.from('analysis_summary').select('*').eq('job_id', jobId).maybeSingle(),
          supabase.from('scraped_content').select('*').eq('job_id', jobId),
          supabase.from('sentiment_results').select('*').eq('job_id', jobId),
        ]);

        setSummary(summaryRes.data);
        setContent(contentRes.data || []);
        setSentiments(sentimentRes.data || []);
        setLoading(false);
      }
    }
  };

  const handleExportCSV = () => {
    if (!summary || !content || !sentiments) return;
    exportToCSV(job!, summary, content, sentiments);
  };

  const handleExportPDF = () => {
    if (!summary) return;
    exportToPDF(job!, summary);
  };

  if (loading || job?.status !== 'completed') {
    return (
      <div className="flex items-center justify-center min-h-96">
        <div className="text-center">
          <div className="inline-block w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-xl font-semibold text-gray-700">
            {job?.status === 'processing' ? 'Analyzing content...' : 'Preparing analysis...'}
          </p>
          <p className="text-gray-500 mt-2">This may take a few moments</p>
        </div>
      </div>
    );
  }

  if (!summary) {
    return <div className="text-center text-gray-500">No data available</div>;
  }

  const sentimentData = [
    { name: 'Positive', value: summary.positive_count, color: SENTIMENT_COLORS.positive },
    { name: 'Negative', value: summary.negative_count, color: SENTIMENT_COLORS.negative },
    { name: 'Neutral', value: summary.neutral_count, color: SENTIMENT_COLORS.neutral },
  ];

  const filteredContent = content.filter((item) => {
    if (filter === 'all') return true;
    const sentiment = sentiments.find((s) => s.content_id === item.id);
    return sentiment?.sentiment === filter;
  });

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Analysis Results</h2>
            <p className="text-gray-600 text-sm mt-1 break-all">{job.url}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition"
            >
              <Download className="w-4 h-4" />
              CSV
            </button>
            <button
              onClick={handleExportPDF}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition"
            >
              <Download className="w-4 h-4" />
              PDF
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-600 text-sm font-semibold">Total Items</p>
                <p className="text-3xl font-bold text-blue-900">{summary.total_items}</p>
              </div>
              <MessageSquare className="w-12 h-12 text-blue-600 opacity-20" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-600 text-sm font-semibold">Positive</p>
                <p className="text-3xl font-bold text-green-900">{summary.positive_count}</p>
              </div>
              <TrendingUp className="w-12 h-12 text-green-600 opacity-20" />
            </div>
          </div>

          <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-red-600 text-sm font-semibold">Negative</p>
                <p className="text-3xl font-bold text-red-900">{summary.negative_count}</p>
              </div>
              <Users className="w-12 h-12 text-red-600 opacity-20" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Sentiment Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={sentimentData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value}`}
                outerRadius={100}
                fill="#8884d8"
                dataKey="value"
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-800 mb-4">Sentiment Timeline</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={summary.sentiment_timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="positive" stroke={SENTIMENT_COLORS.positive} strokeWidth={2} />
              <Line type="monotone" dataKey="negative" stroke={SENTIMENT_COLORS.negative} strokeWidth={2} />
              <Line type="monotone" dataKey="neutral" stroke={SENTIMENT_COLORS.neutral} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Top Keywords</h3>
        <WordCloud data={summary.top_keywords} />
      </div>

      <div className="bg-white rounded-2xl shadow-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">Top Contributors</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={summary.top_contributors.slice(0, 10)}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white rounded-2xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-800">Content Details</h3>
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-4 py-2 rounded-lg transition ${
                filter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilter('positive')}
              className={`px-4 py-2 rounded-lg transition ${
                filter === 'positive'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Positive
            </button>
            <button
              onClick={() => setFilter('negative')}
              className={`px-4 py-2 rounded-lg transition ${
                filter === 'negative'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Negative
            </button>
            <button
              onClick={() => setFilter('neutral')}
              className={`px-4 py-2 rounded-lg transition ${
                filter === 'neutral'
                  ? 'bg-gray-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Neutral
            </button>
          </div>
        </div>

        <div className="space-y-3 max-h-96 overflow-y-auto">
          {filteredContent.slice(0, 50).map((item) => {
            const sentiment = sentiments.find((s) => s.content_id === item.id);
            return (
              <div
                key={item.id}
                className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition"
              >
                <div className="flex items-start justify-between mb-2">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      sentiment?.sentiment === 'positive'
                        ? 'bg-green-100 text-green-700'
                        : sentiment?.sentiment === 'negative'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}
                  >
                    {sentiment?.sentiment}
                  </span>
                  {item.author && (
                    <span className="text-sm text-gray-500">by {item.author}</span>
                  )}
                </div>
                <p className="text-gray-700">{item.text_content}</p>
                {sentiment?.keywords && sentiment.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {sentiment.keywords.slice(0, 5).map((keyword, i) => (
                      <span key={i} className="text-xs bg-blue-50 text-blue-600 px-2 py-1 rounded">
                        {keyword}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
