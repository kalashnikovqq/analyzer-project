export interface User {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser: boolean;
  full_name?: string;
  created_at: string;
}

export interface Analysis {
  id: string;
  user_id: string;
  product_id?: string;
  url: string;
  platform: string;
  marketplace?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  limit: number;
  created_at: string;
  updated_at: string;
  reviews_count?: number;
  product_name?: string;
}

export interface AnalysisResult {
  id: string;
  analysis_id: string;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  keywords: KeywordData[];
  topics: TopicData[];
  sentiment_distribution: SentimentDistribution;
  reviews: Review[];
}

export interface KeywordData {
  keyword: string;
  count: number;
  sentiment: 'positive' | 'negative' | 'neutral';
}

export interface TopicData {
  topic: string;
  count: number;
  sentiment: 'positive' | 'negative' | 'neutral';
}

export interface SentimentDistribution {
  positive: number;
  negative: number;
  neutral: number;
}

export interface Review {
  id: string;
  text: string;
  rating: number;
  author?: string;
  date?: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  sentiment_score?: number;
  topics?: string[];
} 