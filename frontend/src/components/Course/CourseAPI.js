import axios from "axios";

const API_BASE = "http://localhost:8000";

export const generateCourse = async (payload) => {
  const res = await axios.post(`${API_BASE}/generate_course`, payload);
  return res.data.result;
};

export const reviseCourse = async (payload) => {
  const res = await axios.post(`${API_BASE}/revise_course`, payload);
  return res.data.result;
};

export const chatReviseCourse = async (courseData, instruction) => {
  const res = await axios.post("http://localhost:8000/chat_revise", {
    instruction,
    course_data: courseData,
  });
  return res.data.result;
};