// src/components/MessageBubble.tsx
import { Bot, User, Download, ChevronRight } from 'lucide-react';
import { Message, ChartData } from "../types";
import DynamicChart from "./DynamicChart";
import { useMemo } from 'react';

interface MessageBubbleProps {
  message: Message;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isBot = message.sender === 'bot';

  // Add this function to format chart data from comprehensiveCharts if needed
  const getChartFromComprehensiveData = useMemo((): ChartData | null => {
    // If we have comprehensiveCharts in the message, use that
    if (message.comprehensiveCharts) {
      const charts = message.comprehensiveCharts;

      // Team Status Distribution (Doughnut)
      if (message.text.toLowerCase().includes('status') || message.text.toLowerCase().includes('breakdown')) {
        if (charts.status_distribution && charts.status_distribution.length > 0) {
          return {
            chartType: 'doughnut',
            chartTitle: 'Team Status Distribution',
            labels: charts.status_distribution.map((d: { status: any; }) => d.status),
            datasets: [{
              label: 'Employees',
              data: charts.status_distribution.map((d: { count: any; }) => d.count),
              backgroundColor: ['#10B981', '#3B82F6', '#F59E0B', '#F97316', '#EF4444', '#64748B']
            }]
          };
        }
      }

      // Project Distribution (Doughnut)
      if (message.text.toLowerCase().includes('project') && (message.text.toLowerCase().includes('distribution') || message.text.toLowerCase().includes('share'))) {
        if (charts.project_distribution && charts.project_distribution.length > 0) {
          return {
            chartType: 'doughnut',
            chartTitle: 'Project Workload Distribution',
            labels: charts.project_distribution.map((d: { project: any; }) => d.project),
            datasets: [{
              label: 'Hours',
              data: charts.project_distribution.map((d: { hours: any; }) => d.hours),
              backgroundColor: ['#6366F1', '#8B5CF6', '#EC4899', '#06B6D4', '#F97316']
            }]
          };
        }
      }

      // For Lyell queries, use appropriate data
      if (message.text.toLowerCase().includes('lyell')) {
        // Use top contributors chart
        if (charts.top_submitters && charts.top_submitters.length > 0) {
          return {
            chartType: 'bar',
            chartTitle: 'Top Lyell Contributors',
            labels: charts.top_submitters.slice(0, 10).map((emp: { name: any; }) => emp.name),
            datasets: [{
              label: 'Hours',
              data: charts.top_submitters.slice(0, 10).map((emp: { rate: any; }) => emp.rate || 0),
              backgroundColor: ['#36A2EB', '#FF6384', '#FFCE56', '#4BC0C0', '#9966FF',
                '#ffa040', '#C9CBCF', '#8AC926', '#1982C4', '#6A4C93']
            }]
          };
        }
      }

      // For general performance queries
      if (message.text.toLowerCase().includes('performance')) {
        if (charts.top_hours && charts.top_hours.length > 0) {
          return {
            chartType: 'bar',
            chartTitle: 'Employee Performance',
            labels: charts.top_hours.slice(0, 10).map((emp: { name: any; }) => emp.name),
            datasets: [{
              label: 'Average Daily Hours',
              data: charts.top_hours.slice(0, 10).map((emp: { hours: any; }) => emp.hours || 0),
              backgroundColor: ['#36A2EB', '#4BC0C0', '#FFCE56', '#FF9F40', '#FF6384',
                '#9966FF', '#C9CBCF', '#8AC926', '#1982C4', '#6A4C93']
            }]
          };
        }
      }
    }

    return null;
  }, [message.comprehensiveCharts, message.text]);

