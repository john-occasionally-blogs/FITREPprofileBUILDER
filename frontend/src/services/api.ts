import axios from 'axios';
import { Officer, ProfileData, ProfileSummary, BatchProcessingResult } from '../types';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000, // 30 second timeout for file processing
});

export const officerApi = {
  getOfficers: async (): Promise<Officer[]> => {
    const response = await apiClient.get('/officers');
    return response.data;
  },

  getOfficer: async (officerId: number): Promise<Officer> => {
    const response = await apiClient.get(`/officers/${officerId}`);
    return response.data;
  },

  createOfficer: async (officerData: Omit<Officer, 'id' | 'total_reports'>): Promise<Officer> => {
    const response = await apiClient.post('/officers', officerData);
    return response.data;
  },
};

export const profileApi = {
  getProfile: async (officerId: number): Promise<ProfileData> => {
    const response = await apiClient.get(`/profiles/${officerId}`);
    return response.data;
  },

  getProfileSummary: async (officerId: number): Promise<ProfileSummary> => {
    const response = await apiClient.get(`/profiles/${officerId}/summary`);
    return response.data;
  },

  getReportingSeniors: async () => {
    const response = await apiClient.get('/profiles');
    return response.data;
  },
};

export const fitreportApi = {
  autoUpload: async (files: File[]): Promise<BatchProcessingResult & { officer_id: number; auto_extracted_info: any }> => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await apiClient.post('/fitreports/auto-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 600000, // 10 minutes for auto processing (supports large batches)
    });

    return response.data;
  },

  multiRsUpload: async (files: File[]): Promise<{
    message: string;
    rs_profiles: Array<{ id: number; name: string; rank: string; fitrep_count: number }>;
    total_files_processed: number;
    unique_rs_count: number;
    processing_details?: Array<{ filename: string; status: string; message: string }>;
  }> => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });

    const response = await apiClient.post('/fitreports/multi-rs-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 600000, // 10 minutes for multi-RS processing (supports large batches)
    });

    return response.data;
  },

  processFiles: async (files: File[], officerId: number): Promise<BatchProcessingResult> => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    formData.append('officer_id', officerId.toString());

    const response = await apiClient.post('/fitreports/process-files', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 600000, // 10 minutes for file processing (supports large batches)
    });

    return response.data;
  },

  getAllReports: async () => {
    const response = await apiClient.get(`/fitreports/all`);
    return response.data;
  },

  getOfficerReports: async (officerId: number) => {
    const response = await apiClient.get(`/fitreports/officer/${officerId}`);
    return response.data;
  },

  deleteReport: async (fitrepId: number) => {
    const response = await apiClient.delete(`/fitreports/${fitrepId}`);
    return response.data;
  },

  deleteAllReports: async () => {
    const response = await apiClient.delete(`/fitreports/all`);
    return response.data;
  },

  deleteAllOfficerReports: async (officerId: number) => {
    const response = await apiClient.delete(`/fitreports/officer/${officerId}/all`);
    return response.data;
  },
};

export const scoringApi = {
  predictImpact: async (data: {
    officer_id: number;
    rank: string;
    reporting_senior: string;
    proposed_reports: Array<{[trait: string]: string}>;
  }) => {
    const response = await apiClient.post('/scoring/predict-impact', data);
    return response.data;
  },

  validateTraitScores: async (traitScores: {[trait: string]: string}) => {
    const response = await apiClient.post('/scoring/validate-trait-scores', {
      trait_scores: traitScores
    });
    return response.data;
  },
};