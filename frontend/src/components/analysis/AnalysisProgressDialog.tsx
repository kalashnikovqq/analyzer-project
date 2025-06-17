import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  Box,
  Typography,
  LinearProgress,
  CircularProgress,
  Chip,
  Card,
  CardContent,
  IconButton,
  Button,
  Fade,
  Zoom,
  Slide,
  useTheme,
  alpha
} from '@mui/material';
import {
  Close as CloseIcon,
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as PsychologyIcon,
  Assessment as AssessmentIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as HourglassEmptyIcon
} from '@mui/icons-material';
import { keyframes } from '@mui/system';

const pulse = keyframes`
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
`;

const rotate = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

const shimmer = keyframes`
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
`;

interface ProgressData {
  analysis_id: string;
  status: string;
  progress_percentage: number;
  stage: string;
  stage_name: string;
  processed_reviews: number;
  total_reviews: number;
  estimated_time_remaining?: number;
}

interface AnalysisProgressDialogProps {
  open: boolean;
  onClose: () => void;
  analysisId: string;
  onComplete?: (analysisId: string) => void;
  onError?: (error: string) => void;
  onCancel?: (analysisId: string) => void;
}

const AnalysisProgressDialog: React.FC<AnalysisProgressDialogProps> = ({
  open,
  onClose,
  analysisId,
  onComplete,
  onError,
  onCancel
}) => {
  const theme = useTheme();
  const [progressData, setProgressData] = useState<ProgressData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);

  const getStageIcon = (stage: string, status: string) => {
    if (status === 'completed') return <CheckCircleIcon color="success" />;
    if (status === 'failed') return <ErrorIcon color="error" />;
    if (status === 'cancelled') return <ErrorIcon color="warning" />;
    
    switch (stage) {
      case 'pending':
        return <HourglassEmptyIcon color="warning" />;
      case 'parsing':
        return <AnalyticsIcon color="info" sx={{ animation: `${rotate} 2s linear infinite` }} />;
      case 'sentiment_analysis':
        return <PsychologyIcon color="info" sx={{ animation: `${pulse} 1.5s ease-in-out infinite` }} />;
      case 'aspect_analysis':
        return <TrendingUpIcon color="info" sx={{ animation: `${pulse} 1.5s ease-in-out infinite` }} />;
      case 'finalizing':
        return <AssessmentIcon color="info" sx={{ animation: `${pulse} 1.5s ease-in-out infinite` }} />;
      default:
        return <AnalyticsIcon color="info" />;
    }
  };

  const getProgressColor = (percentage: number, status: string) => {
    if (status === 'completed') return 'success';
    if (status === 'failed') return 'error';
    if (status === 'cancelled') return 'warning';
    if (percentage < 30) return 'warning';
    if (percentage < 70) return 'info';
    return 'primary';
  };

  const getStageDescription = (stage: string, status: string) => {
    if (status === 'completed') return 'Анализ успешно завершен!';
    if (status === 'failed') return 'Произошла ошибка при анализе';
    if (status === 'cancelled') return 'Анализ был отменен';
    
    switch (stage) {
      case 'pending':
        return 'Подготовка к анализу...';
      case 'parsing':
        return 'Загрузка и парсинг отзывов...';
      case 'sentiment_analysis':
        return 'Анализ тональности отзывов...';
      case 'aspect_analysis':
        return 'Анализ аспектов и категорий...';
      case 'finalizing':
        return 'Формирование итогового отчета...';
      default:
        return 'Обработка данных...';
    }
  };

  const cancelAnalysis = async () => {
    if (!analysisId || isCancelling) return;
    
    setIsCancelling(true);
    try {
      const token = localStorage.getItem('access_token');
      const url = `/api/v1/analyses/${analysisId}/cancel`;
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const result = await response.json();
        onCancel?.(analysisId);
        onClose();
      } else {
        const errorData = await response.json();
        const errorMessage = errorData.detail || 'Ошибка при отмене анализа';
        setError(`Ошибка отмены анализа: ${errorMessage}`);
      }
    } catch (err) {
      setError('Ошибка сети при отмене анализа');
    } finally {
      setIsCancelling(false);
    }
  };

  const fetchProgress = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(`/api/v1/analyses/progress/${analysisId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProgressData(data);
        setIsLoading(false);
        setError(null);

        if (data.status === 'completed') {
          setTimeout(() => {
            onComplete?.(analysisId);
          }, 1500); 
        } else if (data.status === 'failed') {
          setError('Анализ завершился с ошибкой');
          onError?.('Анализ завершился с ошибкой');
        } else if (data.status === 'cancelled') {
          setError('Анализ был отменен');
          onCancel?.(analysisId);
        }
      } else {
        const errorData = await response.json();
        let errorMessage = errorData.detail || 'Ошибка получения прогресса';
        
        if (response.status === 404) {
          errorMessage = 'Анализ не найден. Возможно, он был удален или у вас нет доступа к нему.';
        } else if (response.status === 403) {
          errorMessage = 'У вас нет доступа к этому анализу.';
        }
        
        setError(errorMessage);
        setIsLoading(false); 
        onError?.(errorMessage);
      }
    } catch (err) {
      setError('Ошибка сети при получении прогресса');
      setIsLoading(false); 
      onError?.('Ошибка сети при получении прогресса');
    }
  };

  useEffect(() => {
    if (!open || !analysisId) return;

    setIsLoading(true);
    setError(null);
    setProgressData(null);

    const initialTimeout = setTimeout(() => {
      fetchProgress();
    }, 500);

    const interval = setInterval(fetchProgress, 2000); 

    return () => {
      clearTimeout(initialTimeout);
      clearInterval(interval);
    };
  }, [open, analysisId]);

  useEffect(() => {
    if (!open || !analysisId) return;

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (progressData?.status === 'processing') {
        navigator.sendBeacon(
          `/api/v1/analyses/${analysisId}/cancel`,
          JSON.stringify({})
        );
        
        event.preventDefault();
        event.returnValue = 'Анализ будет отменен при закрытии страницы. Вы уверены?';
        return event.returnValue;
      }
    };

    const handleVisibilityChange = () => {
      if (document.hidden && progressData?.status === 'processing') {
        cancelAnalysis();
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [open, analysisId, progressData?.status]);

  const formatTime = (seconds?: number) => {
    if (!seconds) return 'неизвестно';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}м ${remainingSeconds}с`;
  };

  return (
    <Dialog
      open={open}
      onClose={progressData?.status === 'completed' ? onClose : undefined}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          borderRadius: 3,
          overflow: 'hidden'
        }
      }}
    >
      <DialogTitle sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
        color: 'white',
        pb: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <AnalyticsIcon />
          <Typography variant="h6">Анализ отзывов</Typography>
        </Box>
        {progressData?.status === 'completed' && (
          <IconButton onClick={onClose} sx={{ color: 'white' }}>
            <CloseIcon />
          </IconButton>
        )}
      </DialogTitle>

      <DialogContent sx={{ p: 3 }}>
        {isLoading ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4, mt: 3 }}>
            <CircularProgress size={60} sx={{ mb: 2 }} />
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Сбор отзывов с сайта...
            </Typography>
            {/* Кнопка отмены анализа в состоянии загрузки */}
            <Button
              variant="outlined"
              color="warning"
              onClick={cancelAnalysis}
              disabled={isCancelling}
              sx={{ minWidth: 150 }}
            >
              {isCancelling ? 'Отменяем...' : 'Остановить анализ'}
            </Button>
          </Box>
        ) : error ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4, mt: 3 }}>
            <ErrorIcon color="error" sx={{ fontSize: 60, mb: 2 }} />
            <Typography variant="h6" color="error" gutterBottom>
              Ошибка
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
              {error}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="outlined" onClick={fetchProgress}>
                Попробовать снова
              </Button>
              <Button variant="contained" onClick={onClose}>
                Закрыть
              </Button>
            </Box>
          </Box>
        ) : progressData ? (
          <Fade in={true} timeout={500}>
            <Box sx={{ mt: 3 }}>
              {/* Основная карточка прогресса */}
              <Card sx={{ 
                mb: 3, 
                background: progressData.status === 'completed' 
                  ? `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.1)}, ${alpha(theme.palette.success.main, 0.05)})` 
                  : `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)}, ${alpha(theme.palette.primary.main, 0.05)})`,
                border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`
              }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Zoom in={true} timeout={300}>
                      <Box sx={{ mr: 2 }}>
                        {getStageIcon(progressData.stage, progressData.status)}
                      </Box>
                    </Zoom>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" gutterBottom>
                        {progressData.stage_name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {getStageDescription(progressData.stage, progressData.status)}
                      </Typography>
                    </Box>
                    <Chip 
                      label={`${Math.round(progressData.progress_percentage)}%`}
                      color={getProgressColor(progressData.progress_percentage, progressData.status)}
                      sx={{ 
                        fontWeight: 'bold',
                        fontSize: '1rem',
                        animation: progressData.status === 'processing' ? `${pulse} 2s ease-in-out infinite` : 'none'
                      }}
                    />
                  </Box>

                  {/* Прогресс-бар */}
                  <Box sx={{ mb: 2 }}>
                    <LinearProgress
                      variant="determinate"
                      value={progressData.progress_percentage}
                      color={getProgressColor(progressData.progress_percentage, progressData.status)}
                      sx={{
                        height: 12,
                        borderRadius: 6,
                        backgroundColor: alpha(theme.palette.grey[300], 0.3),
                        '& .MuiLinearProgress-bar': {
                          borderRadius: 6,
                          background: progressData.status === 'processing' 
                            ? `linear-gradient(90deg, 
                                ${theme.palette.primary.main} 0%, 
                                ${theme.palette.primary.light} 50%, 
                                ${theme.palette.primary.main} 100%)`
                            : undefined,
                          backgroundSize: progressData.status === 'processing' ? '200px 100%' : 'auto',
                          animation: progressData.status === 'processing' ? `${shimmer} 2s infinite linear` : 'none'
                        }
                      }}
                    />
                  </Box>

                  {/* Статистика */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Обработано отзывов: {progressData.processed_reviews} / {progressData.total_reviews || '?'}
                    </Typography>
                    {progressData.estimated_time_remaining && (
                      <Typography variant="body2" color="text.secondary">
                        Осталось: {formatTime(progressData.estimated_time_remaining)}
                      </Typography>
                    )}
                  </Box>

                  {/* Кнопка отмены анализа */}
                  {progressData.status === 'processing' && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                      <Button
                        variant="outlined"
                        color="warning"
                        onClick={cancelAnalysis}
                        disabled={isCancelling}
                        sx={{ minWidth: 150 }}
                      >
                        {isCancelling ? 'Отменяем...' : 'Остановить анализ'}
                      </Button>
                    </Box>
                  )}
                </CardContent>
              </Card>

              {/* Этапы анализа */}
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                    Этапы анализа
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    {[
                      { key: 'pending', name: 'Подготовка', progress: 5 },
                      { key: 'parsing', name: 'Загрузка отзывов', progress: 30 },
                      { key: 'sentiment_analysis', name: 'Анализ тональности', progress: 60 },
                      { key: 'aspect_analysis', name: 'Анализ аспектов', progress: 85 },
                      { key: 'finalizing', name: 'Формирование отчета', progress: 100 }
                    ].map((stage, index) => {
                      const isCompleted = progressData.progress_percentage >= stage.progress;
                      const isCurrent = progressData.stage === stage.key;
                      
                      return (
                        <Slide 
                          key={stage.key} 
                          direction="right" 
                          in={true} 
                          timeout={300 + index * 100}
                        >
                          <Box sx={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            p: 1,
                            borderRadius: 1,
                            backgroundColor: isCurrent 
                              ? alpha(theme.palette.primary.main, 0.1)
                              : isCompleted 
                                ? alpha(theme.palette.success.main, 0.1)
                                : 'transparent',
                            border: isCurrent ? `1px solid ${theme.palette.primary.main}` : '1px solid transparent'
                          }}>
                            <Box sx={{ 
                              width: 24, 
                              height: 24, 
                              borderRadius: '50%',
                              backgroundColor: isCompleted 
                                ? theme.palette.success.main 
                                : isCurrent 
                                  ? theme.palette.primary.main
                                  : theme.palette.grey[300],
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              mr: 2,
                              transition: 'all 0.3s ease'
                            }}>
                              {isCompleted ? (
                                <CheckCircleIcon sx={{ fontSize: 16, color: 'white' }} />
                              ) : (
                                <Typography variant="caption" sx={{ color: 'white', fontWeight: 'bold' }}>
                                  {index + 1}
                                </Typography>
                              )}
                            </Box>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                fontWeight: isCurrent ? 'bold' : 'normal',
                                color: isCompleted ? 'success.main' : isCurrent ? 'primary.main' : 'text.secondary'
                              }}
                            >
                              {stage.name}
                            </Typography>
                            <Box sx={{ flexGrow: 1 }} />
                            <Typography variant="caption" color="text.secondary">
                              {stage.progress}%
                            </Typography>
                          </Box>
                        </Slide>
                      );
                    })}
                  </Box>
                </CardContent>
              </Card>
            </Box>
          </Fade>
        ) : null}
      </DialogContent>
    </Dialog>
  );
};

export default AnalysisProgressDialog; 