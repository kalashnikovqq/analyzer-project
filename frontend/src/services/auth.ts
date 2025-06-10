import { userApi } from './api';

interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  avatar?: string;
}

class AuthService {
  private readonly ACCESS_TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_KEY = 'user_data';
  

  saveTokens(tokens: AuthTokens): void {
    if (!tokens.access_token) {
      return;
    }
    
    localStorage.setItem(this.ACCESS_TOKEN_KEY, tokens.access_token);
    if (tokens.refresh_token) {
      localStorage.setItem(this.REFRESH_TOKEN_KEY, tokens.refresh_token);
    }
  }
  

  saveUser(user: User): void {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  }
  

  getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }
  

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }
  

  getUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    return userStr ? JSON.parse(userStr) : null;
  }
  
 
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }
  

  logout(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  }
  
 
  async login(email: string, password: string): Promise<User> {
    try {
      const response = await userApi.login(email, password);
      const { user, access_token, refresh_token } = response.data;
      
      this.saveTokens({ access_token, refresh_token });
      this.saveUser(user);
      
      return user;
    } catch (error) {
      throw error;
    }
  }
  

  async register(userData: any): Promise<User> {
    try {
      const response = await userApi.register(userData);
      const { user, access_token, refresh_token } = response.data;
      
      this.saveTokens({ access_token, refresh_token });
      this.saveUser(user);
      
      return user;
    } catch (error) {
      throw error;
    }
  }

  async forgotPassword(email: string): Promise<void> {
    try {
      await userApi.forgotPassword(email);
    } catch (error) {
      throw error;
    }
  }
  
  async resetPassword(token: string, password: string): Promise<void> {
    try {
      await userApi.resetPassword(token, password);
    } catch (error) {
      throw error;
    }
  }
  
  async getProfile(): Promise<User> {
    try {
      const token = this.getAccessToken();
      
      if (!token) {
        throw new Error('Токен авторизации отсутствует');
      }
      
      const response = await userApi.getProfile();
      const user = response.data;
      this.saveUser(user);
      
      return user;
    } catch (error: any) {
      throw error;
    }
  }

  async updateProfile(userData: Partial<User>): Promise<User> {
    try {
      const response = await userApi.updateProfile(userData);
      const updatedUser = response.data;
      
      const currentUser = this.getUser();
      const mergedUser = { ...currentUser, ...updatedUser };
      
      this.saveUser(mergedUser);
      
      return mergedUser;
    } catch (error) {
      throw error;
    }
  }
  
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    try {
      await userApi.changePassword({ currentPassword, newPassword });
    } catch (error) {
      throw error;
    }
  }
  
  async updateAvatar(file: File): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('avatar', file);
      
      const response = await userApi.updateAvatar(formData);
      const avatarUrl = response.data.avatarUrl;
      
      const currentUser = this.getUser();
      if (currentUser) {
        currentUser.avatar = avatarUrl;
        this.saveUser(currentUser);
      }
      
      return avatarUrl;
    } catch (error) {
      throw error;
    }
  }
}

export default new AuthService(); 