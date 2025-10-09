// Type definitions for FITREP Application

export interface Officer {
  id: number;
  last_name: string;
  first_name: string;
  middle_initial?: string;
  service_number: string;
  current_rank: string;
  total_reports: number;
}

export interface FitReport {
  id: number;
  officer_id: number;
  fitrep_id: string;
  rank_at_time: string;
  period_from: string;
  period_to: string;
  fra_score?: number;
  relative_value?: number;
  organization?: string;
  reporting_senior_name?: string;
  occasion_type?: string;
}

export interface TraitScores {
  [traitName: string]: string; // A-G or H for non-observed
}

export interface ProfileData {
  officer_info: {
    name: string;
    rank: string;
    total_reports: number;
  };
  rank_breakdown: {
    [rank: string]: RankProfileData;
  };
  marines: Marine[];
}

export interface Marine {
  last_name: string;
  first_name: string;
  fitreports: FitReportDetail[];
}

export interface FitReportDetail {
  fitrep_id: string;
  rank_at_time: string;
  period_from: string;
  period_to: string;
  fra_score?: number;
  relative_value?: number;
  organization?: string;
  reporting_senior_name?: string;
  trait_scores?: TraitScore[];
  occasion_type?: string;
}

export interface TraitScore {
  trait_name: string;
  score_letter: string;
}

export interface RankProfileData {
  total_reports: number;
  average_fra: number;
  highest_fra: number;
  lowest_fra: number;
  average_rv?: number;
  reports: ReportSummary[];
}

export interface ReportSummary {
  fitrep_id: string;
  period: string;
  fra_score: number;
  relative_value?: number;
  reporting_senior: string;
  organization?: string;
  trait_scores?: TraitScores;
  occasion_type?: string;
}

export interface ProfileSummary {
  officer_name: string;
  current_rank: string;
  total_reports: number;
  latest_fra: number;
  latest_rv: number;
}

export interface ProcessingResult {
  filename: string;
  status: 'success' | 'error' | 'failed' | 'skipped';
  fitrep_id?: string;
  fra_score?: number;
  error?: string;
}

export interface BatchProcessingResult {
  total_files: number;
  successful: number;
  failed: number;
  results: ProcessingResult[];
}