import React from 'react';
import { Box, Container, Typography, Link, Grid } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const Footer: React.FC = () => {
  return (
    <Box
      component="footer"
      sx={{
        py: 3,
        px: 2,
        mt: 'auto',
        backgroundColor: (theme) =>
          theme.palette.mode === 'light'
            ? theme.palette.grey[200]
            : theme.palette.grey[800],
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={3}>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              О проекте
            </Typography>
            <Typography variant="body2" color="text.secondary">
              FeedbackLab - современная платформа для анализа отзывов с маркетплейсов Wildberries и Ozon с использованием искусственного интеллекта.
            </Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Ссылки
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <Link component={RouterLink} to="/" color="inherit">
                Главная
              </Link>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <Link component={RouterLink} to="/analysis/new" color="inherit">
                Новый анализ
              </Link>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <Link component={RouterLink} to="/login" color="inherit">
                Вход
              </Link>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <Link component={RouterLink} to="/register" color="inherit">
                Регистрация
              </Link>
            </Typography>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Контакты
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Email: stud0000238584@utmn.ru
            </Typography>
          </Grid>
        </Grid>
        <Box mt={3}>
          <Typography variant="body2" color="text.secondary" align="center">
            {"© "}
            <Link color="inherit" component={RouterLink} to="/">
              FeedbackLab
            </Link>{" "}
            {new Date().getFullYear()}
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer; 