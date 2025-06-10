import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store';
import { getProfile } from '../../store/slices/authSlice';
import { authApi } from '../../services/api';


const TokenRefresher = () => {
  const dispatch = useDispatch<AppDispatch>();

  useEffect(() => {
    const checkToken = async () => {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (!accessToken) {
        if (refreshToken) {
          try {
            await authApi.refreshToken();
            await dispatch(getProfile());
          } catch (error) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_data');
          }
        }
        return;
      }

      try {
        await dispatch(getProfile());
      } catch (error) {
        if (refreshToken) {
          try {
            await authApi.refreshToken();
            await dispatch(getProfile());
          } catch (refreshError) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user_data');
          }
        } else {
        localStorage.removeItem('access_token');
          localStorage.removeItem('user_data');
        }
      }
    };

    checkToken();
  }, [dispatch]);

  return null;
};

export default TokenRefresher; 