import React, { useState } from 'react';
import { useDispatch } from 'react-redux';
import { createAnalysis, fetchAllAnalyses } from '../../store/slices/analysisSlice';
import { AppDispatch } from '../../store';
import { 
  Button, 
  TextField, 
  Typography, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Paper, 
  Box, 
  CircularProgress, 
  Snackbar, 
  Alert 
} from '@mui/material';
import AnalysisProgressDialog from './AnalysisProgressDialog';

const AnalysisForm: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  
  const [marketplace, setMarketplace] = useState<'wildberries' | 'ozon'>('wildberries');
  const [url, setUrl] = useState('');
  const [limit, setLimit] = useState(100);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [showProgressDialog, setShowProgressDialog] = useState(false);
  const [currentAnalysisId, setCurrentAnalysisId] = useState<string | null>(null);
  
  const isWildberriesUrl = (url: string): boolean => {
    return /wildberries\.ru\/catalog\/\d+\/detail\.aspx/.test(url) || 
           /wb\.ru\/catalog\/\d+\/detail/.test(url);
  };
  
  const isOzonUrl = (url: string): boolean => {
    return /ozon\.ru\/product\//.test(url) || 
           /ozon\.ru\/context\/detail\/id\/\d+/.test(url);
  };
  
  const validateUrl = (): boolean => {
    if (!url.trim()) {
      setError('Ссылка на товар не может быть пустой');
      return false;
    }
    
    if (marketplace === 'wildberries' && !isWildberriesUrl(url)) {
      setError('Указана некорректная ссылка на товар Wildberries');
      return false;
    }
    
    if (marketplace === 'ozon' && !isOzonUrl(url)) {
      setError('Указана некорректная ссылка на товар Ozon');
      return false;
    }
    
    return true;
  };
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateUrl()) {
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await dispatch(createAnalysis({ marketplace, url, max_reviews: limit })).unwrap();
      
      if (result && result.id) {
        setCurrentAnalysisId(result.id);
        setShowProgressDialog(true);
        
        setUrl('');
        setLimit(100);
      } else {
        setSuccess(true);
      }
      
      dispatch(fetchAllAnalyses() as any); 
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка при создании анализа');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSuccessClose = () => {
    setSuccess(false);
  };
  
  const handleErrorClose = () => {
    setError(null);
  };

  const handleAnalysisComplete = (analysisId: string) => {
    setShowProgressDialog(false);
    setCurrentAnalysisId(null);
    setSuccess(true);
    dispatch(fetchAllAnalyses() as any);
  };

  const handleAnalysisError = (errorMessage: string) => {
    setShowProgressDialog(false);
    setCurrentAnalysisId(null);
    setError(errorMessage);
  };

  const handleAnalysisCancel = (analysisId: string) => {
    setShowProgressDialog(false);
    setCurrentAnalysisId(null);
    setError('Анализ был отменен');
  };

  const handleProgressDialogClose = () => {
    setShowProgressDialog(false);
    setCurrentAnalysisId(null);
  };
  
  return (
    <Paper sx={{ p: 3, maxWidth: 800, mx: 'auto', my: 4 }}>
      <Typography variant="h5" component="h2" gutterBottom align="center">
        Новый анализ отзывов
      </Typography>
      
      <Box component="form" onSubmit={handleSubmit} noValidate>
        <FormControl fullWidth margin="normal">
          <InputLabel id="marketplace-label">Платформа</InputLabel>
          <Select
            labelId="marketplace-label"
            value={marketplace}
            label="Платформа"
            onChange={(e) => setMarketplace(e.target.value as 'wildberries' | 'ozon')}
          >
            <MenuItem value="wildberries">Wildberries</MenuItem>
            <MenuItem value="ozon">Ozon</MenuItem>
          </Select>
        </FormControl>
        
        <TextField
          margin="normal"
          required
          fullWidth
          id="url"
          label="Ссылка на товар"
          name="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder={marketplace === 'wildberries' 
            ? "https://www.wildberries.ru/catalog/12345678/detail.aspx" 
            : "https://www.ozon.ru/product/[название-товара]/"}
          helperText={marketplace === 'wildberries' 
            ? "Например: https://www.wildberries.ru/catalog/12345678/detail.aspx" 
            : "Например: https://www.ozon.ru/product/[название-товара]/"}
        />
        
        <TextField
          margin="normal"
          fullWidth
          id="limit"
          label="Количество отзывов для анализа"
          name="limit"
          type="number"
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          inputProps={{ min: 10, max: 1000 }}
          helperText="Минимум 10, максимум 1000 отзывов"
        />
        
        <Button
          type="submit"
          fullWidth
          variant="contained"
          color="primary"
          sx={{ mt: 3, mb: 2 }}
          disabled={loading}
        >
          {loading ? <CircularProgress size={24} /> : 'Начать анализ'}
        </Button>
      </Box>
      
      <Snackbar open={!!error} autoHideDuration={6000} onClose={handleErrorClose}>
        <Alert onClose={handleErrorClose} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
      
      <Snackbar open={success} autoHideDuration={6000} onClose={handleSuccessClose}>
        <Alert onClose={handleSuccessClose} severity="success" sx={{ width: '100%' }}>
          Анализ успешно создан!
        </Alert>
      </Snackbar>

      {/* Диалог прогресса анализа */}
      {showProgressDialog && currentAnalysisId && (
        <AnalysisProgressDialog
          analysisId={currentAnalysisId}
          open={showProgressDialog}
          onClose={handleProgressDialogClose}
          onComplete={handleAnalysisComplete}
          onError={handleAnalysisError}
          onCancel={handleAnalysisCancel}
        />
      )}
    </Paper>
  );
};

export default AnalysisForm; 