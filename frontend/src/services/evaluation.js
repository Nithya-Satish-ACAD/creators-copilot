import axiosInstance from '../utils/axiosConfig';
import { getCurrentUser } from './auth';

// Track ongoing evaluation requests to prevent duplicates
const ongoingEvaluations = new Set();
// Track last evaluation request timestamps to prevent rapid duplicates
const lastEvaluationTime = new Map();
// Track completed evaluations to prevent re-evaluation
const completedEvaluations = new Set();


export const evaluationService = {
  // Clear completed evaluations tracking (useful when starting fresh)
  clearCompletedEvaluations() {
    completedEvaluations.clear();
    ongoingEvaluations.clear();
  },

  async uploadMarkScheme({ courseId, markSchemeFile }) {
    const formData = new FormData();
    formData.append('course_id', courseId);
    formData.append('mark_scheme', markSchemeFile);
    
    try {
      const res = await axiosInstance.post('/evaluation/upload-mark-scheme', formData, {
        headers: { 
          'Content-Type': 'multipart/form-data'
        }
      });
      return res.data; // { evaluation_id: "uuid", mark_scheme_file_id: "uuid" }
    } catch (error) {
      console.error('Upload mark scheme error:', error);
      if (error.response?.status === 401) {
        throw new Error('Authentication failed. Please try again.');
      }
      throw new Error(error.response?.data?.detail || 'Failed to upload mark scheme');
    }
  },

  async uploadAnswerSheets({ evaluationId, answerSheetFiles }) {
    const formData = new FormData();
    formData.append('evaluation_id', evaluationId);
    if (Array.isArray(answerSheetFiles)) {
      answerSheetFiles.forEach(f => formData.append('answer_sheets', f));
    } else if (answerSheetFiles) {
      formData.append('answer_sheets', answerSheetFiles);
    }
    
    try {
      const res = await axiosInstance.post('/evaluation/upload-answer-sheets', formData, {
        headers: { 
          'Content-Type': 'multipart/form-data'
        }
      });
      return res.data; // { evaluation_id: "uuid", answer_sheet_file_ids: ["uuid1", "uuid2"] }
    } catch (error) {
      console.error('Upload answer sheets error:', error);
      if (error.response?.status === 401) {
        throw new Error('Authentication failed. Please try again.');
      }
      throw new Error(error.response?.data?.detail || 'Failed to upload answer sheets');
    }
  },

  async evaluateFiles(evaluationId, { signal } = {}) {
    const now = Date.now();
    const lastRequestTime = lastEvaluationTime.get(evaluationId) || 0;
    
    // Check if this evaluation is already completed
    if (completedEvaluations.has(evaluationId)) {
      throw new Error('This evaluation has already been completed. Please refresh the page.');
    }
    
    // Prevent duplicate requests for the same evaluation
    if (ongoingEvaluations.has(evaluationId)) {
      throw new Error('Evaluation already in progress for this ID');
    }
    
    // NUCLEAR PROTECTION: Prevent rapid successive requests (within 3 seconds)
    if (now - lastRequestTime < 3000) {
      throw new Error('Duplicate request blocked - please wait');
    }
    
    ongoingEvaluations.add(evaluationId);
    lastEvaluationTime.set(evaluationId, now);
    
    try {
      const user = getCurrentUser();
      if (!user?.id) {
        ongoingEvaluations.delete(evaluationId);
        throw new Error('User not authenticated');
      }


      // Trigger backend evaluation (runs in background)
      const res = await axiosInstance.get('/evaluation/evaluate-files', {
        params: {
          evaluation_id: evaluationId,
          user_id: user.id
        },
        timeout: 30000,
        signal
      });
      
      ongoingEvaluations.delete(evaluationId); // Clean up tracking
      return res.data; // { evaluation_id: "uuid", message: "Evaluation started in background" }
    } catch (error) {
      console.error('Evaluation error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        evaluationId: evaluationId,
        code: error.code
      });
      
      if (error.response?.status === 401) {
        throw new Error('Authentication failed. Please try again.');
      }
      
      // On timeout, the evaluation is still running in background
      if (error.response?.status === 504 || error.code === 'ECONNABORTED') {
        ongoingEvaluations.delete(evaluationId);
        throw new Error('Evaluation started successfully. You will receive an email when it completes.');
      }
      
      if (error.response?.status >= 500) {
        const errorDetail = error.response?.data?.detail || 'Server error during evaluation';
        throw new Error(`Server error: ${errorDetail}. The backend may still be processing. Please try again in a few minutes.`);
      }
      
      if (error.response?.status === 404) {
        throw new Error('Evaluation session not found. Please restart the evaluation process.');
      }
      
      // Always clean up tracking in catch block
      ongoingEvaluations.delete(evaluationId);
      throw new Error(error.response?.data?.detail || `Evaluation failed: ${error.message}`);
        }
  },


  async checkEvaluationStatus(evaluationId, { signal } = {}) {
    try {
      const res = await axiosInstance.get(`/evaluation/status/${evaluationId}`, {
        timeout: 10000,
        signal
      });
      
      
      // Mark as completed if we get a completed status
      if (res.data.status === 'completed') {
        completedEvaluations.add(evaluationId);
      }
      
      return res.data; // { status: "completed" | "processing", evaluation_result?: {...} }
    } catch (error) {
      console.error('Status check error:', error);
      
      if (error.response?.status === 401) {
        throw new Error('Authentication failed. Please try again.');
      }
      
      if (error.response?.status === 404) {
        // 404 might mean the evaluation was not created properly or was deleted
        // Let's provide more context
        console.warn(`Evaluation ${evaluationId} not found (404). This might be a timing issue or the evaluation was not created properly.`);
        throw new Error('Evaluation not found. Please try restarting the evaluation process.');
      }
      
      if (error.response?.status >= 500) {
        throw new Error('Server error while checking evaluation status. Please try again.');
      }
      
      // For other errors, provide a generic message but don't fail completely
      console.warn('Status check failed, but continuing to retry:', error.message);
      throw new Error(error.response?.data?.detail || 'Failed to check evaluation status');
    }
  },

  async checkCompletedEvaluation(evaluationId, { signal } = {}) {
    try {
      const res = await axiosInstance.get(`/evaluation/status/${evaluationId}`, {
        timeout: 10000,
        signal
      });
      
      if (res.data.status === 'completed') {
        completedEvaluations.add(evaluationId);
        return { status: 'completed', evaluation_result: res.data.evaluation_result };
      }

      return { status: 'processing' };
    } catch (error) {
      console.error('Fallback evaluation check error:', error);
      throw error;
    }
  },

  async editQuestionResult({ evaluationId, fileId, questionNumber, score, feedback }) {
    try {
      const user = getCurrentUser();
      if (!user?.id) {
        throw new Error('User not authenticated');
      }
      
      const res = await axiosInstance.put('/evaluation/edit-results', {
        evaluation_id: evaluationId,
        file_id: fileId,
        question_number: questionNumber,
        score: score,
        feedback: feedback
      });
      
      return res.data; // { message: "Results updated" }
    } catch (error) {
      console.error('Edit question result error:', error);
      if (error.response?.status === 401) {
        throw new Error('Authentication failed. Please try again.');
      }
      throw new Error(error.response?.data?.detail || 'Failed to edit question result');
    }
  },

  async saveEvaluation(evaluationId, assetName, fileName) {
    try {
      const formData = new FormData();
      formData.append('asset_name', assetName);
      formData.append('file_name', fileName);
      const res = await axiosInstance.post(`/evaluation/save/${evaluationId}`, formData, {
        headers: { 
          'Content-Type': 'multipart/form-data'
        }
      });
      
      return res.data;
    } catch (error) {
      console.error('Save evaluation error:', error);
      if (error.response?.status === 401) {
        throw new Error('Authentication failed. Please try again.');
      }
      throw new Error(error.response?.data?.detail || 'Failed to save evaluation');
    }
  },

  async getCombinedReport(evaluationId, { signal } = {}) {
    try {
      const res = await axiosInstance.get(`/evaluation/report/${evaluationId}`, {
        timeout: 10000,
        signal
      });
      return res.data; // { report: "markdown string" }
    } catch (error) {
      console.error('Get combined report error:', error);
      if (error.response?.status === 401) {
        throw new Error('Authentication failed. Please try again.');
      }
      if (error.response?.status === 400) {
        throw new Error('Evaluation not yet completed');
      }
      throw new Error(error.response?.data?.detail || 'Failed to get combined report');
    }
  },

  async getStudentReport(evaluationId, studentIndex, { signal } = {}) {
    try {
      const res = await axiosInstance.get(`/evaluation/report/${evaluationId}/student/${studentIndex}`, {
        timeout: 10000,
        signal
      });
      return res.data; // { report: "markdown string", student_index: 0, total_students: 10 }
    } catch (error) {
      console.error('Get student report error:', error);
      if (error.response?.status === 401) {
        throw new Error('Authentication failed. Please try again.');
      }
      if (error.response?.status === 400) {
        throw new Error('Evaluation not yet completed');
      }
      if (error.response?.status === 404) {
        throw new Error('Student not found');
      }
      throw new Error(error.response?.data?.detail || 'Failed to get student report');
    }
  },

  async downloadReportCSV(evaluationId) {
    try {
      const res = await axiosInstance.get(`/evaluation/report/${evaluationId}/csv`, {
        responseType: 'blob',
        timeout: 30000
      });
      
      // Create a download link
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      
      // Extract filename from response headers or use default
      const contentDisposition = res.headers['content-disposition'];
      let filename = `evaluation_report_${evaluationId}.csv`;
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return { success: true, filename };
    } catch (error) {
      console.error('Download CSV report error:', error);
      if (error.response?.status === 401) {
        throw new Error('Authentication failed. Please try again.');
      }
      if (error.response?.status === 400) {
        throw new Error('Evaluation not yet completed');
      }
      throw new Error(error.response?.data?.detail || 'Failed to download CSV report');
    }
  }
}; 