import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import analysisReducer from './slices/analysisSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    analysis: analysisReducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 