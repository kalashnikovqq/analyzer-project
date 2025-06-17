import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Divider,
  Container
} from '@mui/material';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';

import { useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store';
import { createAnalysis } from '../../store/slices/analysisSlice';

import AnalysisProgressDialog from '../../components/analysis/AnalysisProgressDialog';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analyze-tabpanel-${index}`}
      aria-labelledby={`analyze-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const NewAnalysisPage: React.FC = () => {
  const navigate = useNavigate();
  const [tabIndex, setTabIndex] = useState(0);
  const [marketplace, setMarketplace] = useState('wildberries');
  const [productUrl, setProductUrl] = useState('');
  const [productId, setProductId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [maxReviews, setMaxReviews] = useState(30);
  const [showProgressDialog, setShowProgressDialog] = useState(false);
  const [currentAnalysisId, setCurrentAnalysisId] = useState<string | null>(null);
  const dispatch = useDispatch<AppDispatch>();

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  const handleMarketplaceChange = (event: SelectChangeEvent) => {
    setMarketplace(event.target.value);
  };

  const handleUrlSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    
    if (!productUrl) {
      setError('Пожалуйста, введите URL товара');
      return;
    }
    
    if (marketplace === 'wildberries' && !productUrl.includes('wildberries.ru')) {
      setError('URL должен быть с сайта Wildberries');
      return;
    }
    
    if (marketplace === 'ozon' && !productUrl.includes('ozon.ru')) {
      setError('URL должен быть с сайта Ozon');
      return;
    }
    
    setError('');
    startAnalysis();
  };

  const handleIdSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    
    if (!productId) {
      setError('Пожалуйста, введите ID товара');
      return;
    }
    
    if (marketplace === 'wildberries' && !/^\d+$/.test(productId)) {
      setError('ID товара Wildberries должен содержать только цифры');
      return;
    }
    
    if (marketplace === 'ozon' && !/^\d+$/.test(productId)) {
      setError('ID товара Ozon должен содержать только цифры');
      return;
    }
    
    setError('');
    startAnalysis();
  };

  const startAnalysis = async () => {
    setLoading(true);
    
    try {
      let validatedMaxReviews = maxReviews;
      if (typeof maxReviews !== 'number' || isNaN(maxReviews)) {
        validatedMaxReviews = 100;
      } else if (maxReviews < 10) {
        validatedMaxReviews = 10;
      } else if (maxReviews > 1000) {
        validatedMaxReviews = 1000;
      }
      
      const analysisRequest = {
        url: tabIndex === 0 ? productUrl : productId,
        marketplace: marketplace as 'wildberries' | 'ozon',
        max_reviews: validatedMaxReviews
      };
      
      const result = await dispatch(createAnalysis(analysisRequest));
      
      if (createAnalysis.fulfilled.match(result)) {
        setCurrentAnalysisId(result.payload.id);
        setShowProgressDialog(true);
      } else {
        throw new Error(result.payload as string || 'Не удалось создать анализ');
      }
    } catch (err: any) {
      setError(err.message || 'Произошла ошибка при создании анализа');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalysisComplete = (analysisId: string) => {
    setShowProgressDialog(false);
    setCurrentAnalysisId(null);
    navigate(`/analysis/result/${analysisId}`);
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
    <Container maxWidth="lg">
      <Paper elevation={3} sx={{ p: 3, mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Новый анализ
        </Typography>
        
        <Typography variant="body1" color="text.secondary" align="center" paragraph>
          Выберите маркетплейс и укажите товар для анализа отзывов
        </Typography>
        
        <Paper elevation={3} sx={{ mt: 4, p: 0, borderRadius: 2, maxWidth: 800, mx: 'auto' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={tabIndex} 
              onChange={handleTabChange} 
              aria-label="analysis tabs" 
              centered
            >
              <Tab label="Поиск по URL" />
              <Tab label="Поиск по ID товара" />
            </Tabs>
          </Box>
          
          <Box sx={{ p: 3 }}>
            <FormControl fullWidth margin="normal">
              <InputLabel id="marketplace-select-label">Маркетплейс</InputLabel>
              <Select
                labelId="marketplace-select-label"
                id="marketplace-select"
                value={marketplace}
                label="Маркетплейс"
                onChange={handleMarketplaceChange}
                startAdornment={<ShoppingBagIcon sx={{ color: 'action.active', mr: 1 }} />}
              >
                <MenuItem value="wildberries">Wildberries</MenuItem>
                <MenuItem value="ozon">Ozon</MenuItem>
              </Select>
            </FormControl>
          
            <FormControl fullWidth margin="normal">
              <TextField
                id="max-reviews-input"
                label="Количество отзывов для парсинга"
                type="number"
                value={maxReviews}
                onChange={(e) => {
                  const value = Number(e.target.value);
                  if (value >= 1 && value <= 1000) {
                    setMaxReviews(value);
                  } else if (value < 1) {
                    setMaxReviews(1);
                  } else if (value > 1000) {
                    setMaxReviews(1000);
                  }
                }}
                InputProps={{ 
                  inputProps: { min: 1, max: 1000 } 
                }}
                helperText="Большее количество отзывов увеличивает точность, но замедляет анализ (макс. 1000)"
              />
            </FormControl>
          
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
            
            <Box sx={{ mt: 3 }}>
              <TabPanel value={tabIndex} index={0}>
              <Box component="form" onSubmit={handleUrlSubmit} noValidate>
                <Typography variant="body2" paragraph>
                  Вставьте ссылку на товар с сайта {marketplace === 'wildberries' ? 'Wildberries' : 'Ozon'}
                  {marketplace === 'wildberries' && (
                    <><br />Пример: https://www.wildberries.ru/catalog/344109761/detail.aspx?targetUrl=SP</>
                  )}
                  {marketplace === 'ozon' && (
                    <><br />Пример: https://www.ozon.ru/product/example-product-344109761/</>
                  )}
                </Typography>
                
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="product-url"
                  label="URL товара"
                  name="productUrl"
                  autoFocus
                  value={productUrl}
                  onChange={(e) => setProductUrl(e.target.value)}
                  placeholder={marketplace === 'wildberries' 
                    ? 'https://www.wildberries.ru/catalog/12345678/detail.aspx' 
                    : 'https://www.ozon.ru/product/12345678/'
                  }
                />
                
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  sx={{ mt: 3, mb: 2 }}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <CircularProgress size={24} sx={{ mr: 1 }} />
                      Анализ отзывов...
                    </>
                  ) : 'Начать анализ'}
                </Button>
              </Box>
            </TabPanel>
            
            <TabPanel value={tabIndex} index={1}>
              <Box component="form" onSubmit={handleIdSubmit} noValidate>
                <Typography variant="body2" paragraph>
                  Введите {marketplace === 'wildberries' ? 'артикул товара Wildberries' : 'ID товара Ozon'}
                  {marketplace === 'wildberries' && (
                    <><br />Пример: 344109761</>
                  )}
                  {marketplace === 'ozon' && (
                    <><br />Пример: 344109761</>
                  )}
                </Typography>
                
                <TextField
                  margin="normal"
                  required
                  fullWidth
                  id="product-id"
                  label={marketplace === 'wildberries' ? 'Артикул товара' : 'ID товара'}
                  name="productId"
                  value={productId}
                  onChange={(e) => setProductId(e.target.value)}
                  placeholder={marketplace === 'wildberries' ? '344109761' : '344109761'}
                />
                
                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  sx={{ mt: 3, mb: 2 }}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <CircularProgress size={24} sx={{ mr: 1 }} />
                      Анализ отзывов...
                    </>
                  ) : 'Начать анализ'}
                </Button>
              </Box>
            </TabPanel>
            </Box>
          </Box>
          
          <Divider />
          
          <Box sx={{ p: 3, bgcolor: 'background.default', borderRadius: '0 0 8px 8px' }}>
            <Typography variant="body2" color="text.secondary">
              Анализатор соберет отзывы о товаре, обработает их с помощью искусственного интеллекта и выделит ключевые аспекты, которые упоминают покупатели.
            </Typography>
          </Box>
        </Paper>
      </Paper>

      <AnalysisProgressDialog
        open={showProgressDialog}
        onClose={handleProgressDialogClose}
        analysisId={currentAnalysisId || ''}
        onComplete={handleAnalysisComplete}
        onError={handleAnalysisError}
        onCancel={handleAnalysisCancel}
      />
    </Container>
  );
};

export default NewAnalysisPage; 