import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { 
  Box, 
  Typography, 
  Paper, 
  Grid, 
  Tabs, 
  Tab, 
  Button, 
  Chip, 
  Divider,
  CircularProgress,
  Alert,
  Container,
  Snackbar
} from '@mui/material';
import { 
  Share as ShareIcon
} from '@mui/icons-material';

import AspectCard from '../../components/analysis/AspectCard';
import ExportResultsButton from '../../components/analysis/ExportResultsButton';


import { analysisApi } from '../../services/api';
import axios from 'axios';

interface ExportData {
  analysisId: string;
  productName: string;
  productId: string;
  marketplace: string;
  date: string;
  reviewsCount: number;
  positiveCount: number;
  negativeCount: number;
  neutralCount: number;
  positiveAspects: { aspect: string; count: number }[];
  negativeAspects: { aspect: string; count: number }[];
}

interface AspectItem {
  text: string;
  count: number;
}

interface AspectCategory {
  name: string;
  aspects: AspectItem[];
  total_mentions_in_category: number;
}

interface AspectsStructure {
  categories: AspectCategory[];
  total_aspect_mentions: number;
}

interface FinalAspectsStructure {
  positive: AspectsStructure;
  negative: AspectsStructure;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
      style={{ padding: 24 }}
    >
      {value === index && (
        <Box>
          {children}
        </Box>
      )}
    </div>
  );
}

const AnalysisResultPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [initialLoading, setInitialLoading] = useState(true);
  const [isLoadingLiveAnalysis, setIsLoadingLiveAnalysis] = useState(false);
  const [isSavingAnalysis, setIsSavingAnalysis] = useState(false);
  const [analysisRequestData, setAnalysisRequestData] = useState<any>(null);
  const [displayedAnalysisData, setDisplayedAnalysisData] = useState<any>(null);
  const [tabIndex, setTabIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [showError, setShowError] = useState(false);
  const navigate = useNavigate();
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  const processAnalysis = useCallback(async () => {
    if (!id) {
        setError('Идентификатор анализа не указан');
        setInitialLoading(false);
        return;
    }
    setInitialLoading(true);
    setIsLoadingLiveAnalysis(false); 
    setIsSavingAnalysis(false);
    setError(null); 
    setShowError(false);
    const analysisRequestKey = `analysis_request_${id}`;

    try {
      let currentAnalysisRequest: any = null;
      try {
        const storedRequest = localStorage.getItem(analysisRequestKey);
        if (storedRequest) {
          currentAnalysisRequest = JSON.parse(storedRequest);
        }
      } catch (e) {
        localStorage.removeItem(analysisRequestKey);
      }
      
      if (!currentAnalysisRequest || !currentAnalysisRequest.status) {
        try {
          currentAnalysisRequest = await analysisApi.getAnalysisById(id);
          if (currentAnalysisRequest) {
            localStorage.setItem(analysisRequestKey, JSON.stringify(currentAnalysisRequest));
          } else {
            throw new Error('Не удалось получить данные запроса на анализ с сервера.');
          }
        } catch (apiError: any) {
          if (apiError.response?.status === 404) {
            throw new Error('Анализ не найден. Возможно, он был удален или у вас нет доступа к нему.');
          } else if (apiError.response?.status === 403) {
            throw new Error('У вас нет доступа к этому анализу.');
          } else {
            throw new Error(apiError.response?.data?.detail || 'Не удалось получить данные анализа с сервера.');
          }
        }
      }
      
      setAnalysisRequestData(currentAnalysisRequest);

      if (currentAnalysisRequest && currentAnalysisRequest.status === 'pending') {
        setIsLoadingLiveAnalysis(true);
        setIsSavingAnalysis(true); 

        try {
          const liveAnalysisParams = {
            url: currentAnalysisRequest.url,
            marketplace: currentAnalysisRequest.marketplace,
            max_reviews: currentAnalysisRequest.max_reviews || 100,
          };
          const liveResults = await analysisApi.performLiveAnalysis(liveAnalysisParams);
          setIsLoadingLiveAnalysis(false);

          let structuredAspectsForSaving: any = {
            positive: { categories: [], total_aspect_mentions: 0 },
            negative: { categories: [], total_aspect_mentions: 0 }
          };

          const liveSentAnalysis = liveResults.sentiment_analysis;

          if (liveSentAnalysis && liveSentAnalysis.aspects) {
            const processSentimentType = (sentimentType: 'positive' | 'negative') => {
              const liveAspectData = liveSentAnalysis.aspects[sentimentType];
              if (liveAspectData) {
                // Если API возвращает categories: [{name, aspects: [{text, count}]}]
                if (liveAspectData.categories && Array.isArray(liveAspectData.categories)) {
                  structuredAspectsForSaving[sentimentType] = {
                    categories: liveAspectData.categories.map((cat: any) => ({
                      name: cat.name || 'другое',
                      aspects: (cat.aspects || []).map((asp: any) => ({ text: asp.text || '', count: asp.count || 0 })),
                      total_mentions_in_category: (cat.aspects || []).reduce((s: number, asp: any) => s + (asp.count || 0), 0)
                    })),
                    total_aspect_mentions: liveAspectData.total_aspect_mentions || liveAspectData.categories.reduce((s: number, cat: any) => s + (cat.aspects || []).reduce((s_asp: number, asp: any) => s_asp + (asp.count || 0), 0) ,0)
                  };
                } 
                // Если API возвращает массив аспектов [{text, count}] для sentimentType
                else if (Array.isArray(liveAspectData) && liveAspectData.length > 0) {
                  const aspects = liveAspectData.map((asp: any) => ({ text: asp.text || '', count: asp.count || 0 }));
                  const totalMentions = aspects.reduce((s: number, asp: any) => s + (asp.count || 0), 0);
                  structuredAspectsForSaving[sentimentType] = {
                    categories: [{ name: "другое", aspects: aspects, total_mentions_in_category: totalMentions }],
                    total_aspect_mentions: totalMentions
                  };
                }
              }
            };
            processSentimentType('positive');
            processSentimentType('negative');
          }
          
          const resultsToSave = {
            positive_aspects: (structuredAspectsForSaving.positive?.categories || [])
              .flatMap((cat:any) => cat.aspects || [])
              .map((asp: any) => ({ text: asp.text, count: asp.count })),
            negative_aspects: (structuredAspectsForSaving.negative?.categories || [])
              .flatMap((cat:any) => cat.aspects || [])
              .map((asp: any) => ({ text: asp.text, count: asp.count })),
            aspect_categories: structuredAspectsForSaving,
            reviews_count: liveResults.reviews_count || 0,
            sentiment_summary: {
              total: liveResults.sentiment_analysis?.total || 0,
              positive: liveResults.sentiment_analysis?.positive || 0,
              negative: liveResults.sentiment_analysis?.negative || 0,
              neutral: liveResults.sentiment_analysis?.neutral || 0,
              positive_percent: liveResults.sentiment_analysis?.positive_percent || 0,
              negative_percent: liveResults.sentiment_analysis?.negative_percent || 0,
              neutral_percent: liveResults.sentiment_analysis?.neutral_percent || 0,
            },
            product_info: liveResults.product_info || {},
          };
          await analysisApi.saveCompletedAnalysis(id, resultsToSave);
          const finalAnalysisRequest = await analysisApi.getAnalysisById(id);
          if (finalAnalysisRequest) {
            localStorage.setItem(analysisRequestKey, JSON.stringify(finalAnalysisRequest));
            setAnalysisRequestData(finalAnalysisRequest);
          } else {
            throw new Error('Не удалось перезапросить данные анализа после сохранения.');
          }
        } catch (liveSaveError: any) {
          setError(liveSaveError.message || 'Ошибка при выполнении или сохранении анализа.');
          setShowError(true);
        } finally {
          setIsLoadingLiveAnalysis(false);
          setIsSavingAnalysis(false);
        }
      } else if (currentAnalysisRequest && currentAnalysisRequest.status === 'failed') {
        setError(currentAnalysisRequest.error_message || 'Анализ завершился с ошибкой.');
        setShowError(true);
      }
    } catch (err: any) {
      setError(err.message || 'Произошла неизвестная ошибка при загрузке данных анализа.');
      setShowError(true);
    } finally {
      setInitialLoading(false);
    }
  }, [id]); 

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token && !isAuthenticated) {
      setError('Для просмотра результатов анализа необходимо авторизоваться');
      setShowError(true);
      setInitialLoading(false);
      sessionStorage.setItem('redirectAfterLogin', window.location.pathname);
      setTimeout(() => navigate('/login'), 3000);
      return;
    }
    processAnalysis();
  }, [processAnalysis, isAuthenticated, navigate]); 
  
  const formatDataForDisplay = useCallback((dataToFormat: any) => {
    if (!dataToFormat) return null;
    
    let sourceData = dataToFormat;
    let productInfo: any = {};
    let sentimentAnalysis: any = {};
    let ratingStats: any = {};
    let reviewsCount = 0;
    let finalAspectsStructure: FinalAspectsStructure = {
        positive: { categories: [], total_aspect_mentions: 0 },
        negative: { categories: [], total_aspect_mentions: 0 }
    };

    if (dataToFormat.status === 'completed' && dataToFormat.results) {
        sourceData = { 
            ...dataToFormat,
            ...dataToFormat.results 
        };
        productInfo = sourceData.product_info || {};
        reviewsCount = sourceData.reviews_count || 0;
        sentimentAnalysis = sourceData.sentiment_summary || {};

        if (sourceData.aspect_categories && sourceData.aspect_categories.positive && sourceData.aspect_categories.negative) {
            finalAspectsStructure = {
                positive: {
                    categories: (sourceData.aspect_categories.positive?.categories || []).map((cat: any) => ({
                        name: cat.name || 'другое',
                        aspects: (cat.aspects || []).map((asp: any) => ({ text: asp.text || '', count: asp.count || 0})),
                        total_mentions_in_category: (cat.aspects || []).reduce((s:number, asp:any) => s + (asp.count || 0), 0)
                    })),
                    total_aspect_mentions: sourceData.aspect_categories.positive?.total_aspect_mentions || 0
                },
                negative: {
                    categories: (sourceData.aspect_categories.negative?.categories || []).map((cat: any) => ({
                        name: cat.name || 'другое',
                        aspects: (cat.aspects || []).map((asp: any) => ({ text: asp.text || '', count: asp.count || 0})),
                        total_mentions_in_category: (cat.aspects || []).reduce((s:number, asp:any) => s + (asp.count || 0), 0)
                    })),
                    total_aspect_mentions: sourceData.aspect_categories.negative?.total_aspect_mentions || 0
                }
            };
        } else if (sourceData.positive_aspects || sourceData.negative_aspects) {
            // Fallback for old data structure (flat positive_aspects/negative_aspects)
            const convertFlatAspectsToCategories = (flatAspectsArray: any[], sentiment: 'positive' | 'negative') => {
                if (!flatAspectsArray || !Array.isArray(flatAspectsArray) || flatAspectsArray.length === 0) {
                    return { categories: [], total_aspect_mentions: 0 };
                }
                const aspects = flatAspectsArray.map(a => ({ text: a.text || '', count: a.count || 0 }));
                const totalMentions = aspects.reduce((sum, aspect) => sum + aspect.count, 0);
                return {
                    categories: [{
                        name: "другое",
                        aspects: aspects,
                        total_mentions_in_category: totalMentions
                    }],
                    total_aspect_mentions: totalMentions
                };
            };
            finalAspectsStructure.positive = convertFlatAspectsToCategories(sourceData.positive_aspects, 'positive');
            finalAspectsStructure.negative = convertFlatAspectsToCategories(sourceData.negative_aspects, 'negative');
        }
        sentimentAnalysis.aspects = finalAspectsStructure;

    } else if (dataToFormat.raw_live_results) { // Handle pending/live results
        sourceData = {
            id: dataToFormat.id, 
            created_at: dataToFormat.created_at,
            product_id: dataToFormat.raw_live_results.product_id,
            marketplace: dataToFormat.raw_live_results.marketplace,
            product_info: dataToFormat.raw_live_results.product_info,
            reviews_count: dataToFormat.raw_live_results.reviews_count,
            sentiment_analysis: dataToFormat.raw_live_results.sentiment_analysis,
            rating_stats: dataToFormat.raw_live_results.rating_stats,
        };
        productInfo = sourceData.product_info || {};
        sentimentAnalysis = sourceData.sentiment_analysis || { aspects: {} };
        ratingStats = sourceData.rating_stats || {};
        reviewsCount = sourceData.reviews_count || 0;

        if (sentimentAnalysis.aspects) {
            const transformLiveAspects = (liveAspectDataType: any, sentiment: 'positive' | 'negative') => {
                if (!liveAspectDataType) return { categories: [], total_aspect_mentions: 0 };

                if (liveAspectDataType.categories && Array.isArray(liveAspectDataType.categories)) {
                    // API returns categories: [{name, aspects: [{text, count}]}]
                    return {
                        categories: liveAspectDataType.categories.map((cat: any) => ({
                            name: cat.name || 'другое',
                            aspects: (cat.aspects || []).map((asp: any) => ({ text: asp.text || '', count: asp.count || 0})),
                            total_mentions_in_category: (cat.aspects || []).reduce((s:number, asp:any) => s + (asp.count || 0), 0)
                        })),
                        total_aspect_mentions: liveAspectDataType.total_aspect_mentions || 
                                             (liveAspectDataType.categories || []).reduce((s: number, cat: any) => s + (cat.aspects || []).reduce((s_asp:number, asp:any) => s_asp + (asp.count || 0), 0), 0)
                    };
                } else if (Array.isArray(liveAspectDataType) && liveAspectDataType.length > 0) {
                    // API returns array of aspects: [{text, count}]
                    const aspects = liveAspectDataType.map((asp: any) => ({ text: asp.text || '', count: asp.count || 0 }));
                    const totalMentions = aspects.reduce((sum: number, asp: any) => sum + asp.count, 0);
                    return {
                        categories: [{ name: "другое", aspects: aspects, total_mentions_in_category: totalMentions }],
                        total_aspect_mentions: totalMentions
                    };
                }
                return { categories: [], total_aspect_mentions: 0 }; 
            };
            
            finalAspectsStructure = {
                positive: transformLiveAspects(sentimentAnalysis.aspects.positive, 'positive'),
                negative: transformLiveAspects(sentimentAnalysis.aspects.negative, 'negative')
            };
            sentimentAnalysis.aspects = finalAspectsStructure;
        }
    } else {
      sentimentAnalysis.aspects = finalAspectsStructure; 
    }

    const formatted = {
      id: sourceData.id || id,
      date: sourceData.created_at || new Date().toISOString(),
      product: {
        id: sourceData.product_id,
        name: productInfo.name || `Товар ${sourceData.marketplace}`,
        marketplace: sourceData.marketplace,
        url: productInfo.url || '#',
        rating: ratingStats.average || 0,
        image_url: productInfo.image_url || '',
        brand: productInfo.brand || '',
        price: productInfo.price || 0,
      },
      reviews: {
        total: reviewsCount,
        analyzed: reviewsCount,
        positive: sentimentAnalysis.positive || 0,
        negative: sentimentAnalysis.negative || 0,
        neutral: sentimentAnalysis.neutral || 0,
        positive_percent: sentimentAnalysis.positive_percent || 0,
        negative_percent: sentimentAnalysis.negative_percent || 0,
        neutral_percent: sentimentAnalysis.neutral_percent || 0,
      },
      sentiment_analysis_aspects: sentimentAnalysis.aspects || finalAspectsStructure,
      exportData: {
        analysisId: sourceData.id || id,
        productName: productInfo.name || `Товар ${sourceData.marketplace}`,
        productId: sourceData.product_id,
        marketplace: sourceData.marketplace,
        date: sourceData.created_at || new Date().toISOString(),
        reviewsCount: reviewsCount,
        positiveCount: sentimentAnalysis.positive || 0,
        negativeCount: sentimentAnalysis.negative || 0,
        neutralCount: sentimentAnalysis.neutral || 0,
        positiveAspects: (sentimentAnalysis.aspects?.positive?.categories || [])
          .flatMap((category: any) =>
            (category.aspects || []).map((aspect: any) => ({
              aspect: aspect.text ? `${aspect.text} (${category.name || 'другое'})` : `[Нет текста] (${category.name || 'другое'})`,
              count: aspect.count || 0,
            }))
          )
          .sort((a: any, b: any) => b.count - a.count) || [],
        negativeAspects: (sentimentAnalysis.aspects?.negative?.categories || [])
          .flatMap((category: any) =>
            (category.aspects || []).map((aspect: any) => ({
              aspect: aspect.text ? `${aspect.text} (${category.name || 'другое'})` : `[Нет текста] (${category.name || 'другое'})`,
              count: aspect.count || 0,
            }))
          )
          .sort((a: any, b: any) => b.count - a.count) || [],
      },
    };
    
    return formatted;
  }, [id]); 

  useEffect(() => {
    if (analysisRequestData && (analysisRequestData.status === 'completed' || analysisRequestData.status === 'failed')) {
        const formatted = formatDataForDisplay(analysisRequestData);
        setDisplayedAnalysisData(formatted);
    } else if (analysisRequestData && analysisRequestData.status === 'pending' && !isLoadingLiveAnalysis && !isSavingAnalysis) {
        if (analysisRequestData.raw_live_results) {
            const formatted = formatDataForDisplay(analysisRequestData);
            setDisplayedAnalysisData(formatted);
        } else {
            setDisplayedAnalysisData(null);
        }
    }
  }, [analysisRequestData, isLoadingLiveAnalysis, isSavingAnalysis, formatDataForDisplay]); 

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  const handleCloseError = () => {
    setShowError(false);
    setError(null);
  };

  const renderResults = () => {
    if (initialLoading || isLoadingLiveAnalysis || isSavingAnalysis) {
      return (
        <Container sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh', flexDirection: 'column', gap: 2 }}>
          <CircularProgress />
          {isLoadingLiveAnalysis && <Typography>Выполняется анализ отзывов...</Typography>}
          {isSavingAnalysis && !isLoadingLiveAnalysis && <Typography>Сохранение результатов анализа...</Typography>}
          {initialLoading && !isLoadingLiveAnalysis && !isSavingAnalysis && <Typography>Загрузка данных анализа...</Typography>}
        </Container>
      );
    }

    if (error && showError) { 
        return (
            <Container sx={{ textAlign: 'center', my: 4 }}>
                <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
                <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                  <Button variant="outlined" onClick={() => processAnalysis()}>Попробовать снова</Button>
                  <Button variant="contained" onClick={() => navigate('/analysis/history')}>
                    Вернуться к списку анализов
                  </Button>
                </Box>
            </Container>
        );
    }
    
    if (!displayedAnalysisData) {
      return (
        <Container sx={{ textAlign: 'center', my: 8 }}>
          <Typography variant="h6">Данные анализа не найдены или еще не загружены.</Typography>
          <Typography>Если анализ только что запущен, это может занять некоторое время.</Typography>
          <Button variant="outlined" onClick={() => processAnalysis()} sx={{mt: 2}}>Обновить</Button>
        </Container>
      );
    }

    const positiveAspectData = displayedAnalysisData.sentiment_analysis_aspects?.positive;
    const negativeAspectData = displayedAnalysisData.sentiment_analysis_aspects?.negative;

    return (
      <Container sx={{py: 2}}>
        <Paper elevation={1} sx={{ p: {xs: 2, md: 3}, mb: 3, borderRadius: 2 }}>
          <Typography variant="h4" component="h1" gutterBottom sx={{fontWeight: 'bold'}}>
            {displayedAnalysisData.product.name}
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 1 }}>
            <Chip label={`ID: ${displayedAnalysisData.product.id}`} size="small" />
            <Chip label={`Маркетплейс: ${displayedAnalysisData.product.marketplace}`} size="small" />
            {displayedAnalysisData.product.brand && <Chip label={`Бренд: ${displayedAnalysisData.product.brand}`} size="small" />}
            {displayedAnalysisData.product.price > 0 && <Chip label={`Цена: ${displayedAnalysisData.product.price} ₽`} size="small" color="primary"/>}
            {displayedAnalysisData.product.rating > 0 && <Chip label={`Рейтинг: ${displayedAnalysisData.product.rating} ★`} size="small" color="warning"/>}
          </Box>
          {displayedAnalysisData.product.url && displayedAnalysisData.product.url !== '#' &&
            <Button 
              href={displayedAnalysisData.product.url} 
              target="_blank" 
              variant="outlined"
              sx={{mt:1}}
            >
              Перейти к товару
            </Button>
          }
        </Paper>

        <Paper elevation={1} sx={{ p: 2, mb: 3, borderRadius: 2 }}>
          <Box sx={{ mb: 1 }}>
            <Typography variant="subtitle1" align="center" gutterBottom>
              Соотношение аспектов в отзывах
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Box 
                sx={{ 
                  flexGrow: positiveAspectData?.total_aspect_mentions || 1, 
                  height: 30, 
                  bgcolor: 'success.main', 
                  borderRadius: '4px 0 0 4px' 
                }} 
              />
              <Box 
                sx={{ 
                  flexGrow: negativeAspectData?.total_aspect_mentions || 1, 
                  height: 30, 
                  bgcolor: 'error.main', 
                  borderRadius: '0 4px 4px 0' 
                }} 
              />
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="success.main">
                Положительные: {positiveAspectData?.total_aspect_mentions || 0}
              </Typography>
              <Typography variant="body2" color="error.main">
                Отрицательные: {negativeAspectData?.total_aspect_mentions || 0}
              </Typography>
            </Box>
          </Box>
        </Paper>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <AspectCard 
              title="Положительные аспекты" 
              data={positiveAspectData} 
              sentiment="positive" 
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <AspectCard 
              title="Отрицательные аспекты" 
              data={negativeAspectData} 
              sentiment="negative" 
            />
          </Grid>
        </Grid>
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center', gap: 2 }}>
         {displayedAnalysisData.exportData && 
            <ExportResultsButton 
                analysisId={displayedAnalysisData.id} 
                exportData={displayedAnalysisData.exportData} 
            />}
        </Box>

      </Container>
    );
  };

  if (initialLoading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Alert severity="error" sx={{ mt: 3 }}>
          {error}
        </Alert>
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Button variant="contained" onClick={() => navigate('/analysis/history')}>
            Вернуться к истории анализов
          </Button>
      </Box>
      </Container>
    );
  }

  if (!displayedAnalysisData) {
    return (
      <Box sx={{ textAlign: 'center', my: 8 }}>
        <Typography variant="h5" color="error">
          Ошибка загрузки данных
        </Typography>
        <Typography variant="body1" sx={{ mt: 2 }}>
          Не удалось загрузить результаты анализа. Пожалуйста, попробуйте позже.
        </Typography>
      </Box>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Snackbar 
        open={showError}
        autoHideDuration={6000} 
        onClose={handleCloseError}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseError} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>

      {renderResults()}
      
    </Container>
  );
};

export default AnalysisResultPage; 