interface AnalysisResults {
  id: string;
  date: string;
  product: {
    id: string;
    name: string;
    marketplace: string;
    url: string;
    rating: number;
    image_url?: string;
    brand?: string;
    price?: number;
  };
  reviews: {
    total: number;
    analyzed: number;
    positive: number;
    negative: number;
    neutral: number;
    positive_percent: number;
    negative_percent: number;
    neutral_percent: number;
  };
  aspect_statistics: {
    positive_aspects: Array<{text: string; count: number; category?: string}>;
    negative_aspects: Array<{text: string; count: number; category?: string}>;
    aspect_categories?: Record<string, any>;
  }
}

const processCategories = (aspects: any): Record<string, any> => {
  if (!aspects || !aspects.aspect_categories) {
    return {};
  }
  return aspects.aspect_categories || {};
};

export const mapAnalysisResults = (data: any): AnalysisResults => {
  const categories = processCategories(data.sentiment_analysis?.aspects);

  return {
    id: data.product_id || '',
    date: new Date().toISOString(),
    product: {
      id: data.product_id || '',
      name: data.product_info?.name || `Товар ${data.marketplace}`,
      marketplace: data.marketplace || '',
      url: data.product_info?.url || '#',
      rating: data.rating_stats?.average || 0,
      image_url: data.product_info?.image_url || '',
      brand: data.product_info?.brand || '',
      price: data.product_info?.price || 0
    },
    reviews: {
      total: data.reviews_count || 0,
      analyzed: data.reviews_count || 0,
      positive: data.sentiment_analysis?.positive || 0, 
      negative: data.sentiment_analysis?.negative || 0,
      neutral: data.sentiment_analysis?.neutral || 0,
      positive_percent: data.sentiment_analysis?.positive_percent || 0,
      negative_percent: data.sentiment_analysis?.negative_percent || 0,
      neutral_percent: data.sentiment_analysis?.neutral_percent || 0
    },
    aspect_statistics: {
      positive_aspects: data.aspect_statistics?.positive_aspects || [],
      negative_aspects: data.aspect_statistics?.negative_aspects || [],
      aspect_categories: data.aspect_statistics?.aspect_categories || {}
    }
  };
}; 