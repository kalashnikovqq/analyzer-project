import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  CircularProgress, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemAvatar, 
  Avatar, 
  Chip,
  LinearProgress,
  Divider,
  Button,
  useTheme,
  alpha
} from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store';
import { fetchAllAnalyses } from '../../store/slices/analysisSlice';
import LoopIcon from '@mui/icons-material/Loop';
import ErrorIcon from '@mui/icons-material/Error';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import { Link } from 'react-router-dom';
import { formatDistance } from 'date-fns';
import { ru } from 'date-fns/locale';
import { keyframes } from '@mui/system';

const shimmer = keyframes`
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: calc(200px + 100%) 0;
  }
`;

const POLLING_INTERVAL = 5000;

const ActiveAnalysisList: React.FC = () => {
  const dispatch = useDispatch();
  const theme = useTheme();
  const { analyses, loading } = useSelector((state: RootState) => state.analysis);
  
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  useEffect(() => {
    dispatch(fetchAllAnalyses() as any);
    
    const intervalId = setInterval(() => {
      dispatch(fetchAllAnalyses() as any);
      
      setIsRefreshing(true);
      setTimeout(() => setIsRefreshing(false), 500);
    }, POLLING_INTERVAL);
    
    return () => clearInterval(intervalId);
  }, [dispatch]);
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <HourglassEmptyIcon color="warning" />;
      case 'processing':
        return <LoopIcon color="info" />;
      case 'completed':
        return <CheckCircleOutlineIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      default:
        return <HourglassEmptyIcon />;
    }
  };
  
  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending':
        return 'Ожидает';
      case 'processing':
        return 'Обрабатывается';
      case 'completed':
        return 'Завершен';
      case 'failed':
        return 'Ошибка';
      default:
        return 'Неизвестно';
    }
  };
  
  const getStatusColor = (status: string): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    switch (status) {
      case 'pending':
        return 'warning';
      case 'processing':
        return 'info';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };
  
  const calculateProgress = (analysis: any) => {
    if (analysis.status === 'completed') return 100;
    if (analysis.status === 'failed') return 0;
    
    if (analysis.status === 'pending') return 5;
    if (analysis.status === 'processing') {
      const stage = analysis.stage || 'processing';
      switch (stage) {
        case 'parsing': return 30;
        case 'sentiment_analysis': return 60;
        case 'aspect_analysis': return 85;
        case 'finalizing': return 95;
        default: return 50;
      }
    }
    
    return 0;
  };
  
  const formatElapsedTime = (startTime: string) => {
    try {
      return formatDistance(new Date(startTime), new Date(), { 
        addSuffix: true,
        locale: ru
      });
    } catch (error) {
      return 'неизвестно';
    }
  };
  
  const handleRefresh = () => {
    setIsRefreshing(true);
    dispatch(fetchAllAnalyses() as any).then(() => {
      setTimeout(() => setIsRefreshing(false), 500);
    });
  };
  
  return (
    <Paper elevation={3} sx={{ p: 3, borderRadius: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" component="h3" gutterBottom>
          Активные анализы
        </Typography>
        
        <Button 
          startIcon={<LoopIcon />} 
          onClick={handleRefresh}
          disabled={loading || isRefreshing}
        >
          Обновить
        </Button>
      </Box>
      
      {isRefreshing && <LinearProgress sx={{ mb: 2 }} />}
      
      {loading && !analyses.length ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : !analyses.length ? (
        <Typography variant="body1" color="text.secondary" sx={{ p: 2, textAlign: 'center' }}>
          Нет активных анализов
        </Typography>
      ) : (
        <List>
          {analyses.map((analysis, index) => (
            <React.Fragment key={analysis.id}>
              {index > 0 && <Divider component="li" />}
              <ListItem 
                alignItems="flex-start" 
                component={analysis.status === 'completed' ? Link : 'div'}
                to={analysis.status === 'completed' ? `/analysis/result/${analysis.id}` : undefined}
                sx={{ 
                  cursor: analysis.status === 'completed' ? 'pointer' : 'default',
                  '&:hover': { 
                    bgcolor: analysis.status === 'completed' ? 'action.hover' : 'inherit'
                  }
                }}
              >
                <ListItemAvatar>
                  <Avatar>
                    <ShoppingBagIcon />
                  </Avatar>
                </ListItemAvatar>
                
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                      <Typography variant="subtitle1" component="span">
                        {analysis.url || `Анализ ${analysis.id.substring(0, 8)}`}
                      </Typography>
                      <Chip 
                        label={getStatusText(analysis.status)} 
                        color={getStatusColor(analysis.status)}
                        size="small"
                        icon={getStatusIcon(analysis.status)}
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" component="span" color="text.secondary">
                        {analysis.platform === 'wildberries' ? 'Wildberries' : 'Ozon'} • 
                        ID: {analysis.id.substring(0, 8)} • 
                        Начат {formatElapsedTime(analysis.created_at)}
                      </Typography>
                      
                      <Box sx={{ mt: 1, mb: 0.5 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={calculateProgress(analysis)} 
                          color={analysis.status === 'completed' ? 'success' : analysis.status === 'failed' ? 'error' : 'primary'}
                          sx={{ 
                            height: 8, 
                            borderRadius: 4,
                            backgroundColor: alpha(theme.palette.grey[300], 0.3),
                            '& .MuiLinearProgress-bar': {
                              borderRadius: 4,
                              background: analysis.status === 'processing' 
                                ? `linear-gradient(90deg, 
                                    ${theme.palette.primary.main} 0%, 
                                    ${theme.palette.primary.light} 50%, 
                                    ${theme.palette.primary.main} 100%)`
                                : undefined,
                              backgroundSize: analysis.status === 'processing' ? '200px 100%' : 'auto',
                              animation: analysis.status === 'processing' ? `${shimmer} 2s infinite linear` : 'none'
                            }
                          }}
                        />
                      </Box>
                      
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" component="span" color="text.secondary">
                        {analysis.status === 'completed' 
                          ? `${analysis.reviews_count || 0} отзывов обработано` 
                          : (analysis.status === 'processing' 
                              ? 'Обработка отзывов...' 
                              : 'Ожидание начала обработки')}
                      </Typography>
                        <Typography variant="body2" component="span" color="primary.main" sx={{ fontWeight: 'bold' }}>
                          {Math.round(calculateProgress(analysis))}%
                        </Typography>
                      </Box>
                    </Box>
                  }
                />
              </ListItem>
            </React.Fragment>
          ))}
        </List>
      )}
    </Paper>
  );
};

export default ActiveAnalysisList; 