// src/types/index.ts

export interface Employee {
  id: number;
  name: string;
  email: string;
}

export interface EmployeeSummary {
  total_employees: number;
  submitted_today: number;
  not_submitted_today: number;
}

export interface ChartData {
  chartType: 'bar' | 'line' | 'pie' | 'doughnut' | 'radar' | 'scatter' | 'bubble' | 'polarArea' | 'none';
  chartTitle: string;
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[] | Array<{ x: number; y: number; r?: number }>;
    backgroundColor: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
  }>;
  options?: {
    xAxisLabel?: string;
    yAxisLabel?: string;
    [key: string]: any;
  };
}

export interface Message {
  comprehensiveCharts: any;
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  chartData?: ChartData;
  invoice_metadata?: {
    year: number;
    month: number;
  };
}

export interface ChatResponse {
  response: string;
  type: 'individual' | 'team' | 'comparison' | 'general' | 'error';
  metrics?: any;
  chartData?: ChartData;
  error?: string;
}

export interface StaticChartData {
  status_distribution: Array<{ status: string; count: number }>;
  top_submitters: Array<{ name: string; rate: number }>;
  top_hours: Array<{ name: string; hours: number }>;
  team_metrics: {
    avg_submission_rate: number;
    avg_daily_hours: number;
    total_employees: number;
    high_performers: number;
  };
}



// Add to src/types.ts or src/types/index.ts

export interface FilterOptions {
  projects: string[];
  statuses: string[];
  dateRange: {
    start: string | null;
    end: string | null;
  };
  searchQuery: string;
}

export interface MonthlyInvoice {
  invoice_number: string;
  year: number;
  month: number;
  month_name: string;
  period_start: string;
  period_end: string;
  total_hours: number;
  total_billable_hours: number;
  total_extra_hours: number;
  employee_breakdown: EmployeeInvoiceItem[];
  category_breakdown: CategoryInvoiceItem[];
  generated_at: string;
  has_sow_violations: boolean;
  period_description: string;
}

export interface EmployeeInvoiceItem {
  employee_name: string;
  employee_email: string;
  total_hours: number;
  billable_hours: number;
  extra_hours: number;
  days_worked: number;
  categories: {
    actual_hours: Record<string, number>;
    billable_hours: Record<string, number>;
    extra_hours: Record<string, number>;
  };
  billing_efficiency: number;
  sow_compliance: string;
}

export interface CategoryInvoiceItem {
  category: string;
  category_label: string;
  total_hours: number;
  billable_hours: number;
  extra_hours: number;
  has_cap: boolean;
  cap_value: string;
}

export interface InvoicePeriod {
  year: number;
  month: number;
  month_name: string;
  period: string;
  has_data: boolean;
}