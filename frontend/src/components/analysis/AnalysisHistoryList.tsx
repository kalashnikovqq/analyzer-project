import React, { useState, useEffect } from 'react';
import { Box, Typography, CircularProgress, Alert, Grid, Pagination } from '@mui/material';
import AnalysisHistoryItem, { AnalysisHistoryItemData } from './AnalysisHistoryItem';

interface AnalysisHistoryListProps {
  data?: AnalysisHistoryItemData[];
  isLoading?: boolean;
  error?: string | null;
  onDelete?: (id: string) => void;
}

const AnalysisHistoryList: React.FC<AnalysisHistoryListProps> = ({
  data = [],
  isLoading = false,
  error = null,
  onDelete
}) => {
  const [page, setPage] = useState(1);
  const itemsPerPage = 6;
  const totalPages = Math.ceil(data.length / itemsPerPage);
  
  const startIndex = (page - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = data.slice(startIndex, endIndex);
  
  useEffect(() => {
    setPage(1);
  }, [data.length]);
  
  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };
  
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        {error}
      </Alert>
    );
  }
  
  // Если список пуст
  if (data.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body1" color="text.secondary">
          История анализов пуста. Создайте новый анализ, чтобы он появился здесь.
        </Typography>
      </Box>
    );
  }
  
  return (
    <Box>
      <Grid container spacing={3}>
        {currentItems.map((item) => (
          <Grid item xs={12} sm={6} md={4} key={item.id}>
            <AnalysisHistoryItem 
              data={item} 
              onDelete={onDelete ? () => onDelete(item.id) : undefined} 
            />
          </Grid>
        ))}
      </Grid>
      
      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <Pagination 
            count={totalPages} 
            page={page} 
            onChange={handlePageChange} 
            color="primary" 
          />
        </Box>
      )}
    </Box>
  );
};

export default AnalysisHistoryList; 