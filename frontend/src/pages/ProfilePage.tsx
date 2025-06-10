import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { 
  Container, 
  Paper, 
  Typography, 
  TextField, 
  Button, 
  Box, 
  Grid,
  Avatar,
  Divider,
  CircularProgress,
  IconButton,
  Alert,
  Snackbar
} from '@mui/material';
import PhotoCamera from '@mui/icons-material/PhotoCamera';
import { 
  updateProfile, 
  changePassword,
  updateAvatar,
  User
} from '../store/slices/authSlice';
import { RootState } from '../store';

const ProfilePage: React.FC = () => {
  const dispatch = useDispatch();
  const { user, loading, error } = useSelector((state: RootState) => state.auth);
  
  const [profile, setProfile] = useState<Partial<User>>({
    email: '',
    firstName: '',
    lastName: ''
  });
  
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmNewPassword: ''
  });
  
  const [successMessage, setSuccessMessage] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  
  const [validationErrors, setValidationErrors] = useState({
    email: '',
    firstName: '',
    lastName: '',
    currentPassword: '',
    newPassword: '',
    confirmNewPassword: ''
  });

  useEffect(() => {
    if (user && !profile.email) {
      setProfile({
        email: user.email || '',
        firstName: user.firstName || '',
        lastName: user.lastName || ''
      });
    }
  }, [user, profile.email]);

  const showSuccessNotification = (message: string) => {
    setSuccessMessage(message);
    setShowSuccess(true);
  };

  const clearValidationErrors = () => {
    setValidationErrors({
      email: '',
      firstName: '',
      lastName: '',
      currentPassword: '',
      newPassword: '',
      confirmNewPassword: ''
    });
  };

  const validateProfile = () => {
    const errors: any = {};
    
    if (!profile.email) {
      errors.email = 'Email обязателен';
    } else if (!/\S+@\S+\.\S+/.test(profile.email)) {
      errors.email = 'Некорректный email';
    }
    
    if (!profile.firstName) {
      errors.firstName = 'Имя обязательно';
    }
    
    if (!profile.lastName) {
      errors.lastName = 'Фамилия обязательна';
    }
    
    setValidationErrors(prev => ({ ...prev, ...errors }));
    return Object.keys(errors).length === 0;
  };

  const validatePassword = () => {
    const errors: any = {};
    
    if (!passwordData.currentPassword) {
      errors.currentPassword = 'Текущий пароль обязателен';
    }
    
    if (!passwordData.newPassword) {
      errors.newPassword = 'Новый пароль обязателен';
    } else if (passwordData.newPassword.length < 6) {
      errors.newPassword = 'Пароль должен содержать минимум 6 символов';
    }
    
    if (passwordData.newPassword !== passwordData.confirmNewPassword) {
      errors.confirmNewPassword = 'Пароли не совпадают';
    }
    
    setValidationErrors(prev => ({ ...prev, ...errors }));
    return Object.keys(errors).length === 0;
  };

  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfile(prev => ({ ...prev, [name]: value }));
    clearValidationErrors();
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
    clearValidationErrors();
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateProfile()) {
      return;
    }
    
    try {
      await dispatch(updateProfile(profile) as any);
      showSuccessNotification('Профиль успешно обновлен');
    } catch (error) {
      console.error('Ошибка при обновлении профиля:', error);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validatePassword()) {
      return;
    }
    
    try {
      await dispatch(changePassword({
        currentPassword: passwordData.currentPassword,
        newPassword: passwordData.newPassword
      }) as any);
      
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmNewPassword: ''
      });
      
      showSuccessNotification('Пароль успешно изменен');
    } catch (error) {
      console.error('Ошибка при смене пароля:', error);
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    try {
      await dispatch(updateAvatar(file) as any);
      showSuccessNotification('Аватар успешно обновлен');
    } catch (error) {
      console.error('Ошибка при загрузке аватара:', error);
    }
  };

  if (!user) {
    return (
      <Container maxWidth="md">
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="md">
      <Typography variant="h4" component="h1" gutterBottom>
        Профиль пользователя
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Аватар
            </Typography>
            
            <Box sx={{ position: 'relative', display: 'inline-block', mb: 2 }}>
              <Avatar
                src={user.avatar}
                sx={{ width: 120, height: 120, mx: 'auto' }}
              />
              <IconButton
                color="primary"
                aria-label="загрузить аватар"
                component="label"
                sx={{ 
                  position: 'absolute', 
                  bottom: 0, 
                  right: 0,
                  backgroundColor: 'background.paper',
                  '&:hover': { backgroundColor: 'background.paper' }
                }}
              >
                <input
                  hidden
                  accept="image/*"
                  type="file"
                  onChange={handleAvatarUpload}
                />
                <PhotoCamera />
              </IconButton>
            </Box>
            
            <Typography variant="body2" color="text.secondary">
              Нажмите на камеру, чтобы изменить аватар
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Основная информация
            </Typography>
            
            <Box component="form" onSubmit={handleProfileSubmit}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email"
                    name="email"
                    type="email"
                    value={profile.email}
                    onChange={handleProfileChange}
                    error={!!validationErrors.email}
                    helperText={validationErrors.email}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Имя"
                    name="firstName"
                    value={profile.firstName}
                    onChange={handleProfileChange}
                    error={!!validationErrors.firstName}
                    helperText={validationErrors.firstName}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Фамилия"
                    name="lastName"
                    value={profile.lastName}
                    onChange={handleProfileChange}
                    error={!!validationErrors.lastName}
                    helperText={validationErrors.lastName}
                  />
                </Grid>
              </Grid>
              
              <Button
                type="submit"
                variant="contained"
                sx={{ mt: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Сохранить'}
              </Button>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Смена пароля
            </Typography>
            
            <Box component="form" onSubmit={handlePasswordSubmit}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Текущий пароль"
                    name="currentPassword"
                    type="password"
                    value={passwordData.currentPassword}
                    onChange={handlePasswordChange}
                    error={!!validationErrors.currentPassword}
                    helperText={validationErrors.currentPassword}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Новый пароль"
                    name="newPassword"
                    type="password"
                    value={passwordData.newPassword}
                    onChange={handlePasswordChange}
                    error={!!validationErrors.newPassword}
                    helperText={validationErrors.newPassword}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Подтвердите новый пароль"
                    name="confirmNewPassword"
                    type="password"
                    value={passwordData.confirmNewPassword}
                    onChange={handlePasswordChange}
                    error={!!validationErrors.confirmNewPassword}
                    helperText={validationErrors.confirmNewPassword}
                  />
                </Grid>
              </Grid>
              
              <Button
                type="submit"
                variant="contained"
                color="secondary"
                sx={{ mt: 2 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Изменить пароль'}
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      <Snackbar 
        open={showSuccess} 
        autoHideDuration={6000} 
        onClose={() => setShowSuccess(false)}
      >
        <Alert 
          onClose={() => setShowSuccess(false)} 
          severity="success" 
          sx={{ width: '100%' }}
        >
          {successMessage}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default ProfilePage; 