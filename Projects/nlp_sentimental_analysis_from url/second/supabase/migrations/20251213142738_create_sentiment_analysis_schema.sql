/*
  # Sentiment Analysis Platform Schema

  1. New Tables
    - `analysis_jobs`
      - `id` (uuid, primary key)
      - `user_id` (uuid, references auth.users)
      - `url` (text, the target URL to analyze)
      - `platform_type` (text, detected platform: youtube, twitter, website, etc.)
      - `status` (text, job status: pending, processing, completed, failed)
      - `created_at` (timestamptz)
      - `completed_at` (timestamptz, nullable)
      - `error_message` (text, nullable)
    
    - `scraped_content`
      - `id` (uuid, primary key)
      - `job_id` (uuid, references analysis_jobs)
      - `content_type` (text, type: comment, post, tweet, review, etc.)
      - `text_content` (text, extracted text)
      - `author` (text, nullable)
      - `timestamp` (timestamptz, nullable)
      - `metadata` (jsonb, additional data like likes, replies, etc.)
      - `created_at` (timestamptz)
    
    - `sentiment_results`
      - `id` (uuid, primary key)
      - `job_id` (uuid, references analysis_jobs)
      - `content_id` (uuid, references scraped_content)
      - `sentiment` (text, positive, negative, or neutral)
      - `confidence_score` (decimal, 0-1)
      - `keywords` (text[], extracted keywords)
      - `created_at` (timestamptz)
    
    - `analysis_summary`
      - `id` (uuid, primary key)
      - `job_id` (uuid, unique, references analysis_jobs)
      - `total_items` (integer)
      - `positive_count` (integer)
      - `negative_count` (integer)
      - `neutral_count` (integer)
      - `top_keywords` (jsonb, word frequencies)
      - `sentiment_timeline` (jsonb, time-based trends)
      - `top_contributors` (jsonb, most active authors)
      - `created_at` (timestamptz)

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users to manage their own data
*/

CREATE TABLE IF NOT EXISTS analysis_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  url text NOT NULL,
  platform_type text DEFAULT 'website',
  status text DEFAULT 'pending',
  created_at timestamptz DEFAULT now(),
  completed_at timestamptz,
  error_message text
);

CREATE TABLE IF NOT EXISTS scraped_content (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid REFERENCES analysis_jobs(id) ON DELETE CASCADE,
  content_type text DEFAULT 'comment',
  text_content text NOT NULL,
  author text,
  timestamp timestamptz,
  metadata jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sentiment_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid REFERENCES analysis_jobs(id) ON DELETE CASCADE,
  content_id uuid REFERENCES scraped_content(id) ON DELETE CASCADE,
  sentiment text NOT NULL,
  confidence_score decimal(3,2) DEFAULT 0.5,
  keywords text[] DEFAULT '{}',
  created_at timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analysis_summary (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid UNIQUE REFERENCES analysis_jobs(id) ON DELETE CASCADE,
  total_items integer DEFAULT 0,
  positive_count integer DEFAULT 0,
  negative_count integer DEFAULT 0,
  neutral_count integer DEFAULT 0,
  top_keywords jsonb DEFAULT '{}',
  sentiment_timeline jsonb DEFAULT '[]',
  top_contributors jsonb DEFAULT '[]',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE analysis_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraped_content ENABLE ROW LEVEL SECURITY;
ALTER TABLE sentiment_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_summary ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own analysis jobs"
  ON analysis_jobs FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create own analysis jobs"
  ON analysis_jobs FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own analysis jobs"
  ON analysis_jobs FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own analysis jobs"
  ON analysis_jobs FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view scraped content from own jobs"
  ON scraped_content FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM analysis_jobs
      WHERE analysis_jobs.id = scraped_content.job_id
      AND analysis_jobs.user_id = auth.uid()
    )
  );

CREATE POLICY "Service can insert scraped content"
  ON scraped_content FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Users can view sentiment results from own jobs"
  ON sentiment_results FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM analysis_jobs
      WHERE analysis_jobs.id = sentiment_results.job_id
      AND analysis_jobs.user_id = auth.uid()
    )
  );

CREATE POLICY "Service can insert sentiment results"
  ON sentiment_results FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Users can view analysis summary from own jobs"
  ON analysis_summary FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM analysis_jobs
      WHERE analysis_jobs.id = analysis_summary.job_id
      AND analysis_jobs.user_id = auth.uid()
    )
  );

CREATE POLICY "Service can insert analysis summary"
  ON analysis_summary FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Service can update analysis summary"
  ON analysis_summary FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_analysis_jobs_user_id ON analysis_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scraped_content_job_id ON scraped_content(job_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_results_job_id ON sentiment_results(job_id);
CREATE INDEX IF NOT EXISTS idx_analysis_summary_job_id ON analysis_summary(job_id);