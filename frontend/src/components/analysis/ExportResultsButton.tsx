import React, { useState } from 'react';
import { 
  Button, 
  Menu, 
  MenuItem, 
  ListItemIcon, 
  ListItemText,
  Snackbar,
  Alert
} from '@mui/material';
import { 
  Save as SaveIcon,
  KeyboardArrowDown as ArrowDownIcon,
  Description as CsvIcon
} from '@mui/icons-material';

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

interface ExportResultsButtonProps {
  analysisId: string;
  exportData: ExportData;
  disabled?: boolean;
}

const ExportResultsButton: React.FC<ExportResultsButtonProps> = ({ analysisId, exportData, disabled = false }) => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const generateCSV = () => {
    let csvContent = 'Название,Значение\n';
    
    csvContent += `Товар,${exportData.productName}\n`;
    csvContent += `ID товара,${exportData.productId}\n`;
    csvContent += `Маркетплейс,${exportData.marketplace}\n`;
    csvContent += `Дата анализа,${new Date(exportData.date).toLocaleString()}\n`;
    csvContent += `Количество отзывов,${exportData.reviewsCount}\n\n`;
    
    csvContent += 'Тональность,Количество,Процент\n';
    const positivePercent = (exportData.positiveCount / exportData.reviewsCount * 100).toFixed(1);
    const negativePercent = (exportData.negativeCount / exportData.reviewsCount * 100).toFixed(1);
    const neutralPercent = (exportData.neutralCount / exportData.reviewsCount * 100).toFixed(1);
    
    csvContent += `Положительные,${exportData.positiveCount},${positivePercent}%\n`;
    csvContent += `Отрицательные,${exportData.negativeCount},${negativePercent}%\n`;
    csvContent += `Нейтральные,${exportData.neutralCount},${neutralPercent}%\n\n`;
    
    csvContent += 'Положительные аспекты,Частота,Отрицательные аспекты,Частота\n';
    
    const maxLength = Math.max(exportData.positiveAspects.length, exportData.negativeAspects.length);
    
    for (let i = 0; i < maxLength; i++) {
      const positiveAspect = i < exportData.positiveAspects.length 
        ? `"${exportData.positiveAspects[i].aspect}"` 
        : '';
      const positiveCount = i < exportData.positiveAspects.length 
        ? exportData.positiveAspects[i].count 
        : '';
      const negativeAspect = i < exportData.negativeAspects.length 
        ? `"${exportData.negativeAspects[i].aspect}"` 
        : '';
      const negativeCount = i < exportData.negativeAspects.length 
        ? exportData.negativeAspects[i].count 
        : '';
      
      csvContent += `${positiveAspect},${positiveCount},${negativeAspect},${negativeCount}\n`;
    }
    
    return csvContent;
  };

  const downloadCSV = () => {
    const csvContent = generateCSV();
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `analysis_${analysisId}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleExport = async () => {
    setLoading(true);
    setError(null);
    handleClose();

    try {
      downloadCSV();
      setSuccess('Экспорт в CSV успешно выполнен');
    } catch (err) {
      console.error('Ошибка при экспорте результатов:', err);
      setError('Не удалось экспортировать результаты. Попробуйте позже.');
    } finally {
      setLoading(false);
    }
  };

  const handleCloseSnackbar = () => {
    setError(null);
    setSuccess(null);
  };

  return (
    <>
      <Button
        variant="contained"
        color="primary"
        onClick={handleExport}
        startIcon={<CsvIcon />}
        disabled={disabled || loading}
      >
        Экспорт в CSV
      </Button>
      
      {/* Уведомления об ошибках и успешном экспорте */}
      <Snackbar open={!!error} autoHideDuration={6000} onClose={handleCloseSnackbar}>
        <Alert onClose={handleCloseSnackbar} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
      
      <Snackbar open={!!success} autoHideDuration={6000} onClose={handleCloseSnackbar}>
        <Alert onClose={handleCloseSnackbar} severity="success" sx={{ width: '100%' }}>
          {success}
        </Alert>
      </Snackbar>
    </>
  );
};

export default ExportResultsButton; 