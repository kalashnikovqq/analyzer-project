import React, { useState } from 'react';
import { Card, CardContent, CardActions, Typography, Chip, IconButton, Box, Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import VisibilityIcon from '@mui/icons-material/Visibility';
import { useNavigate } from 'react-router-dom';
import { formatDate } from '../../utils/formatters';

export interface AnalysisHistoryItemData {
  id: string;
  productName: string;
  marketplace: 'wildberries' | 'ozon';
  date: string;
  reviewCount: number;
  positivePercent: number;
  negativePercent: number;
  neutralPercent: number;
}

interface AnalysisHistoryItemProps {
  data: AnalysisHistoryItemData;
  onDelete?: () => void;
}

const AnalysisHistoryItem: React.FC<AnalysisHistoryItemProps> = ({ data, onDelete }) => {
  const navigate = useNavigate();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  
  const getSentimentColor = () => {
    if (data.positivePercent > data.negativePercent && data.positivePercent > data.neutralPercent) {
      return 'success.main';
    } else if (data.negativePercent > data.positivePercent && data.negativePercent > data.neutralPercent) {
      return 'error.main';
    } else {
      return 'info.main';
    }
  };
  
  const marketplaceLabels = {
    'wildberries': 'Wildberries',
    'ozon': 'Ozon'
  };
  
  const handleView = () => {
    navigate(`/analysis/result/${data.id}`);
  };
  
  const handleOpenDeleteDialog = (e: React.MouseEvent) => {
    e.stopPropagation();
    setDeleteDialogOpen(true);
  };
  
  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
  };
  
  const handleConfirmDelete = () => {
    if (onDelete) {
      onDelete();
    }
    setDeleteDialogOpen(false);
  };
  
  return (
    <>
      <Card sx={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 6,
          cursor: 'pointer'
        }
      }} onClick={handleView}>
        <CardContent sx={{ flexGrow: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Chip 
              label={marketplaceLabels[data.marketplace]} 
              size="small" 
              color={data.marketplace === 'wildberries' ? 'secondary' : 'primary'} 
            />
            <Typography variant="caption" color="text.secondary">
              {formatDate(data.date)}
            </Typography>
          </Box>
          
          <Typography variant="h6" noWrap title={data.productName}>
            {data.productName.length > 40 
              ? `${data.productName.substring(0, 40)}...` 
              : data.productName}
          </Typography>
          
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Проанализировано отзывов: {data.reviewCount}
          </Typography>
          
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ 
                width: 12, 
                height: 12, 
                borderRadius: '50%', 
                bgcolor: 'success.main', 
                mr: 1 
              }} />
              <Typography variant="body2">{Math.round(data.positivePercent)}%</Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ 
                width: 12, 
                height: 12, 
                borderRadius: '50%', 
                bgcolor: 'error.main', 
                mr: 1 
              }} />
              <Typography variant="body2">{Math.round(data.negativePercent)}%</Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Box sx={{ 
                width: 12, 
                height: 12, 
                borderRadius: '50%', 
                bgcolor: 'info.main', 
                mr: 1 
              }} />
              <Typography variant="body2">{Math.round(data.neutralPercent)}%</Typography>
            </Box>
          </Box>
        </CardContent>
        
        <CardActions sx={{ justifyContent: 'flex-end', p: 1 }}>
          <IconButton 
            size="small" 
            onClick={handleView} 
            aria-label="смотреть результаты"
          >
            <VisibilityIcon fontSize="small" />
          </IconButton>
          
          {onDelete && (
            <IconButton 
              size="small" 
              onClick={handleOpenDeleteDialog} 
              aria-label="удалить анализ"
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
          )}
        </CardActions>
      </Card>
      
      {/* Диалог подтверждения удаления */}
      <Dialog open={deleteDialogOpen} onClose={handleCloseDeleteDialog}>
        <DialogTitle>Удаление анализа</DialogTitle>
        <DialogContent>
          <Typography>
            Вы уверены, что хотите удалить анализ продукта "{data.productName}"?
            Это действие нельзя отменить.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog}>Отмена</Button>
          <Button onClick={handleConfirmDelete} color="error" variant="contained">
            Удалить
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default AnalysisHistoryItem; 