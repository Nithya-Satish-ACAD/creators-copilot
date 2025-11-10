import axiosInstance from '../utils/axiosConfig';



export async function getAllResources(courseId = null) {
  // If courseId is not provided, try to get it from localStorage
  if (!courseId) {
    courseId = localStorage.getItem('currentCourseId');
    if (!courseId) {
      throw new Error('No course ID provided and none found in localStorage');
    }
  }
  
  const res = await axiosInstance.get(`/courses/${courseId}/resources`);
  return res.data;
}

// upload resources
export async function uploadResources(courseId, files) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  const res = await axiosInstance.post(`/courses/${courseId}/resources`, formData, {
    headers: {
      'Content-Type': undefined  // Let browser set multipart/form-data with boundary
    }
  });
  return res.data;
}


function handleAxiosError(error) {
  if (error.response && error.response.data && error.response.data.detail) {
    const detail = error.response.data.detail;
    // If detail is an array (FastAPI validation errors), format it
    if (Array.isArray(detail)) {
      const messages = detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join(', ');
      throw new Error(messages);
    }
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  throw new Error(error.message || 'Unknown error');
}

export async function uploadCourseResources(courseId, files) {
  console.log('uploadCourseResources called with:', { courseId, filesCount: files?.length, files });
  
  if (!files || files.length === 0) {
    throw new Error('No files provided for upload');
  }
  
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  
  try {
    const res = await axiosInstance.post(`/courses/${courseId}/resources`, formData, {
      headers: {
        'Content-Type': undefined  // Let browser set multipart/form-data with boundary
      }
    });
    return res.data;
  } catch (error) {
    console.error('Upload error:', error);
    console.error('Error response:', error.response?.data);
    handleAxiosError(error);
  }
}

export async function deleteResource(courseId, resourceName) {
  const res = await axiosInstance.delete(`/courses/${courseId}/resources/${encodeURIComponent(resourceName)}`);
  return res.data;
}

export async function viewResource(courseId, resourceName) {
  console.log('viewResource called with:', { courseId, resourceName });
  const url = `/courses/${courseId}/resources/${encodeURIComponent(resourceName)}/content`;
  console.log('Making request to:', url);
  const res = await axiosInstance.get(url);
  console.log('Response received:', res.data);
  return res.data;
}

/*
// Returns the view URL for a resource (for use as an href)
export function getResourceViewUrl(courseId, resourceName) {
  return `${API_BASE}/courses/${courseId}/resources/${encodeURIComponent(resourceName)}/view`;
}
*/
/*
// Fetches and opens the resource file in a new tab for viewing
export async function viewResourceFile(courseId, resourceName) {
  const url = getResourceViewUrl(courseId, resourceName);
  const token = getToken();
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Failed to fetch file');
  const blob = await response.blob();
  const fileURL = window.URL.createObjectURL(blob);
  window.open(fileURL, '_blank');
}
*/
// Fetches and triggers download of the resource file
/*
export async function downloadResourceFile(courseId, resourceName) {
  const url = getResourceViewUrl(courseId, resourceName);
  const token = getToken();
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  if (!response.ok) throw new Error('Failed to fetch file');
  const blob = await response.blob();
  const fileURL = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = fileURL;
  a.download = resourceName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(fileURL);
}
*/