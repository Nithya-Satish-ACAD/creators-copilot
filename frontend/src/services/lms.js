// LMS Service - Handles all LMS platform operations
import axiosInstance from '../utils/axiosConfig';
import { isAuthenticated } from './auth';

/**
 * Get LMS authentication cookies (session-based auth)
 */
function getLMSCookies() {
  const lmsCookies = localStorage.getItem('lms_cookies');
  if (!lmsCookies) {
    throw new Error('Not logged into LMS. Please login to LMS first.');
  }
  return lmsCookies;
}

/**
 * Login to LMS platform
 * @param {string} email - LMS user email
 * @param {string} password - LMS user password
 * @returns {Promise<Object>} Login response with token and user info
 */
export async function loginToLMS(email, password) {
  try {
    // Ensure user is authenticated before LMS operations
    if (!isAuthenticated()) {
      throw new Error('User not authenticated. Please log in first.');
    }
    const response = await axiosInstance.post(
      '/login-lms',
      { email, password }
    );

    // Store LMS credentials in localStorage
    const lmsCookies = response.data.cookies || "";
    const lmsToken = response.data.token || response.data.data?.token || "";
    const lmsUser = response.data.data?.user || response.data.user || {};
    
    localStorage.setItem("lms_cookies", lmsCookies);
    localStorage.setItem("lms_user", JSON.stringify(lmsUser));
    if (lmsToken) {
      localStorage.setItem("lms_token", lmsToken);  // Store token if provided
    }
    
    return {
      success: true,
      cookies: lmsCookies,
      token: lmsToken,
      user: lmsUser,
      message: response.data.message
    };
  } catch (error) {
    console.error('LMS login error:', error);
    throw error.response?.data || { detail: 'LMS login failed' };
  }
}

/**
 * Get courses from LMS platform
 * @returns {Promise<Array>} List of LMS courses
 */
export async function getLMSCourses() {
  try {
    // Ensure user is authenticated before LMS operations
    if (!isAuthenticated()) {
      throw new Error('User not authenticated. Please log in first.');
    }
    const lmsCookies = getLMSCookies();

    const response = await axiosInstance.post(
      '/courses-lms',
      { lms_cookies: lmsCookies }
    );

    return {
      success: true,
      courses: response.data.data || [],
      message: response.data.message
    };
  } catch (error) {
    console.error('Get LMS courses error:', error);
    
    // If cookies expired or invalid, clear LMS data
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem('lms_cookies');
      localStorage.removeItem('lms_token');
      localStorage.removeItem('lms_user');
    }
    
    throw error.response?.data || { detail: 'Failed to fetch LMS courses' };
  }
}

/**
 * Get modules for a specific LMS course
 * @param {string} lmsCourseId - LMS course ID
 * @returns {Promise<Object>} Response with list of modules
 */
export async function getLMSModules(lmsCourseId) {
  try {
    // Ensure user is authenticated before LMS operations
    if (!isAuthenticated()) {
      throw new Error('User not authenticated. Please log in first.');
    }
    const lmsCookies = getLMSCookies();

    // Log the request data for debugging
    console.log('getLMSModules - Request data:', {
      lms_cookies: lmsCookies ? `${lmsCookies.substring(0, 50)}...` : 'MISSING',
      lms_course_id: lmsCourseId || 'MISSING',
      lmsCourseIdType: typeof lmsCourseId
    });

    // Validate required data
    if (!lmsCookies) {
      throw new Error('LMS cookies not found. Please login to LMS first.');
    }
    if (!lmsCourseId) {
      throw new Error('Course ID is required');
    }

    const response = await axiosInstance.post(
      '/modules-lms',
      { 
        lms_cookies: String(lmsCookies),
        lms_course_id: String(lmsCourseId)
      }
    );

    return {
      success: true,
      modules: response.data.data || [],
      message: response.data.message
    };
  } catch (error) {
    console.error('Get LMS modules error:', error);
    console.error('Error response data:', error.response?.data);
    
    // If cookies expired or invalid, clear LMS data
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem('lms_cookies');
      localStorage.removeItem('lms_token');
      localStorage.removeItem('lms_user');
    }
    
    throw error.response?.data || { detail: 'Failed to fetch LMS modules' };
  }
}

/**
 * Create a new module in LMS platform
 * @param {string} lmsCourseId - LMS course ID
 * @param {string} moduleTitle - Title of the module
 * @param {number} order - Order of the module (defaults to 1)
 * @returns {Promise<Object>} Response with created module data
 */
export async function createLMSModule(lmsCourseId, moduleTitle, order = 1) {
  try {
    // Ensure user is authenticated before LMS operations
    if (!isAuthenticated()) {
      throw new Error('User not authenticated. Please log in first.');
    }
    const lmsCookies = getLMSCookies();

    // Log the request data for debugging
    console.log('createLMSModule - Request data:', {
      lms_cookies: lmsCookies ? `${lmsCookies.substring(0, 50)}...` : 'MISSING',
      lms_course_id: lmsCourseId || 'MISSING',
      module_title: moduleTitle || 'MISSING',
      order: order,
      lmsCourseIdType: typeof lmsCourseId,
      moduleTitleType: typeof moduleTitle
    });

    // Validate required data
    if (!lmsCookies) {
      throw new Error('LMS cookies not found. Please login to LMS first.');
    }
    if (!lmsCourseId) {
      throw new Error('Course ID is required');
    }
    if (!moduleTitle || !moduleTitle.trim()) {
      throw new Error('Module title is required');
    }

    const response = await axiosInstance.post(
      '/create-module-lms',
      { 
        lms_cookies: String(lmsCookies),
        lms_course_id: String(lmsCourseId),
        module_title: String(moduleTitle),
        order: Number(order) || 1
      }
    );

    return {
      success: true,
      module: response.data.data || {},
      message: response.data.message
    };
  } catch (error) {
    console.error('Create LMS module error:', error);
    console.error('Error response data:', error.response?.data);
    
    // If cookies expired or invalid, clear LMS data
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem('lms_cookies');
      localStorage.removeItem('lms_token');
      localStorage.removeItem('lms_user');
    }
    
    throw error.response?.data || { detail: 'Failed to create LMS module' };
  }
}

/**
 * Check if user is logged into LMS
 * @returns {boolean}
 */
export function isLoggedIntoLMS() {
  const lmsCookies = localStorage.getItem('lms_cookies');
  return !!lmsCookies;
}

/**
 * Logout from LMS
 */
export function logoutFromLMS() {
  localStorage.removeItem('lms_cookies');
  localStorage.removeItem('lms_token');
  localStorage.removeItem('lms_user');
  localStorage.removeItem('lms_courses');
}

/**
 * Get LMS user info
 * @returns {Object|null}
 */
export function getLMSUser() {
  const lmsUserStr = localStorage.getItem('lms_user');
  return lmsUserStr ? JSON.parse(lmsUserStr) : null;
}

/**
 * Get stored LMS courses from localStorage
 * @returns {Array} List of courses (empty array if none stored)
 */
export function getStoredLMSCourses() {
  const coursesStr = localStorage.getItem('lms_courses');
  return coursesStr ? JSON.parse(coursesStr) : [];
}

/**
 * Clear stored LMS courses
 */
export function clearStoredLMSCourses() {
  localStorage.removeItem('lms_courses');
}

// Export default object with all functions
const lmsService = {
  loginToLMS,
  getLMSCourses,
  getLMSModules,
  createLMSModule,
  isLoggedIntoLMS,
  logoutFromLMS,
  getLMSUser,
  getStoredLMSCourses,
  clearStoredLMSCourses
};

export default lmsService;

