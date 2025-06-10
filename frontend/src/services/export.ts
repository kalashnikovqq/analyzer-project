import { saveAs } from 'file-saver';
import apiClient from './api';

export enum ExportFormat {
  CSV = 'csv',
}

export interface ExportData {
  analysisId: string;
  productName: string;
  productId: string;
  marketplace: string;
  date: string;
  reviewsCount: number;
  positiveCount: number;
  negativeCount: number;
  neutralCount: number;
  positiveAspects: Array<{ aspect: string; count: number }>;
  negativeAspects: Array<{ aspect: string; count: number }>;
}

export const ExportService = {
  async exportToCSV(analysisId: string): Promise<void> {
    try {
      const response = await apiClient.get(`/analyses/${analysisId}/export`, {
        responseType: 'blob',
      });
      
      const blob = new Blob([response.data], { type: 'text/csv;charset=utf-8' });
      saveAs(blob, `analysis-${analysisId}.csv`);
    } catch (error) {
      console.error('Ошибка при экспорте в CSV:', error);
      throw error;
    }
  }
};