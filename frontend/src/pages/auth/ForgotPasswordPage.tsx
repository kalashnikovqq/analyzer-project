import React, { useState } from 'react';
import { 
  Container, 
  Box, 
  Typography, 
  TextField, 
  Button, 
  Grid, 
  Link, 
  Paper,
  Alert
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import LockResetIcon from '@mui/icons-material/LockReset';

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    
    if (!email) {
      setError('Пожалуйста, введите email');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // Здесь будет API-запрос для восстановления пароля
      
      // Имитация успешного запроса
      setTimeout(() => {
        setSuccess(true);
        setLoading(false);
      }, 1000);
      
    } catch (err) {
      setError('Ошибка при восстановлении пароля. Проверьте email и попробуйте снова.');
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Paper elevation={3} sx={{ p: 4, mt: 8, borderRadius: 2 }}>
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <Box 
            sx={{ 
              p: 2, 
              bgcolor: 'primary.main', 
              color: 'white', 
              borderRadius: '50%',
              mb: 2
            }}
          >
            <LockResetIcon />
          </Box>
          <Typography component="h1" variant="h5">
            Восстановление пароля
          </Typography>
          
          {error && (
            <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
              {error}
            </Alert>
          )}
          
          {success ? (
            <Box sx={{ mt: 4, textAlign: 'center' }}>
              <Alert severity="success" sx={{ mb: 3 }}>
                Инструкции по сбросу пароля отправлены на указанный email.
              </Alert>
              <Typography variant="body1" gutterBottom>
                Пожалуйста, проверьте вашу почту и следуйте инструкциям для сброса пароля.
              </Typography>
              <Button
                component={RouterLink}
                to="/login"
                variant="contained"
                sx={{ mt: 3 }}
              >
                Вернуться на страницу входа
              </Button>
            </Box>
          ) : (
            <Box component="form" onSubmit={handleSubmit} noValidate sx={{ mt: 1, width: '100%' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 2 }}>
                Введите ваш email, и мы отправим вам инструкции по сбросу пароля.
              </Typography>
              
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="Email"
                name="email"
                autoComplete="email"
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              
              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2 }}
                disabled={loading}
              >
                {loading ? 'Отправка...' : 'Отправить инструкции'}
              </Button>
              
              <Grid container>
                <Grid item xs>
                  <Link component={RouterLink} to="/login" variant="body2">
                    Вернуться ко входу
                  </Link>
                </Grid>
                <Grid item>
                  <Link component={RouterLink} to="/register" variant="body2">
                    {"Нет аккаунта? Зарегистрируйтесь"}
                  </Link>
                </Grid>
              </Grid>
            </Box>
          )}
        </Box>
      </Paper>
    </Container>
  );
};

export default ForgotPasswordPage; 