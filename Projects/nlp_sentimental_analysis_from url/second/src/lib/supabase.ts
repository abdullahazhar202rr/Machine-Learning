import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface AnalysisJob {
  id: string;
  user_id: string;
  url: string;
  platform_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  error_message?: string;
}

export interface ScrapedContent {
  id: string;
  job_id: string;
  content_type: string;
  text_content: string;
  author?: string;
  timestamp?: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface SentimentResult {
  id: string;
  job_id: string;
  content_id: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  confidence_score: number;
  keywords: string[];
  created_at: string;
}

export interface AnalysisSummary {
  id: string;
  job_id: string;
  total_items: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  top_keywords: Record<string, number>;
  sentiment_timeline: Array<{
    date: string;
    positive: number;
    negative: number;
    neutral: number;
  }>;
  top_contributors: Array<{
    name: string;
    count: number;
  }>;
  created_at: string;
}
