import { axiosInstance } from './api';

export interface FleetSummary {
  total_ships: number;
  total_fuel_consumed_mt: number;
  total_co2_emissions_tonnes: number;
  total_transport_work_tonne_miles: number;
  fleet_average_eefi: number | null;
  fuel_breakdown: Record<string, { fuel_mt: number; co2: number; voyage_count: number }>;
}

export interface Report {
  id: string;
  org_id: string;
  year: number;
  status: string;
  generated_at: string;
  report_type: string;
  pdf_url: string;
  fleet_summary: FleetSummary;
}

export interface ReportListResponse {
  reports: Report[];
  total: number;
}

export interface ReportGenerateRequest {
  year: number;
}

export interface ReportStatusUpdate {
  status: string;
}

export const generateReport = async (data: ReportGenerateRequest): Promise<{ report: Report; message: string }> => {
  const { data: response } = await axiosInstance.post('/reports/generate', data);
  return response;
};

export const getReports = async (): Promise<ReportListResponse> => {
  const { data } = await axiosInstance.get<ReportListResponse>('/reports');
  return data;
};

export const getReportById = async (id: string): Promise<{ report: Report }> => {
  const { data } = await axiosInstance.get<{ report: Report }>(`/reports/${id}`);
  return data;
};

export const downloadReport = async (id: string): Promise<void> => {
  const response = await axiosInstance.get(`/reports/${id}/download`, {
    responseType: 'blob',
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `IMO_DCS_Report_${id}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
};

export const updateReportStatus = async (id: string, statusData: ReportStatusUpdate): Promise<{ report_id: string; status: string; message: string }> => {
  const { data } = await axiosInstance.patch(`/reports/${id}/status`, statusData);
  return data;
};
