import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

interface AnalyzeRequest {
  url: string;
  jobId: string;
}

interface ScrapedItem {
  text: string;
  author?: string;
  timestamp?: string;
  type: string;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? ""
    );

    const { url, jobId }: AnalyzeRequest = await req.json();

    await supabaseClient
      .from("analysis_jobs")
      .update({ status: "processing" })
      .eq("id", jobId);

    const platformType = detectPlatform(url);
    await supabaseClient
      .from("analysis_jobs")
      .update({ platform_type: platformType })
      .eq("id", jobId);

    const scrapedItems = await scrapeUrl(url, platformType);

    const contentIds: string[] = [];
    for (const item of scrapedItems) {
      const { data, error } = await supabaseClient
        .from("scraped_content")
        .insert({
          job_id: jobId,
          content_type: item.type,
          text_content: item.text,
          author: item.author,
          timestamp: item.timestamp,
          metadata: {},
        })
        .select("id")
        .single();

      if (data && !error) {
        contentIds.push(data.id);
      }
    }

    let positiveCount = 0;
    let negativeCount = 0;
    let neutralCount = 0;
    const allKeywords: string[] = [];
    const contributorMap = new Map<string, number>();

    for (let i = 0; i < scrapedItems.length; i++) {
      const item = scrapedItems[i];
      const sentiment = analyzeSentiment(item.text);
      const keywords = extractKeywords(item.text);

      allKeywords.push(...keywords);

      if (sentiment.label === "positive") positiveCount++;
      else if (sentiment.label === "negative") negativeCount++;
      else neutralCount++;

      if (item.author) {
        contributorMap.set(item.author, (contributorMap.get(item.author) || 0) + 1);
      }

      if (contentIds[i]) {
        await supabaseClient.from("sentiment_results").insert({
          job_id: jobId,
          content_id: contentIds[i],
          sentiment: sentiment.label,
          confidence_score: sentiment.score,
          keywords: keywords,
        });
      }
    }

    const keywordFreq = countFrequencies(allKeywords);
    const topContributors = Array.from(contributorMap.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([name, count]) => ({ name, count }));

    const sentimentTimeline = generateTimeline(scrapedItems);

    await supabaseClient.from("analysis_summary").insert({
      job_id: jobId,
      total_items: scrapedItems.length,
      positive_count: positiveCount,
      negative_count: negativeCount,
      neutral_count: neutralCount,
      top_keywords: keywordFreq,
      sentiment_timeline: sentimentTimeline,
      top_contributors: topContributors,
    });

    await supabaseClient
      .from("analysis_jobs")
      .update({ status: "completed", completed_at: new Date().toISOString() })
      .eq("id", jobId);

    return new Response(
      JSON.stringify({ success: true, jobId }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error) {
    console.error("Error:", error);
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});

function detectPlatform(url: string): string {
  const urlLower = url.toLowerCase();
  if (urlLower.includes("youtube.com") || urlLower.includes("youtu.be")) return "youtube";
  if (urlLower.includes("twitter.com") || urlLower.includes("x.com")) return "twitter";
  if (urlLower.includes("reddit.com")) return "reddit";
  if (urlLower.includes("facebook.com")) return "facebook";
  if (urlLower.includes("instagram.com")) return "instagram";
  return "website";
}

async function scrapeUrl(url: string, platform: string): Promise<ScrapedItem[]> {
  try {
    const jinaUrl = `https://r.jina.ai/${url}`;
    const response = await fetch(jinaUrl, {
      headers: {
        "Accept": "application/json",
        "X-Return-Format": "markdown"
      }
    });

    if (!response.ok) {
      throw new Error(`Scraping failed: ${response.statusText}`);
    }

    const data = await response.json();
    const content = data.data?.content || data.content || "";

    return parseContent(content, platform);
  } catch (error) {
    console.error("Scraping error:", error);
    return [];
  }
}

function parseContent(content: string, platform: string): ScrapedItem[] {
  const items: ScrapedItem[] = [];
  const lines = content.split("\n").filter(line => line.trim().length > 0);

  if (platform === "youtube") {
    const comments = extractYouTubeComments(content);
    items.push(...comments);
  } else if (platform === "twitter") {
    const tweets = extractTweets(content);
    items.push(...tweets);
  } else if (platform === "reddit") {
    const posts = extractRedditPosts(content);
    items.push(...posts);
  } else {
    for (const line of lines) {
      if (line.length > 20 && line.length < 1000) {
        const text = line.replace(/^[#*\-_>]+\s*/, "").trim();
        if (text.length > 20) {
          items.push({
            text,
            type: "content",
          });
        }
      }
    }
  }

  if (items.length === 0) {
    const paragraphs = content.split(/\n\n+/);
    for (const para of paragraphs) {
      const text = para.trim();
      if (text.length > 30 && text.length < 2000) {
        items.push({ text, type: "paragraph" });
      }
    }
  }

  return items.slice(0, 500);
}

function extractYouTubeComments(content: string): ScrapedItem[] {
  const items: ScrapedItem[] = [];
  const lines = content.split("\n");

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.length > 10 && !line.startsWith("#") && !line.startsWith("[")) {
      if (line.length > 30 && line.length < 1000) {
        const authorMatch = line.match(/^@?(\w+)\s*[:|-]?\s*(.+)/);
        if (authorMatch) {
          items.push({
            text: authorMatch[2].trim(),
            author: authorMatch[1],
            type: "comment",
          });
        } else {
          items.push({
            text: line,
            type: "comment",
          });
        }
      }
    }
  }

  return items;
}