  // Update the extractedChartData logic
  const extractedChartData = useMemo((): ChartData | null => {
    // Priority 1: Explicit chartData from message
    if (message.chartData && message.chartData.chartType !== 'none') {
      return message.chartData;
    }

    // Priority 2: Comprehensive charts data
    const comprehensiveChart = getChartFromComprehensiveData;
    if (comprehensiveChart) {
      return comprehensiveChart;
    }

    // Priority 3: Extract from text JSON
    if (!isBot || !message.text.includes('```json')) {
      return null;
    }

    try {
      const jsonMatch = message.text.match(/```json\s*([\s\S]*?)\s*```/);
      if (!jsonMatch || !jsonMatch[1]) {
        return null;
      }

      const chartData = JSON.parse(jsonMatch[1]) as ChartData;

      if (chartData.chartType && chartData.chartType !== 'none') {
        return chartData;
      }
    } catch (error) {
      console.error('Failed to parse embedded chart data:', error);
    }

    return null;
  }, [message.chartData, message.text, isBot, getChartFromComprehensiveData]);

  // Update the cleanedText function to handle JSON better
  const cleanedText = useMemo(() => {
    if (!isBot) return message.text;

    let text = message.text;

    // Remove chart data sections more aggressively
    if (text.includes('```json')) {
      text = text.replace(/```json\s*[\s\S]*?\s*```/g, '').trim();
    }

    // Remove any stray JSON-like content
    if (text.includes('{') && text.includes('}')) {
      const lines = text.split('\n');
      const cleanLines = lines.filter(line => {
        const trimmed = line.trim();
        return !(trimmed.startsWith('{') && trimmed.endsWith('}')) &&
          !(trimmed.includes('"chartType"')) &&
          !(trimmed.includes('"datasets"')) &&
          !(trimmed.includes('"labels"'));
      });
      text = cleanLines.join('\n').trim();
    }

    // Remove the chart data section if it exists (keep for backward compatibility)
    if (text.includes('### CHART DATA STRUCTURE')) {
      text = text.replace(/### CHART DATA STRUCTURE[\s\S]*?```json[\s\S]*?```/g, '').trim();
    }

    // Remove extra blank lines
    text = text.replace(/\n\s*\n\s*\n/g, '\n\n');

    return text || "Analysis complete. See chart below.";
  }, [message.text, isBot]);

  // Format message text with markdown-like styling
  const formatMessageText = (text: string) => {
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      // Bold text between ** **
      if (line.includes('**')) {
        const parts = line.split(/(\*\*.*?\*\*)/g);
        return (
          <div key={idx} className="mb-1.5 text-slate-700">
            {parts.map((part, i) => {
              if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={i} className="font-semibold text-slate-900">{part.slice(2, -2)}</strong>;
              }
              return <span key={i}>{part}</span>;
            })}
          </div>
        );
      }

      // Bullet points
      if (line.trim().startsWith('*') && line.trim().length > 1) {
        return (
          <div key={idx} className="flex items-start gap-2.5 mb-1.5 ml-1">
            <span className="text-indigo-500 mt-1.5 text-[10px]">•</span>
            <span className="text-slate-700">{line.replace(/^\*\s*/, '')}</span>
          </div>
        );
      }

      // Dashes as bullet points
      if (line.trim().startsWith('-') && line.trim().length > 1) {
        return (
          <div key={idx} className="flex items-start gap-2.5 mb-1.5 ml-1">
            <span className="text-indigo-500 mt-1.5 text-[10px]">•</span>
            <span className="text-slate-700">{line.replace(/^-\s*/, '')}</span>
          </div>
        );
      }

      // Numbers for ordered lists
      if (/^\d+\./.test(line.trim())) {
        return (
          <div key={idx} className="flex items-start gap-2 mb-1.5 ml-1">
            <span className="font-semibold text-indigo-600 min-w-5 text-sm">{line.match(/^\d+\./)?.[0]}</span>
            <span className="text-slate-700">{line.replace(/^\d+\.\s*/, '')}</span>
          </div>
        );
      }

      // Empty lines
      if (line.trim() === '') {
        return <div key={idx} className="h-2" />;
      }

      // Headers with ##
      if (line.trim().startsWith('##')) {
        return (
          <div key={idx} className="font-bold text-slate-900 text-lg mt-4 mb-3 tracking-tight">
            {line.replace(/^#+\s*/, '')}
          </div>
        );
      }

      // Section headers ending with :
      if (line.trim().endsWith(':') && line.trim().length < 100) {
        return (
          <div key={idx} className="font-semibold text-slate-800 mt-3 mb-1.5">
            {line}
          </div>
        );
      }

      // Dividers (---)
      if (line.trim() === '---' || line.trim() === '•') {
        return <div key={idx} className="border-t border-slate-200 my-4" />;
      }

      // Regular lines
      return <div key={idx} className="mb-1.5 text-slate-700 leading-normal">{line}</div>;
    });
  };

  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} mb-8 group animate-entrance`}>
      <div className={`max-w-[85%] sm:max-w-2xl lg:max-w-3xl ${isBot ? '' : 'flex justify-end'}`}>
        <div className={`flex gap-3 sm:gap-5 ${isBot ? '' : 'flex-row-reverse'}`}>
          {/* Avatar */}
          <div className={`flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 rounded-[1.25rem] flex items-center justify-center shadow-lg transition-all duration-500 hover:rotate-6 ${isBot
            ? 'bg-gradient-to-br from-indigo-500 via-indigo-600 to-purple-600 shadow-indigo-200'
            : 'bg-white border border-slate-200 shadow-slate-100'
            }`}>
            {isBot ? (
              <Bot className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            ) : (
              <User className="w-5 h-5 sm:w-6 sm:h-6 text-indigo-500" />
            )}
          </div>

          {/* Message content */}
          <div className={`flex flex-col ${isBot ? 'items-start' : 'items-end'}`}>
            {/* Text message bubble */}
            <div
              className={`px-6 sm:px-8 py-5 sm:py-6 shadow-sm transition-all duration-500 ${isBot
                ? 'bg-white border border-slate-100 text-slate-900 rounded-[2rem] rounded-tl-none premium-shadow'
                : 'bg-gradient-to-br from-indigo-600 to-indigo-700 text-white rounded-[2rem] rounded-tr-none shadow-2xl shadow-indigo-200 border border-indigo-500/50'
                }`}
            >
              <div className={`text-[15px] sm:text-[17px] leading-relaxed tracking-tight ${isBot ? 'font-medium' : 'font-black text-white'}`}>
                {isBot ? formatMessageText(cleanedText) : cleanedText}
              </div>
            </div>

            {/* Timestamp */}
            <div
              className={`text-[9px] font-black uppercase tracking-[0.2em] mt-3 transition-all duration-700 opacity-20 group-hover:opacity-60 ${isBot ? 'text-slate-400 pl-3' : 'text-right text-slate-400 pr-3'
                }`}
            >
              <span className="opacity-50 mr-1">Sent at</span>
              {message.timestamp.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>

            {/* Invoice Download Action */}
            {isBot && message.invoice_metadata && (
              <div className="mt-4 w-full animate-entrance">
                <button
                  onClick={() => {
                    const { year, month } = message.invoice_metadata!;
                    const downloadUrl = `http://localhost:5000/api/lyell/invoice/monthly/${year}/${month}/pdf`;
                    const link = document.createElement('a');
                    link.href = downloadUrl;
                    link.setAttribute('download', `Lyell_Invoice_${year}-${month}.pdf`);
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                  }}
                  className="flex items-center justify-between w-full px-6 py-4 bg-indigo-50 border border-indigo-100 rounded-2xl hover:bg-indigo-100 hover:border-indigo-200 transition-all group/pdf shadow-sm"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2.5 bg-white rounded-xl shadow-sm text-indigo-600 group-hover/pdf:scale-110 transition-transform">
                      <Download className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-sm font-black text-indigo-900 tracking-tight">Export Official PDF Ledger</p>
                      <p className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest mt-0.5">Lyell Project • {message.invoice_metadata.year}-{String(message.invoice_metadata.month).padStart(2, '0')}</p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-indigo-300 group-hover/pdf:translate-x-1 transition-transform" />
                </button>
              </div>
            )}

            {/* Chart section - now uses extracted chart data */}
            {isBot && extractedChartData && (
              <div className="mt-6 w-full glass-card rounded-3xl p-1 animate-entrance premium-shadow border-white/40">
                <div className="bg-white/40 rounded-[1.4rem] p-4 lg:p-6 overflow-hidden">
                  <DynamicChart chartData={extractedChartData} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MessageBubble;