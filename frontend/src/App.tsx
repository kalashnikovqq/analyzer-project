import React, { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { useDispatch } from 'react-redux';
import { getProfile } from './store/slices/authSlice';

import MainLayout from './components/Layout';
import ProtectedRoute from './components/Layout/ProtectedRoute';
import LoadingIndicator from './components/LoadingIndicator';

const HomePage = lazy(() => import('./pages/HomePage'));
const LoginPage = lazy(() => import('./pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'));
const ForgotPasswordPage = lazy(() => import('./pages/auth/ForgotPasswordPage'));
const NewAnalysisPage = lazy(() => import('./pages/analysis/NewAnalysisPage'));
const AnalysisResultPage = lazy(() => import('./pages/analysis/AnalysisResultPage'));
const AnalysisHistoryPage = lazy(() => import('./pages/analysis/AnalysisHistoryPage'));
const ProfilePage = lazy(() => import('./pages/ProfilePage'));

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
  },
});

function App() {
  const dispatch = useDispatch();

  useEffect(() => {
    const accessToken = localStorage.getItem('access_token');
    if (accessToken) {
      dispatch(getProfile() as any);
    }
    
    const handleSessionExpired = (e: CustomEvent) => {
      window.location.href = '/login';
    };
    
    window.addEventListener('sessionExpired', handleSessionExpired as EventListener);
    
    return () => {
      window.removeEventListener('sessionExpired', handleSessionExpired as EventListener);
    };
  }, [dispatch]);

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Router>
        <Suspense fallback={<LoadingIndicator />}>
          <Routes>
            {/* Публичные маршруты */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            
            {/* Общедоступные маршруты в основном лейауте */}
            <Route path="/" element={<MainLayout><HomePage /></MainLayout>} />
            
            {/* Защищенные маршруты (требуют аутентификации) */}
            <Route path="/analysis/new" element={
              <MainLayout>
                <ProtectedRoute>
                  <NewAnalysisPage />
                </ProtectedRoute>
              </MainLayout>
            } />
            <Route path="/analysis/result/:id" element={
              <MainLayout>
                <ProtectedRoute>
                  <AnalysisResultPage />
                </ProtectedRoute>
              </MainLayout>
            } />
            <Route path="/analysis/history" element={
              <MainLayout>
                <ProtectedRoute>
                  <AnalysisHistoryPage />
                </ProtectedRoute>
              </MainLayout>
            } />
            <Route path="/profile" element={
              <MainLayout>
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              </MainLayout>
            } />
            
            {/* Маршрут по умолчанию (страница 404) */}
            <Route
              path="*"
              element={
                <MainLayout>
                  <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                    <h1>404</h1>
                    <p>Страница не найдена</p>
                  </div>
                </MainLayout>
              }
            />
          </Routes>
        </Suspense>
      </Router>
    </ThemeProvider>
  );
}

export default App; 