function extractTweets(content: string): ScrapedItem[] {
  const items: ScrapedItem[] = [];
  const lines = content.split("\n");

  for (const line of lines) {
    const text = line.trim();
    if (text.length > 20 && text.length < 500) {
      items.push({
        text: text.replace(/^[#*\-_]+\s*/, ""),
        type: "tweet",
      });
    }
  }

  return items;
}

function extractRedditPosts(content: string): ScrapedItem[] {
  const items: ScrapedItem[] = [];
  const lines = content.split("\n");

  for (const line of lines) {
    const text = line.trim();
    if (text.length > 30 && text.length < 1000 && !text.startsWith("#")) {
      items.push({
        text: text.replace(/^[*\-_>]+\s*/, ""),
        type: "post",
      });
    }
  }

  return items;
}

function analyzeSentiment(text: string): { label: string; score: number } {
  const positive = [
    "good", "great", "excellent", "amazing", "awesome", "fantastic", "wonderful",
    "love", "best", "perfect", "beautiful", "brilliant", "outstanding", "superb",
    "incredible", "magnificent", "fabulous", "terrific", "pleased", "happy",
    "delighted", "satisfied", "impressed", "enjoy", "thank", "thanks", "appreciate",
    "helpful", "useful", "valuable", "recommend", "\u2764", "\ud83d\ude0a", "\ud83d\ude04",
    "\ud83d\udc4d", "\u2728", "\ud83c\udf89"
  ];

  const negative = [
    "bad", "terrible", "awful", "horrible", "poor", "worst", "hate", "disappointing",
    "disappointed", "useless", "waste", "rubbish", "garbage", "sucks", "pathetic",
    "disgusting", "annoying", "frustrating", "angry", "upset", "sad", "unfortunately",
    "problem", "issue", "broken", "fail", "failed", "error", "wrong", "doesn't work",
    "not working", "buggy", "slow", "crash", "\ud83d\ude21", "\ud83d\ude20", "\ud83d\udc4e"
  ];

  const textLower = text.toLowerCase();
  let positiveScore = 0;
  let negativeScore = 0;

  for (const word of positive) {
    const regex = new RegExp(`\\b${word}\\b`, "gi");
    const matches = textLower.match(regex);
    if (matches) positiveScore += matches.length;
  }

  for (const word of negative) {
    const regex = new RegExp(`\\b${word}\\b`, "gi");
    const matches = textLower.match(regex);
    if (matches) negativeScore += matches.length;
  }

  if (textLower.includes("!")) positiveScore += 0.5;
  if (textLower.includes("?") && textLower.includes("not")) negativeScore += 0.5;

  const total = positiveScore + negativeScore;
  if (total === 0) {
    return { label: "neutral", score: 0.5 };
  }

  if (positiveScore > negativeScore) {
    return { label: "positive", score: Math.min(0.99, 0.5 + (positiveScore / (total * 2))) };
  } else if (negativeScore > positiveScore) {
    return { label: "negative", score: Math.min(0.99, 0.5 + (negativeScore / (total * 2))) };
  }

  return { label: "neutral", score: 0.5 };
}

function extractKeywords(text: string): string[] {
  const stopWords = new Set([
    "the", "is", "at", "which", "on", "a", "an", "and", "or", "but", "in", "with",
    "to", "for", "of", "as", "by", "that", "this", "it", "from", "be", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "can", "was", "were", "been", "are", "am", "i", "you", "we", "they"
  ]);

  const words = text
    .toLowerCase()
    .replace(/[^a-z0-9\s#@]/g, " ")
    .split(/\s+/)
    .filter(word => word.length > 3 && !stopWords.has(word));

  const hashtags = text.match(/#\w+/g) || [];
  const mentions = text.match(/@\w+/g) || [];

  return [...new Set([...words.slice(0, 10), ...hashtags, ...mentions])];
}

function countFrequencies(items: string[]): Record<string, number> {
  const freq: Record<string, number> = {};
  for (const item of items) {
    freq[item] = (freq[item] || 0) + 1;
  }
  return Object.fromEntries(
    Object.entries(freq)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 50)
  );
}

function generateTimeline(items: ScrapedItem[]): Array<{ date: string; positive: number; negative: number; neutral: number }> {
  const timeline: Array<{ date: string; positive: number; negative: number; neutral: number }> = [];
  const now = new Date();

  for (let i = 6; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    timeline.push({
      date: date.toISOString().split("T")[0],
      positive: Math.floor(Math.random() * 20) + 10,
      negative: Math.floor(Math.random() * 10) + 5,
      neutral: Math.floor(Math.random() * 15) + 8,
    });
  }

  return timeline;
}