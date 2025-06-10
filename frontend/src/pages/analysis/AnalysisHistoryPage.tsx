import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { 
  Box, Typography, Paper, Container, Grid, Card, CardContent, 
  CardActions, Button, Chip, IconButton, Dialog, DialogTitle, 
  DialogContent, DialogContentText, DialogActions, Pagination, CardHeader, Tooltip
} from '@mui/material';
import { 
  Delete as DeleteIcon, 
  Visibility as ViewIcon
} from '@mui/icons-material';

import { RootState } from '../../store';
import { fetchAllAnalyses, deleteAnalysis, exportAnalysis } from '../../store/slices/analysisSlice';
import { formatDate } from '../../utils/formatters';
import LoadingIndicator from '../../components/LoadingIndicator';
import ExportResultsButton from '../../components/analysis/ExportResultsButton';

const AnalysisHistoryPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { analyses, loading, error } = useSelector((state: RootState) => state.analysis);
  
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  
  const [page, setPage] = useState(1);
  const itemsPerPage = 9;
  
  useEffect(() => {
    dispatch(fetchAllAnalyses() as any);
  }, [dispatch]);
  
  const paginatedAnalyses = analyses.slice(
    (page - 1) * itemsPerPage,
    page * itemsPerPage
  );
  
  const handleViewAnalysis = (id: string) => {
    navigate(`/analysis/result/${id}`);
  };
  
  const handleDeleteClick = (id: string) => {
    setSelectedAnalysisId(id);
    setDeleteDialogOpen(true);
  };
  
  const confirmDelete = () => {
    if (selectedAnalysisId) {
      dispatch(deleteAnalysis(selectedAnalysisId) as any);
      setDeleteDialogOpen(false);
      setSelectedAnalysisId(null);
    }
  };
  
  const cancelDelete = () => {
    setDeleteDialogOpen(false);
    setSelectedAnalysisId(null);
  };
  
  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };
  
  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Завершен';
      case 'processing':
        return 'Обрабатывается';
      case 'pending':
        return 'В очереди';
      case 'failed':
        return 'Ошибка';
      default:
        return status;
    }
  };
  
  if (loading && analyses.length === 0) {
    return <LoadingIndicator />;
  }
  
  return (
    <Container maxWidth="lg">
      <Box my={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          История анализов
        </Typography>
        
        {error && (
          <Paper elevation={0} sx={{ p: 2, mb: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
            <Typography>{error}</Typography>
          </Paper>
        )}
        
        {analyses.length === 0 ? (
          <Paper elevation={3} sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6">
              У вас пока нет выполненных анализов
            </Typography>
            <Button 
              variant="contained" 
              color="primary" 
              sx={{ mt: 2 }}
              onClick={() => navigate('/analysis/new')}
            >
              Создать новый анализ
            </Button>
          </Paper>
        ) : (
          <>
            <Grid container spacing={3}>
              {paginatedAnalyses.map((analysis) => (
                <Grid item xs={12} sm={6} md={4} key={analysis.id}>
                  <Card sx={{
                    borderRadius: 2,
                    border: '1px solid',
                    borderColor: 'divider',
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                    '&:hover': {
                      boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
                      transform: 'translateY(-4px)',
                      borderColor: 'primary.main'
                    }
                  }}>
                    <Box 
                      sx={{ 
                        height: 100, 
                        background: analysis.marketplace === 'wb' 
                          ? 'linear-gradient(135deg, #8B5A96 0%, #A66FB3 100%)'
                          : analysis.marketplace === 'ozon' 
                          ? 'linear-gradient(135deg, #005BFF 0%, #0077FF 100%)'
                          : 'linear-gradient(135deg, #6C7B7F 0%, #8B9A9F 100%)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold', textTransform: 'uppercase' }}>
                        {analysis.marketplace || analysis.platform}
                      </Typography>
                    </Box>
                    
                    <CardContent sx={{ p: 2.5 }}>
                      <Typography 
                        variant="h6" 
                        component="h3" 
                        sx={{ 
                          fontSize: '1.1rem',
                          fontWeight: 600,
                          lineHeight: 1.3,
                          mb: 1.5,
                          color: 'text.primary'
                        }}
                      >
                        {analysis.product_name || `Товар ${analysis.platform || 'неизвестен'}`}
                      </Typography>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
                          ID: {analysis.product_id || analysis.id}
                        </Typography>
                        <Box sx={{ mx: 1, width: 3, height: 3, borderRadius: '50%', bgcolor: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.85rem' }}>
                          {formatDate(analysis.created_at)}
                        </Typography>
                      </Box>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.9rem' }}>
                          Отзывов: <strong>{analysis.reviews_count || 0}</strong>
                        </Typography>
                        {analysis.status === 'completed' && (
                          <Chip 
                            label="Готово" 
                            size="small" 
                            sx={{ 
                              bgcolor: 'success.light', 
                              color: 'success.dark',
                              fontSize: '0.75rem',
                              height: 24
                            }} 
                          />
                        )}
                        {analysis.status === 'failed' && (
                          <Chip 
                            label="Ошибка" 
                            size="small" 
                            sx={{ 
                              bgcolor: 'error.light', 
                              color: 'error.dark',
                              fontSize: '0.75rem',
                              height: 24
                            }} 
                          />
                        )}
                        {(analysis.status === 'pending' || analysis.status === 'processing') && (
                          <Chip 
                            label="В работе" 
                            size="small" 
                            sx={{ 
                              bgcolor: 'warning.light', 
                              color: 'warning.dark',
                              fontSize: '0.75rem',
                              height: 24
                            }} 
                          />
                        )}
                      </Box>
                    </CardContent>
                    <Box sx={{ 
                      p: 2, 
                      display: 'flex', 
                      justifyContent: 'space-between', 
                      alignItems: 'center',
                      gap: 1,
                      borderTop: '1px solid',
                      borderColor: 'divider',
                      bgcolor: '#2d2d2d'
                    }}>
                      {analysis.status === 'completed' && (
                        <Button
                          variant="contained"
                          startIcon={<ViewIcon />}
                          onClick={() => handleViewAnalysis(analysis.id)}
                          sx={{ 
                            bgcolor: 'primary.main',
                            color: 'white',
                            '&:hover': { bgcolor: 'primary.dark' },
                            textTransform: 'none',
                            borderRadius: 2,
                            px: 2,
                            py: 1
                          }}
                        >
                          Посмотреть
                        </Button>
                      )}
                      
                      <Box sx={{ display: 'flex', gap: 1, ml: 'auto' }}>
                        <Tooltip title="Удалить анализ">
                          <IconButton 
                            onClick={() => handleDeleteClick(analysis.id)}
                            size="small"
                            sx={{ 
                              bgcolor: 'error.main',
                              color: 'white',
                              '&:hover': { bgcolor: 'error.dark' }
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>
                  </Card>
                </Grid>
              ))}
            </Grid>
            
            {analyses.length > itemsPerPage && (
              <Box display="flex" justifyContent="center" mt={4}>
                <Pagination 
                  count={Math.ceil(analyses.length / itemsPerPage)} 
                  page={page} 
                  onChange={handlePageChange} 
                  color="primary" 
                />
              </Box>
            )}
          </>
        )}
      </Box>
      
      {/* Диалог подтверждения удаления */}
      <Dialog
        open={deleteDialogOpen}
        onClose={cancelDelete}
      >
        <DialogTitle>Удаление анализа</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Вы уверены, что хотите удалить этот анализ? Это действие нельзя будет отменить.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={cancelDelete}>Отменить</Button>
          <Button onClick={confirmDelete} color="error">Удалить</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AnalysisHistoryPage; 