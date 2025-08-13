import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export async function login(email, password) {
  try {
    const response = await axios.post(`${API_BASE}/api/login`, { email, password });
    
    // Create user object from backend response
    const userData = {
      id: response.data.user_id,
      email: email,
      token: response.data.token,
      message: response.data.message
    };
    
    localStorage.setItem('user', JSON.stringify(userData));
    localStorage.setItem('token', response.data.token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    return userData;
  } catch (error) {
    throw error.response?.data || { detail: 'Login failed' };
  }
}

export async function googleLogin() {
  try {
    const response = await axios.get(`${API_BASE}/api/google-login`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { detail: 'Google login failed' };
  }
}

export async function register(email, password, name) {
  try {
    const response = await axios.post(`${API_BASE}/api/signup`, { email, password, name });
    return response.data;
  } catch (error) {
    throw error.response?.data || { detail: 'Registration failed' };
  }
}

export function logout() {
  localStorage.removeItem('user');
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
}

export function getCurrentUser() {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
}

export function getAuthToken() {
  const user = getCurrentUser();
  return user ? user.token : null;
}

export function isAuthenticated() {
  return !!getAuthToken();
}

export function getUserId() {
  const user = getCurrentUser();
  return user ? user.id : null;
}

export function getUserEmail() {
  const user = getCurrentUser();
  return user ? user.email : null;
}

export function getUserDisplayName() {
  const user = getCurrentUser();
  return user ? user.displayName : null;
}

// Function to refresh token
async function refreshAuthToken() {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  try {
    const response = await axios.post(`${API_BASE}/api/refresh-token`, {
      refresh_token: refreshToken
    });
    
    // Update stored tokens
    localStorage.setItem('token', response.data.token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    
    // Update user object
    const user = getCurrentUser();
    if (user) {
      user.token = response.data.token;
      localStorage.setItem('user', JSON.stringify(user));
    }
    
    return response.data.token;
  } catch (error) {
    // If refresh fails, logout user
    logout();
    throw error;
  }
}

// Axios interceptor to handle token refresh on 401 responses
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const newToken = await refreshAuthToken();
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return axios(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }
    
    return Promise.reject(error);
  }
);
