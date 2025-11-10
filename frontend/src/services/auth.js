import { API_BASE } from '../utils/axiosConfig';
import axios from 'axios';

export async function login(email, password) {
  try {
    // Use raw axios for login (not the instance with interceptor to avoid infinite loop)
    const response = await axios.post(`${API_BASE}/login`, { email, password });
    
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
    // Use raw axios for google login (not the instance with interceptor)
    const response = await axios.get(`${API_BASE}/google-login`);
    return response.data;
  } catch (error) {
    throw error.response?.data || { detail: 'Google login failed' };
  }
}

export async function register(email, password, name) {
  try {
    // Use raw axios for registration (not the instance with interceptor)
    const response = await axios.post(`${API_BASE}/signup`, { email, password, name });
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
