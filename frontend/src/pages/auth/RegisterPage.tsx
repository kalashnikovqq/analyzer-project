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
  InputAdornment,
  IconButton,
  Alert,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import Visibility from '@mui/icons-material/Visibility';
import VisibilityOff from '@mui/icons-material/VisibilityOff';
import { useDispatch } from 'react-redux';
import { register } from '../../store/slices/authSlice';

const steps = ['Личная информация', 'Создание аккаунта', 'Завершение'];

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const [activeStep, setActiveStep] = useState(0);
  
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleNext = () => {
    if (activeStep === 0) {
      if (!firstName || !lastName) {
        setError('Пожалуйста, заполните все поля');
        return;
      }
    } else if (activeStep === 1) {
      if (!email || !password || !confirmPassword) {
        setError('Пожалуйста, заполните все поля');
        return;
      }
      
      if (password !== confirmPassword) {
        setError('Пароли не совпадают');
        return;
      }
      
      if (password.length < 8) {
        setError('Пароль должен содержать не менее 8 символов');
        return;
      }
    }
    
    setError('');
    setActiveStep((prevActiveStep) => prevActiveStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    
    if (activeStep < 2) {
      handleNext();
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const result = await dispatch(register({
        email,
        password,
        username: `${firstName} ${lastName}`
      }) as any);
      
      if (register.fulfilled.match(result)) {
        navigate('/');
      } else {
        setError(result.payload || 'Ошибка при регистрации. Пожалуйста, попробуйте позже.');
      }
      
    } catch (err: any) {
      console.error('Registration error:', err);
      setError(err.response?.data?.detail || 'Ошибка при регистрации. Пожалуйста, попробуйте позже.');
    } finally {
      setLoading(false);
    }
  };

  const handleClickShowPassword = () => {
    setShowPassword(!showPassword);
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <>
            <TextField
              margin="normal"
              required
              fullWidth
              id="firstName"
              label="Имя"
              name="firstName"
              autoComplete="given-name"
              autoFocus
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              id="lastName"
              label="Фамилия"
              name="lastName"
              autoComplete="family-name"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
            />
          </>
        );
      case 1:
        return (
          <>
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email"
              name="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="Пароль"
              type={showPassword ? 'text' : 'password'}
              id="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label="toggle password visibility"
                      onClick={handleClickShowPassword}
                      edge="end"
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
            />
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Подтвердите пароль"
              type={showPassword ? 'text' : 'password'}
              id="confirmPassword"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
          </>
        );
      case 2:
        return (
          <Box sx={{ textAlign: 'center', my: 2 }}>
            <Typography variant="h6" gutterBottom>
              Подтверждение регистрации
            </Typography>
            <Typography variant="body1" gutterBottom>
              Пожалуйста, проверьте ваши данные:
            </Typography>
            <Box sx={{ mt: 2, textAlign: 'left' }}>
              <Typography variant="body2">
                <strong>Имя:</strong> {firstName} {lastName}
              </Typography>
              <Typography variant="body2">
                <strong>Email:</strong> {email}
              </Typography>
            </Box>
          </Box>
        );
      default:
        return 'Неизвестный шаг';
    }
  };

  return (
    <Container component="main" maxWidth="sm">
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
            <PersonAddIcon />
          </Box>
          <Typography component="h1" variant="h5">
            Регистрация
          </Typography>
          
          <Stepper activeStep={activeStep} sx={{ width: '100%', my: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
          
          {error && (
            <Alert severity="error" sx={{ mt: 2, width: '100%' }}>
              {error}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1, width: '100%' }}>
            {getStepContent(activeStep)}
            
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
              <Button
                disabled={activeStep === 0}
                onClick={handleBack}
              >
                Назад
              </Button>
              
              <Button
                type="submit"
                variant="contained"
                disabled={loading}
              >
                {activeStep === steps.length - 1 
                  ? (loading ? 'Регистрация...' : 'Зарегистрироваться') 
                  : 'Далее'}
              </Button>
            </Box>
          </Box>
          
          <Grid container justifyContent="flex-end" sx={{ mt: 3 }}>
            <Grid item>
              <Link component={RouterLink} to="/login" variant="body2">
                Уже есть аккаунт? Войдите
              </Link>
            </Grid>
          </Grid>
        </Box>
      </Paper>
    </Container>
  );
};

export default RegisterPage; 