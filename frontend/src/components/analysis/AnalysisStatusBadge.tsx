import React from 'react';
import { Chip, Tooltip } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import PendingIcon from '@mui/icons-material/Pending';

type AnalysisStatus = 'completed' | 'failed' | 'processing' | 'pending';

interface AnalysisStatusBadgeProps {
  status: AnalysisStatus;
}


const AnalysisStatusBadge: React.FC<AnalysisStatusBadgeProps> = ({ status }) => {
  const getStatusProps = () => {
    switch (status) {
      case 'completed':
        return {
          icon: <CheckCircleIcon fontSize="small" />,
          label: 'Завершен',
          color: 'success' as const,
          tooltip: 'Анализ успешно завершен'
        };
      case 'failed':
        return {
          icon: <ErrorIcon fontSize="small" />,
          label: 'Ошибка',
          color: 'error' as const,
          tooltip: 'Произошла ошибка при анализе'
        };
      case 'processing':
        return {
          icon: <HourglassEmptyIcon fontSize="small" />,
          label: 'Выполняется',
          color: 'primary' as const,
          tooltip: 'Анализ в процессе выполнения'
        };
      case 'pending':
        return {
          icon: <PendingIcon fontSize="small" />,
          label: 'В очереди',
          color: 'warning' as const,
          tooltip: 'Анализ ожидает обработки'
        };
      default:
        return {
          icon: <PendingIcon fontSize="small" />,
          label: 'Неизвестно',
          color: 'default' as const,
          tooltip: 'Неизвестный статус анализа'
        };
    }
  };

  const { icon, label, color, tooltip } = getStatusProps();

  return (
    <Tooltip title={tooltip}>
      <Chip
        icon={icon}
        label={label}
        color={color}
        size="small"
        variant="outlined"
      />
    </Tooltip>
  );
};

export default AnalysisStatusBadge; 