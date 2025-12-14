import { useEffect, useState } from 'react';
import { Clock, ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { supabase, AnalysisJob, AnalysisSummary } from '../lib/supabase';

interface AnalysisHistoryProps {
  onSelectJob: (jobId: string) => void;
  currentJobId?: string;
}

export function AnalysisHistory({ onSelectJob, currentJobId }: AnalysisHistoryProps) {
  const [jobs, setJobs] = useState<(AnalysisJob & { summary?: AnalysisSummary })[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadJobs();
  }, []);

  const loadJobs = async () => {
    const { data: jobsData } = await supabase
      .from('analysis_jobs')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(10);

    if (jobsData) {
      const jobsWithSummary = await Promise.all(
        jobsData.map(async (job) => {
          if (job.status === 'completed') {
            const { data: summary } = await supabase
              .from('analysis_summary')
              .select('*')
              .eq('job_id', job.id)
              .maybeSingle();
            return { ...job, summary };
          }
          return job;
        })
      );
      setJobs(jobsWithSummary);
    }
    setLoading(false);
  };

  if (loading) {
    return <div className="text-center text-gray-500">Loading history...</div>;
  }

  if (jobs.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-8 text-center text-gray-500">
        <Clock className="w-12 h-12 mx-auto mb-4 text-gray-400" />
        <p>No analysis history yet</p>
        <p className="text-sm mt-2">Start by analyzing a URL above</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
        <Clock className="w-6 h-6" />
        Recent Analyses
      </h3>

      <div className="space-y-3">
        {jobs.map((job) => {
          const isSelected = job.id === currentJobId;
          const summary = job.summary;

          return (
            <button
              key={job.id}
              onClick={() => onSelectJob(job.id)}
              className={`w-full text-left p-4 rounded-xl border-2 transition ${
                isSelected
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        job.status === 'completed'
                          ? 'bg-green-100 text-green-700'
                          : job.status === 'processing'
                          ? 'bg-blue-100 text-blue-700'
                          : job.status === 'failed'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {job.status}
                    </span>
                    <span className="text-xs text-gray-500">
                      {new Date(job.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 truncate mb-2">{job.url}</p>
                  {summary && (
                    <div className="flex items-center gap-3 text-xs">
                      <div className="flex items-center gap-1 text-green-600">
                        <TrendingUp className="w-3 h-3" />
                        {summary.positive_count}
                      </div>
                      <div className="flex items-center gap-1 text-red-600">
                        <TrendingDown className="w-3 h-3" />
                        {summary.negative_count}
                      </div>
                      <div className="flex items-center gap-1 text-gray-600">
                        <Minus className="w-3 h-3" />
                        {summary.neutral_count}
                      </div>
                    </div>
                  )}
                </div>
                <ExternalLink className="w-4 h-4 text-gray-400 flex-shrink-0 ml-2" />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
