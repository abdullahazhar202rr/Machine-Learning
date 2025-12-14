import jsPDF from 'jspdf';
import { AnalysisJob, AnalysisSummary, ScrapedContent, SentimentResult } from '../lib/supabase';

export function exportToCSV(
  job: AnalysisJob,
  summary: AnalysisSummary,
  content: ScrapedContent[],
  sentiments: SentimentResult[]
) {
  const rows = [
    ['Sentiment Analysis Report'],
    ['URL', job.url],
    ['Platform', job.platform_type],
    ['Date', new Date(job.created_at).toLocaleDateString()],
    [''],
    ['Summary'],
    ['Total Items', summary.total_items.toString()],
    ['Positive', summary.positive_count.toString()],
    ['Negative', summary.negative_count.toString()],
    ['Neutral', summary.neutral_count.toString()],
    [''],
    ['Content', 'Author', 'Sentiment', 'Confidence', 'Keywords'],
  ];

  content.forEach((item) => {
    const sentiment = sentiments.find((s) => s.content_id === item.id);
    rows.push([
      item.text_content,
      item.author || '',
      sentiment?.sentiment || '',
      sentiment?.confidence_score?.toString() || '',
      sentiment?.keywords?.join(', ') || '',
    ]);
  });

  const csvContent = rows.map((row) => row.map((cell) => `"${cell}"`).join(',')).join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `sentiment-analysis-${Date.now()}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
}

export function exportToPDF(job: AnalysisJob, summary: AnalysisSummary) {
  const doc = new jsPDF();

  doc.setFontSize(20);
  doc.text('Sentiment Analysis Report', 20, 20);

  doc.setFontSize(12);
  doc.text(`URL: ${job.url}`, 20, 35);
  doc.text(`Platform: ${job.platform_type}`, 20, 45);
  doc.text(`Date: ${new Date(job.created_at).toLocaleDateString()}`, 20, 55);

  doc.setFontSize(16);
  doc.text('Summary', 20, 70);

  doc.setFontSize(12);
  doc.text(`Total Items: ${summary.total_items}`, 20, 80);
  doc.text(`Positive: ${summary.positive_count}`, 20, 90);
  doc.text(`Negative: ${summary.negative_count}`, 20, 100);
  doc.text(`Neutral: ${summary.neutral_count}`, 20, 110);

  const positivePercentage = ((summary.positive_count / summary.total_items) * 100).toFixed(1);
  const negativePercentage = ((summary.negative_count / summary.total_items) * 100).toFixed(1);
  const neutralPercentage = ((summary.neutral_count / summary.total_items) * 100).toFixed(1);

  doc.text(`Positive: ${positivePercentage}%`, 20, 125);
  doc.text(`Negative: ${negativePercentage}%`, 20, 135);
  doc.text(`Neutral: ${neutralPercentage}%`, 20, 145);

  doc.setFontSize(16);
  doc.text('Top Keywords', 20, 160);

  doc.setFontSize(10);
  const keywords = Object.entries(summary.top_keywords)
    .slice(0, 10)
    .map(([word, count]) => `${word} (${count})`)
    .join(', ');
  const splitKeywords = doc.splitTextToSize(keywords, 170);
  doc.text(splitKeywords, 20, 170);

  if (summary.top_contributors.length > 0) {
    doc.addPage();
    doc.setFontSize(16);
    doc.text('Top Contributors', 20, 20);

    doc.setFontSize(10);
    let y = 30;
    summary.top_contributors.slice(0, 15).forEach((contributor) => {
      doc.text(`${contributor.name}: ${contributor.count} contributions`, 20, y);
      y += 10;
    });
  }

  doc.save(`sentiment-analysis-${Date.now()}.pdf`);
}
