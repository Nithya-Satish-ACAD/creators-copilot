import axiosInstance from '../utils/axiosConfig';


export async function fetchCourses() {
  const res = await axiosInstance.get('/courses');
  return res.data;
}

export async function createCourse({name, description}) {
  const res = await axiosInstance.post('/courses', {name, description});
  return res.data;
}

export async function deleteCourse(courseId) {
  const res = await axiosInstance.delete(`/courses/${courseId}`);
  return res.data;
}

export async function getCourse(courseId) {
  const res = await axiosInstance.get(`/courses/${courseId}`);
  return res.data;
}

export async function saveCourseSettings(courseId, settings) {
  const res = await axiosInstance.put(`/courses/${courseId}/settings`, settings);
  return res.data;
}

export async function getCourseSettings(courseId) {
  const res = await axiosInstance.get(`/courses/${courseId}/settings`);
  return res.data;
}

export async function generateCourseDescription(description, courseName) {
  const res = await axiosInstance.put('/courses/description', {
    description,
    course_name: courseName
  });
  return res.data;
} 