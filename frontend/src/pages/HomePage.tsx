import React from 'react';
import { 
  Box, 
  Typography, 
  Button, 
  Grid, 
  Card, 
  CardContent,
  Paper
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import ShoppingBagIcon from '@mui/icons-material/ShoppingBag';
import CommentIcon from '@mui/icons-material/Comment';

const HomePage: React.FC = () => {
  return (
    <Box>
      <Paper
        sx={{
          position: 'relative',
          backgroundColor: 'grey.800',
          color: '#fff',
          mb: 4,
          p: 6,
          borderRadius: 2
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            right: 0,
            left: 0,
            backgroundColor: 'rgba(0,0,0,.5)',
            borderRadius: 2
          }}
        />
        <Grid container>
          <Grid item md={6}>
            <Box sx={{ position: 'relative', p: { xs: 3, md: 6 } }}>
              <Typography variant="h3" color="inherit" gutterBottom>
                Аналитика отзывов с маркетплейсов
              </Typography>
              <Typography variant="h5" color="inherit" paragraph>
                Получите ценную информацию из отзывов о товарах на Wildberries и Ozon с помощью искусственного интеллекта
              </Typography>
              <Button 
                variant="contained" 
                size="large" 
                component={RouterLink} 
                to="/analysis/new"
              >
                Начать анализ
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      <Box sx={{ mb: 6 }}>
        <Typography variant="h4" component="h2" align="center" gutterBottom>
          Наши преимущества
        </Typography>
        <Grid container spacing={4} sx={{ mt: 2 }}>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <AnalyticsIcon fontSize="large" color="primary" sx={{ mb: 2 }} />
                <Typography gutterBottom variant="h5" component="h3">
                  Интеллектуальный анализ
                </Typography>
                <Typography>
                  Используем современные методы машинного обучения для выделения ключевых аспектов из отзывов покупателей.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <ShoppingBagIcon fontSize="large" color="primary" sx={{ mb: 2 }} />
                <Typography gutterBottom variant="h5" component="h3">
                  Поддержка популярных маркетплейсов
                </Typography>
                <Typography>
                  Анализируем отзывы с Wildberries и Ozon — крупнейших маркетплейсов в России.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <CommentIcon fontSize="large" color="primary" sx={{ mb: 2 }} />
                <Typography gutterBottom variant="h5" component="h3">
                  Категоризация аспектов
                </Typography>
                <Typography>
                  Автоматически выделяем плюсы и минусы товаров, категоризируем их по типам и представляем в удобном формате.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>

      <Box sx={{ bgcolor: 'background.paper', p: 6, textAlign: 'center', borderRadius: 2 }}>
        <Typography variant="h4" component="h2" gutterBottom>
          Готовы узнать, что думают покупатели?
        </Typography>
        <Typography variant="body1" paragraph>
          Просто укажите ссылку на товар или его артикул, и мы проанализируем все отзывы для вас.
        </Typography>
        <Button 
          variant="contained" 
          size="large" 
          component={RouterLink} 
          to="/analysis/new"
          sx={{ mt: 2 }}
        >
          Начать анализ
        </Button>
      </Box>
    </Box>
  );
};

export default HomePage; 