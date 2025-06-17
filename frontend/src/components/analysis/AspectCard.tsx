import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Divider,
  Grid,
  Paper
} from '@mui/material';

interface AspectItemDetail {
  text: string;
  count: number;
  percentage_total_sentiment: number;
}

interface AspectCategory {
  name: string;
  total_mentions_in_category: number;
  aspects: AspectItemDetail[];
}

interface SentimentAspectsData {
  total_aspect_mentions: number;
  categories: AspectCategory[];
}

interface AspectCardProps {
  title: string;
  data: SentimentAspectsData | null | undefined;
  sentiment: 'positive' | 'negative';
}

const AspectCard: React.FC<AspectCardProps> = ({ title, data, sentiment }) => {


  if (!data || data.categories.length === 0) {
    return (
      <Card elevation={1} sx={{ mb: 2, p:2, borderRadius: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
            {title}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            {sentiment === 'positive' ? 'Положительные' : 'Отрицательные'} аспекты не найдены.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const totalAspectMentionsForSentiment = data.total_aspect_mentions;

  return (
    <Paper elevation={1} sx={{ mb: 3, borderRadius: 2, p: 2}}>
      <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 'bold', textAlign: 'center', mb: 2 }}>
        {title.toUpperCase()}
      </Typography>
      <Typography variant="subtitle1" gutterBottom sx={{ textAlign: 'center', mb: 3 }}>
        Всего уникальных аспектов: {data.categories.reduce((sum, category) => sum + category.aspects.length, 0)}
      </Typography>

      {data.categories.map((category, categoryIndex) => (
        <Box key={categoryIndex} sx={{ mb: 3 }}>
          <Typography variant="h6" component="h3" sx={{ fontWeight: 'medium', textTransform: 'uppercase', color: sentiment === 'positive' ? 'success.dark' : 'error.dark' }}>
            {category.name}
          </Typography>
          <Typography variant="caption" display="block" gutterBottom color="text.secondary" sx={{mb:1}}>
            (Упоминаний в категории: {category.aspects.length})
          </Typography>
          <Divider sx={{ mb: 1 }} />
          {category.aspects.length > 0 ? (
            <List dense disablePadding>
              {category.aspects.map((aspect, aspectIndex) => (
                <ListItem key={aspectIndex} disableGutters sx={{pt:0, pb:0}}>
                  <Grid container alignItems="center" spacing={1}>
                    <Grid item xs={0.5} sm={0.5} sx={{textAlign: 'right'}}>
                      <Typography variant="body2">{aspectIndex + 1}.</Typography>
                    </Grid>
                    <Grid item xs={11.5} sm={11.5}>
                      <ListItemText 
                        primary={<Typography variant="body2">{aspect.text || '[ПУСТОЙ ТЕКСТ]'}</Typography>} 
                      />
                    </Grid>
                  </Grid>
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', ml: 2 }}>
              Аспекты в этой категории не найдены.
            </Typography>
          )}
        </Box>
      ))}
    </Paper>
  );
};

export default AspectCard; 