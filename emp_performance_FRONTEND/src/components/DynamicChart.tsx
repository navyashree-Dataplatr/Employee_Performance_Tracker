

// src/components/DynamicChart.tsx - UPDATED
import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Line, Pie, Doughnut, Radar, Scatter, Bubble, PolarArea } from 'react-chartjs-2';
// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend
);
export interface ChartData {
  chartType: 'bar' | 'horizontalBar' | 'line' | 'pie' | 'doughnut' | 'radar' | 'scatter' | 'bubble' | 'polarArea' | 'none';
  chartTitle: string;
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[] | Array<{ x: number; y: number; r?: number }>;
    backgroundColor: string | string[];
    borderColor?: string | string[];
    borderWidth?: number;
    fill?: boolean;
    tension?: number;
    pointRadius?: number;
    [key: string]: any;
  }>;
  options?: {
    xAxisLabel?: string;
    yAxisLabel?: string;
    [key: string]: any;
  };
}
interface DynamicChartProps {
  chartData: ChartData;
}
const DynamicChart: React.FC<DynamicChartProps> = ({ chartData }) => {
  const chartRef = React.useRef<any>(null);
  // If no chart needed, return null
  if (!chartData || chartData.chartType === 'none') {
    return null;
  }
  // SIMPLIFIED VALIDATION - accept charts even with zero values
  if (!chartData.labels || !chartData.datasets || chartData.datasets.length === 0) {
    console.warn('Invalid chart data structure:', chartData);
    return null;
  }
  // For scatter charts, check for data objects
  if (chartData.chartType === 'scatter') {
    const hasValidData = chartData.datasets.some(dataset =>
      dataset.data && Array.isArray(dataset.data) && dataset.data.length > 0
    );
    if (!hasValidData) {
      console.warn('Scatter chart has no valid data');
      return null;
    }
  }
  // Modern Color Palettes with Gradients
  const chartColors = [
    { start: 'rgba(59, 130, 246, 0.9)', end: 'rgba(37, 99, 235, 0.4)' },   // Blue
    { start: 'rgba(16, 185, 129, 0.9)', end: 'rgba(5, 150, 105, 0.4)' },   // Emerald
    { start: 'rgba(249, 115, 22, 0.9)', end: 'rgba(234, 88, 12, 0.4)' },   // Orange
    { start: 'rgba(139, 92, 246, 0.9)', end: 'rgba(124, 58, 237, 0.4)' },  // Violet
    { start: 'rgba(236, 72, 153, 0.9)', end: 'rgba(219, 39, 119, 0.4)' },  // Pink
    { start: 'rgba(6, 182, 212, 0.9)', end: 'rgba(8, 145, 178, 0.4)' },    // Cyan
    { start: 'rgba(245, 158, 11, 0.9)', end: 'rgba(217, 119, 6, 0.4)' },   // Amber
    { start: 'rgba(99, 102, 241, 0.9)', end: 'rgba(79, 70, 229, 0.4)' },   // Indigo
  ];
  // Helper to create gradients
  const createGradient = (ctx: CanvasRenderingContext2D, area: any, colorIndex: number) => {
    const color = chartColors[colorIndex % chartColors.length];
    const gradient = ctx.createLinearGradient(0, area.bottom, 0, area.top);
    gradient.addColorStop(0, color.end);
    gradient.addColorStop(1, color.start);
    return gradient;
  };
  // Prepare chart configuration
  const chartConfig = {
    labels: chartData.labels,
    datasets: chartData.datasets.map((dataset, index) => {
      // Handle scatter and bubble chart data differently
      if (chartData.chartType === 'scatter' || chartData.chartType === 'bubble') {
        return {
          ...dataset,
          data: dataset.data || [],
          borderWidth: 2,
          pointRadius: chartData.chartType === 'bubble' ? undefined : 6,
          pointHoverRadius: chartData.chartType === 'bubble' ? undefined : 8,
          pointBackgroundColor: chartColors[index % chartColors.length].start,
        };
      }
      // Ensure data is numeric
      const numericData = (dataset.data || []).map(val => {
        if (typeof val === 'number') return val;
        if (typeof val === 'string') {
          const cleaned = String(val).replace(/[^\d.-]/g, '');
          return Number(cleaned) || 0;
        }
        return 0;
      });
      // Gradient background logic
      const backgroundColor = (context: any) => {
        const { ctx, chartArea } = context.chart;
        if (!chartArea) return undefined;
        // Different gradient depending on chart type?
        // For Pie/Doughnut, we might want multiple colors in one dataset
        if (chartData.chartType === 'pie' || chartData.chartType === 'doughnut') {
          // For these, we map the index of data point to color
          const dataIndex = context.dataIndex;
          return chartColors[dataIndex % chartColors.length].start;
        }
        return createGradient(ctx, chartArea, index);
      };
      const borderColor = chartColors[index % chartColors.length].start;
      const isLineChart = chartData.chartType === 'line';
      const isRadar = chartData.chartType === 'radar';
      return {
        ...dataset,
        label: dataset.label,
        data: numericData,
        backgroundColor: (chartData.chartType === 'pie' || chartData.chartType === 'doughnut')
          ? chartColors.map(c => c.start) // Fallback/Static for pie
          : backgroundColor,              // Gradient for others
        borderColor: (chartData.chartType === 'pie' || chartData.chartType === 'doughnut')
          ? '#ffffff'
          : borderColor,
        borderWidth: isRadar ? 2 : (dataset.borderWidth || 0),
        borderRadius: 6, // Modern rounded corners for bars
        borderSkipped: false, // Rounded on all sides if floating, or just top
        // Line chart specifics
        tension: isLineChart ? 0.4 : 0, // Smooth curves
        fill: isLineChart ? true : false,
        pointBackgroundColor: '#ffffff',
        pointBorderColor: borderColor,
        pointBorderWidth: 2,
        pointRadius: isLineChart || isRadar ? 4 : 0,
        pointHoverRadius: 6,
        categoryPercentage: 0.7, // Thicker bars
        barPercentage: 0.9,
      };
    }),
  };
  // Modern Chart Options
  const commonOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    animation: {
      duration: 1000,
      easing: 'easeOutQuart',
    },
    plugins: {
      legend: {
        position: 'top',
        align: 'end',
        labels: {
          usePointStyle: true,
          pointStyle: 'rectRounded',
          font: {
            family: "'Inter', sans-serif",
            size: 11,
            weight: 500,
          },
          color: '#64748b', // Slate 500
          padding: 20,
          boxWidth: 10,
          boxHeight: 10,
        },
      },
      title: {
        display: true,
        text: chartData.chartTitle || 'Insight Chart',
        align: 'start',
        font: {
          family: "'Inter', sans-serif",
          size: 16,
          weight: 600,
        },
        color: '#1e293b', // Slate 800
        padding: { top: 10, bottom: 25 },
      },
      tooltip: {
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        titleColor: '#0f172a', // Slate 900
        bodyColor: '#475569', // Slate 600
        borderColor: '#e2e8f0', // Slate 200
        borderWidth: 1,
        padding: 12,
        boxPadding: 4,
        usePointStyle: true,
        titleFont: {
          family: "'Inter', sans-serif",
          size: 13,
          weight: 600,
        },
        bodyFont: {
          family: "'Inter', sans-serif",
          size: 12,
        },
        callbacks: {
          label: function (context: any) {
            let label = context.dataset.label || '';
            if (label) label += ': ';

            // For bubble charts, show x, y, and radius
            if (context.chart.config.type === 'bubble' && context.parsed) {
              const x = context.parsed.x !== undefined ? context.parsed.x.toLocaleString() : '';
              const y = context.parsed.y !== undefined ? context.parsed.y.toLocaleString() : '';
              const r = context.parsed._custom !== undefined ? context.parsed._custom.toLocaleString() : '';
              label += `(${x}, ${y}${r ? ', r: ' + r : ''})`;
            }
            // For horizontal bar charts, the value is on the x-axis
            // For other charts (bar, line, etc.), the value is on the y-axis
            else {
              const isHorizontalBar = context.chart.config.options?.indexAxis === 'y';

              if (isHorizontalBar && context.parsed.x !== undefined) {
                label += context.parsed.x.toLocaleString();
              } else if (context.parsed.y !== undefined) {
                label += context.parsed.y.toLocaleString();
              } else if (context.parsed !== undefined) {
                label += context.parsed.toLocaleString();
              }
            }
            return label;
          }
        },
        displayColors: true,
        cornerRadius: 8,
        elevation: 4, // If supported by plugin, otherwise nice shadow via CSS not possible here directly
      },
    },
    scales: {
      x: {
        grid: {
          display: false, // Clean look, no vertical grid lines usually
        },
        ticks: {
          font: {
            family: "'Inter', sans-serif",
            size: 11
          },
          color: '#64748b'
        },
        border: {
          display: false
        }
      },
      y: {
        border: {
          display: false, // No axis line
          dash: [4, 4]
        },
        grid: {
          color: '#f1f5f9', // Very light slate for horizontal grid
          drawBorder: false,
        },
        ticks: {
          font: {
            family: "'Inter', sans-serif",
            size: 11
          },
          color: '#64748b',
          padding: 10
        }
      }
    }
  };
  // Special options for specific chart types
  const getChartOptions = () => {
    // Deep clone basic options
    const options = JSON.parse(JSON.stringify(commonOptions));
    // Re-attach functions lost during JSON stringify/parse (tooltip callbacks)
    options.plugins.tooltip = commonOptions.plugins.tooltip;
    // Remove scales for pie/doughnut/radar
    if (['pie', 'doughnut', 'radar', 'polarArea'].includes(chartData.chartType)) {
      delete options.scales;
    }

    if (chartData.chartType === 'doughnut') {
      options.cutout = '65%';
      options.plugins.legend = {
        ...options.plugins.legend,
        position: 'right',
        align: 'center',
      };
    }
    if (chartData.chartType === 'horizontalBar') {
      options.indexAxis = 'y';
      options.scales = {
        x: { ...commonOptions.scales.y, grid: { ...commonOptions.scales.y.grid } },
        y: { ...commonOptions.scales.x, grid: { ...commonOptions.scales.x.grid } } // Swap styles
      };
    }
    if (chartData.chartType === 'radar') {
      options.scales = {
        r: {
          angleLines: { color: '#f1f5f9' },
          grid: { color: '#f1f5f9' },
          pointLabels: {
            font: { family: "'Inter', sans-serif", size: 11 },
            color: '#64748b'
          },
          ticks: { display: false } // Hide radial numbers usually for cleaner look
        }
      };
    }
    return options;
  };
  const renderChart = () => {
    const options = getChartOptions();
    try {
      // Data length safety checks (from previous version)
      if (chartConfig.datasets.length > 0 && chartData.chartType !== 'scatter') {
        chartConfig.datasets.forEach(dataset => {
          const dataLen = dataset.data.length;
          const labelsLen = chartConfig.labels.length;
          if (dataLen < labelsLen) {
            const padding = Array(labelsLen - dataLen).fill(0);
            dataset.data = [...dataset.data, ...padding];
          } else if (dataLen > labelsLen) {
            dataset.data = dataset.data.slice(0, labelsLen);
          }
        });
      }
      const ChartComponent = {
        'bar': Bar,
        'horizontalBar': Bar,
        'line': Line,
        'pie': Pie,
        'doughnut': Doughnut,
        'radar': Radar,
        'scatter': Scatter,
        'bubble': Bubble,
        'polarArea': PolarArea,
        'none': Bar // Fallback
      }[chartData.chartType] || Bar;
      return <ChartComponent ref={chartRef} data={chartConfig as any} options={options} />;
    } catch (error) {
      console.error('Error rendering chart:', error);
      return (
        <div className="flex items-center justify-center h-64 bg-slate-50 rounded-lg">
          <span className="text-slate-400">Unable to render chart</span>
        </div>
      );
    }
  };
  const getChartTypeDisplayName = () => {
    const names: Record<string, string> = {
      'horizontalBar': 'Horizontal Bar',
      'doughnut': 'Donut',
      'bar': 'Bar Analysis',
      'line': 'Trend Line',
      'radar': 'Radar Assessment',
      'pie': 'Distribution',
      'scatter': 'Scatter Plot',
      'bubble': 'Bubble Chart',
      'polarArea': 'Polar Area'
    };
    return names[chartData.chartType] || chartData.chartType;
  };
  return (
    <div className="bg-white/40 backdrop-blur-xl rounded-[2.5rem] p-8 lg:p-10 shadow-2xl shadow-indigo-500/5 border border-white transition-all hover:shadow-indigo-500/10 hover:-translate-y-1 duration-700 group relative overflow-hidden mt-6">
      {/* Container Background Glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 blur-[80px] rounded-full -mr-32 -mt-32"></div>

      <div className="flex items-center justify-between mb-8 relative z-10">
        <div>
          <h3 className="text-xl font-black text-slate-900 tracking-tight group-hover:text-indigo-950 transition-colors">
            {chartData.chartTitle || "Analytics Visualization"}
          </h3>
          <p className="text-[10px] text-slate-400 font-extrabold uppercase tracking-[0.2em] mt-1.5 opacity-80">
            {chartData.chartType.toUpperCase()} Engine Output
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="bg-indigo-50 text-indigo-600 text-[10px] uppercase tracking-wider font-extrabold px-3 py-1.5 rounded-xl border border-indigo-100 shadow-sm">
            {getChartTypeDisplayName()}
          </span>
        </div>
      </div>

      <div className="h-96 w-full relative z-10">
        {renderChart()}
      </div>

      <div className="mt-8 pt-6 border-t border-slate-100/50 flex items-center justify-between relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Live Dynamic Render</span>
        </div>
        <div className="px-4 py-2 bg-slate-50/50 rounded-xl border border-slate-100">
          <span className="text-[10px] font-black text-indigo-600 uppercase tracking-widest">
            {chartData.datasets[0]?.data.length || 0} Data Points
          </span>
        </div>
      </div>
    </div>
  );
};
export default DynamicChart;