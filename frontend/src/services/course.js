import axios from 'axios';
import { getCurrentUser } from './auth';

const baseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const API_BASE = new URL('/api', baseUrl).toString();

function getToken() {
  const user = getCurrentUser();
  if (!user || !user.token) {
    throw new Error('User not authenticated. Please log in.');
  }
  return user.token;
}

export async function fetchCourses() {
  const res = await axios.get(`${API_BASE}/courses`, {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  return res.data;
}

export async function createCourse({name, description}) {
  const res = await axios.post(`${API_BASE}/courses`, {name, description}, {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}`
    }
  });
  return res.data;
}

export async function deleteCourse(courseId) {
  const res = await axios.delete(`${API_BASE}/courses/${courseId}`, {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  return res.data;
}

export async function getCourse(courseId) {
  const res = await axios.get(`${API_BASE}/courses/${courseId}`, {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  return res.data;
}

export async function saveCourseSettings(courseId, settings) {
  
  const res = await axios.put(`${API_BASE}/courses/${courseId}/settings`, settings, {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  return res.data;
}

export async function getCourseSettings(courseId) {
  const res = await axios.get(`${API_BASE}/courses/${courseId}/settings`, {
    headers: { 'Authorization': `Bearer ${getToken()}` }
  });
  return res.data;
} 