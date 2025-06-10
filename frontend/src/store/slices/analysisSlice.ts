import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { Analysis as IAnalysis, AnalysisResult as IAnalysisResult } from '../../types'; 
import axios from 'axios';
import { analysisApi } from '../../services/api';
import { RootState } from '..';

export interface Review {
  id: string;
  content: string;
  rating: number;
  date: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  aspects: {
    category: string;
    sentiment: 'positive' | 'negative' | 'neutral';
    text: string;
  }[];
}

export interface AnalysisLocal {
  id: string;
  product_id: string;
  product_name: string;
  product_image?: string;
  marketplace: 'wildberries' | 'ozon';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  review_count: number;
  positive_sentiment?: number;
  negative_sentiment?: number;
  neutral_sentiment?: number;
  aspects?: {
    name: string;
    positive: number;
    negative: number;
    neutral: number;
  }[];
  error_message?: string;
}

export interface AnalysisResult {
  id: string;
  analysis_id: string;
  summary: {
    positive_count: number;
    negative_count: number;
    neutral_count: number;
    average_rating: number;
    aspect_summary: {
      [category: string]: {
        positive: number;
        negative: number;
        neutral: number;
      }
    };
  };
  reviews: Review[];
}

export interface NewAnalysisRequest {
  url: string;
  marketplace: 'wildberries' | 'ozon';
  max_reviews?: number;
}

interface AnalysisState {
  analyses: IAnalysis[];
  currentAnalysis: IAnalysis | null;
  currentResult: AnalysisResult | null;
  loading: boolean;
  submitting: boolean;
  error: string | null;
}

const initialState: AnalysisState = {
  analyses: [],
  currentAnalysis: null,
  currentResult: null,
  loading: false,
  submitting: false,
  error: null
};

export const fetchAllAnalyses = createAsyncThunk(
  'analysis/fetchAll',
  async (_, { rejectWithValue }) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        return rejectWithValue('Вы не авторизованы. Пожалуйста, выполните вход.');
      }
      
      const response = await analysisApi.getAllAnalyses();
      return response as IAnalysis[];
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Не удалось загрузить анализы');
    }
  }
);

export const fetchAnalysisById = createAsyncThunk(
  'analysis/fetchById',
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await analysisApi.getAnalysisById(id);
      return response as IAnalysis;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Не удалось загрузить анализ');
    }
  }
);

export const createAnalysis = createAsyncThunk(
  'analysis/create',
  async (data: NewAnalysisRequest, { rejectWithValue }) => {
    try {
      const marketplaceMapping = {
        'ozon': 'ozon',
        'wildberries': 'wb'
      };
      
      const transformedData = {
        marketplace: marketplaceMapping[data.marketplace],
        url: data.url,
        max_reviews: data.max_reviews || 30
      };
      
      const response = await analysisApi.createAnalysis(transformedData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Не удалось создать анализ');
    }
  }
);

export const deleteAnalysis = createAsyncThunk(
  'analysis/delete',
  async (id: string, { rejectWithValue }) => {
    try {
      await analysisApi.deleteAnalysis(id);
      return id;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Не удалось удалить анализ');
    }
  }
);

export const exportAnalysis = createAsyncThunk(
  'analysis/export',
  async (id: string, { rejectWithValue }) => {
    try {
      const response = await analysisApi.exportAnalysisResults(id);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Не удалось экспортировать анализ');
    }
  }
);

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearCurrentAnalysis: (state) => {
      state.currentAnalysis = null;
    },
    clearCurrentResult: (state) => {
      state.currentResult = null;
    },
    setCurrentAnalysis: (state, action: PayloadAction<IAnalysis>) => {
      state.currentAnalysis = action.payload;
    }
  },
  extraReducers: (builder) => {
    // fetchAllAnalyses
    builder
      .addCase(fetchAllAnalyses.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAllAnalyses.fulfilled, (state, action) => {
        state.loading = false;
        state.analyses = action.payload;
      })
      .addCase(fetchAllAnalyses.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      .addCase(fetchAnalysisById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchAnalysisById.fulfilled, (state, action) => {
        state.loading = false;
        state.currentAnalysis = action.payload;
      })
      .addCase(fetchAnalysisById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      .addCase(createAnalysis.pending, (state) => {
        state.submitting = true;
        state.error = null;
      })
      .addCase(createAnalysis.fulfilled, (state, action) => {
        state.submitting = false;
        state.analyses.unshift(action.payload);
      })
      .addCase(createAnalysis.rejected, (state, action) => {
        state.submitting = false;
        state.error = action.payload as string;
      })
      
      .addCase(deleteAnalysis.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(deleteAnalysis.fulfilled, (state, action) => {
        state.loading = false;
        state.analyses = state.analyses.filter(analysis => analysis.id !== action.payload);
      })
      .addCase(deleteAnalysis.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      
      .addCase(exportAnalysis.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(exportAnalysis.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(exportAnalysis.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });
  }
});

export const { clearError, clearCurrentAnalysis, clearCurrentResult, setCurrentAnalysis } = analysisSlice.actions;

export const selectAllAnalyses = (state: RootState) => state.analysis.analyses;
export const selectCurrentAnalysis = (state: RootState) => state.analysis.currentAnalysis;
export const selectCurrentResult = (state: RootState) => state.analysis.currentResult;
export const selectLoading = (state: RootState) => state.analysis.loading;
export const selectError = (state: RootState) => state.analysis.error;

export default analysisSlice.reducer; 