// src/components/ChatInterface.tsx
import { useState, useRef, useEffect } from 'react';
import { Send, Lightbulb, ChevronDown, ChevronRight, X } from 'lucide-react';
import MessageBubble from './MessageBubble';

import { Message } from '../types';
import SmartFilters from './SmartSearchFilters';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (text: string) => void;
  isLoading: boolean;
  apiBaseUrl: string; // Add this prop
}

export interface FilterOptions {
  projects: string[];
  statuses: string[];
  dateRange: {
    start: string | null;
    end: string | null;
  };
}

// Organized suggested questions by category
const SUGGESTED_QUESTIONS = {
  'Employee Performance': [
    "Show me John Doe's performance",
    "How is Alice performing?",
    "Analyze Bob Wilson's metrics",
    "What's Sarah's submission rate?",
    "Check Mark's recent activity",
    "Show details for employee with email john@company.com"
  ],

  'Team Overview': [
    "Show team performance",
    "Team overview this month",
    "Overall team metrics",
    "Company performance dashboard",
    "Team submission rates",
    "Workload distribution across team",
    "Average daily hours for team"
  ],

  'Top Performers': [
    "Who are the top performers?",
    "Show me best performing employees",
    "Top 5 performers this month",
    "Highest submission rates",
    "Most productive employees",
    "Employees with best completion ratio",
    "High performers (>3 tasks/day)"
  ],

  'Need Attention': [
    "Which employees need attention?",
    "Show struggling employees",
    "Employees with low submission rate",
    "Who has the most gaps?",
    "Frequent defaulters",
    "Employees with poor performance",
    "Who is underperforming?"
  ],

  'Metrics & Stats': [
    "What's the average submission rate?",
    "Show average daily hours",
    "Team completion ratio",
    "Task diversity across team",
    "Recent activity (last 7 days)",
    "Submission trends",
    "Workload statistics"
  ],

  'Billing & Projects': [
    "Show Lyell billing summary",
    "Analyze DataPlatr project billing",
    "Lyell billing for last month",
    "DataPlatr project hours",
    "Show project billing overview",
    "Billable vs extra hours analysis"
  ],

  'SOW Compliance': [
    "Find Lyell SOW violations",
    "Check SOW compliance for Lyell",
    "Extra hours on Lyell project",
    "ETL hours exceeding caps",
    "Reporting violations",
    "Out of scope hours for Lyell",
    "SOW compliance rate"
  ],

  'Time Based': [
    "Performance this week",
    "Last month's metrics",
    "Quarterly overview",
    "Today's submissions",
    "Yesterday's activity",
    "Recent 30 days performance",
    "Weekly trends analysis"
  ],

  'Analytical': [
    "What patterns do you see?",
    "Identify trends in performance",
    "Any red flags to watch?",
    "Where can we improve?",
    "Strengths and weaknesses analysis",
    "Recommendations for improvement",
    "Action items for team"
  ]
};

function ChatInterface({ messages, onSendMessage, isLoading, apiBaseUrl }: ChatInterfaceProps) {
  const [inputText, setInputText] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [expandedCategories, setExpandedCategories] = useState<string[]>(['Team Overview', 'Quick Questions']);
  const [activeFilters, setActiveFilters] = useState<FilterOptions>({
    projects: [],
    statuses: [],
    dateRange: { start: null, end: null }
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Generate natural language query from filters
  const generateFilterQuery = (filters: FilterOptions): string => {
    let query = '';

    // Determine the type of filter and create appropriate query
    const hasProjects = filters.projects.length > 0;
    const hasStatuses = filters.statuses.length > 0;
    const hasDateRange = filters.dateRange.start || filters.dateRange.end;

    // Top performers query
    if (hasStatuses &&
      filters.statuses.includes('Excellent') &&
      filters.statuses.includes('Good') &&
      filters.statuses.length === 2) {
      query = 'Show top performing employees';
    }
    // Need attention query
    else if (hasStatuses &&
      (filters.statuses.includes('Poor') ||
        filters.statuses.includes('Very Poor') ||
        filters.statuses.includes('Non-Reporter'))) {
      query = 'Show employees needing attention';
    }
    // Project specific queries
    else if (hasProjects && filters.projects.length === 1) {
      query = `Show ${filters.projects[0]} project analysis`;
    }
    else if (hasProjects && filters.projects.length > 1) {
      query = `Show ${filters.projects.join(' and ')} projects analysis`;
    }
    // Date range queries
    else if (hasDateRange && !hasProjects && !hasStatuses) {
      if (filters.dateRange.start && filters.dateRange.end) {
        const start = new Date(filters.dateRange.start);
        const end = new Date(filters.dateRange.end);
        const daysDiff = Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));

        if (daysDiff <= 7) {
          query = 'Show performance for the last 7 days';
        } else if (daysDiff <= 31) {
          query = 'Show performance for this month';
        } else {
          query = `Show performance from ${filters.dateRange.start} to ${filters.dateRange.end}`;
        }
      } else if (filters.dateRange.start) {
        query = `Show performance since ${filters.dateRange.start}`;
      } else if (filters.dateRange.end) {
        query = `Show performance until ${filters.dateRange.end}`;
      }
    }
    // Generic combination query
    else {
      const parts: string[] = [];

      if (hasProjects) {
        parts.push(`${filters.projects.join(' and ')} project${filters.projects.length > 1 ? 's' : ''}`);
      }

      if (hasStatuses) {
        parts.push(`employees with ${filters.statuses.join(' or ')} status`);
      }

      if (hasDateRange) {
        if (filters.dateRange.start && filters.dateRange.end) {
          parts.push(`from ${filters.dateRange.start} to ${filters.dateRange.end}`);
        } else if (filters.dateRange.start) {
          parts.push(`since ${filters.dateRange.start}`);
        } else if (filters.dateRange.end) {
          parts.push(`until ${filters.dateRange.end}`);
        }
      }

      query = parts.length > 0 ? `Show ${parts.join(' ')}` : '';
    }

    return query;
  };

  // Handle filter application
  const handleFiltersApply = (filters: FilterOptions) => {
    setActiveFilters(filters);

    // Generate and send query if any filters are active
    const hasActiveFilters =
      filters.projects.length > 0 ||
      filters.statuses.length > 0 ||
      filters.dateRange.start !== null ||
      filters.dateRange.end !== null;

    if (hasActiveFilters) {
      const query = generateFilterQuery(filters);
      if (query) {
        onSendMessage(query);
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (inputText.trim() && !isLoading) {
      // Append filter context to the query if filters are active
      let finalQuery = inputText.trim();

      const hasActiveFilters =
        activeFilters.projects.length > 0 ||
        activeFilters.statuses.length > 0 ||
        activeFilters.dateRange.start !== null ||
        activeFilters.dateRange.end !== null;

      if (hasActiveFilters) {
        const filterContext: string[] = [];

        if (activeFilters.projects.length > 0) {
          filterContext.push(`filtered to ${activeFilters.projects.join(' and ')} project(s)`);
        }

        if (activeFilters.statuses.length > 0) {
          filterContext.push(`status: ${activeFilters.statuses.join(', ')}`);
        }

        if (activeFilters.dateRange.start || activeFilters.dateRange.end) {
          const dateStr = activeFilters.dateRange.start && activeFilters.dateRange.end
            ? `${activeFilters.dateRange.start} to ${activeFilters.dateRange.end}`
            : activeFilters.dateRange.start || activeFilters.dateRange.end;
          filterContext.push(`date range: ${dateStr}`);
        }

        if (filterContext.length > 0) {
          finalQuery += ` (${filterContext.join(', ')})`;
        }
      }

      onSendMessage(finalQuery);
      setInputText('');
      setShowSuggestions(false);
    }
  };

  const handleSuggestionClick = (question: string) => {
    onSendMessage(question);
    setShowSuggestions(false);
  };

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  // Render category with questions
  const renderCategory = (category: string, questions: string[]) => {
    const isExpanded = expandedCategories.includes(category);

    return (
      <div key={category} className="bg-white/50 rounded-2xl border border-slate-100 overflow-hidden hover:border-indigo-100 hover:shadow-xl hover:shadow-indigo-500/5 transition-all duration-500">
        <button
          onClick={() => toggleCategory(category)}
          className="flex items-center justify-between w-full p-5 bg-white/80 hover:bg-white transition-all group"
          disabled={isLoading}
        >
          <div className="flex items-center gap-4">
            <div className={`w-2.5 h-2.5 rounded-full transition-all duration-700 ${isExpanded ? 'bg-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.6)] animate-pulse' : 'bg-slate-200'}`}></div>
            <span className={`font-black transition-colors text-sm tracking-tight ${isExpanded ? 'text-indigo-950' : 'text-slate-600'}`}>{category}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-[10px] font-black px-2.5 py-1 rounded-lg transition-all ${isExpanded ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200' : 'bg-slate-100 text-slate-400'}`}>
              {questions.length}
            </span>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-indigo-500 group-hover:translate-y-0.5 transition-transform duration-500" />
            ) : (
              <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-transform duration-500" />
            )}
          </div>
        </button>

        {isExpanded && (
          <div className="p-4 space-y-2.5 bg-slate-50/40 animate-entrance">
            {questions.map((question, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(question)}
                className="w-full text-left p-4 text-[13px] font-bold text-slate-600 hover:text-indigo-700 hover:bg-white rounded-2xl transition-all border border-transparent hover:border-indigo-100 shadow-sm hover:shadow-xl hover:shadow-indigo-500/5 truncate flex items-center gap-4 group/item"
                disabled={isLoading}
                title={question}
              >
                <div className="w-1.5 h-1.5 bg-slate-200 rounded-full group-hover/item:bg-indigo-400 group-hover/item:scale-125 transition-all duration-500"></div>
                <span className="truncate">{question}</span>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-slate-50/30">
      {/* Smart Filters Component */}
      <SmartFilters
        onFiltersApply={handleFiltersApply}
        apiBaseUrl={apiBaseUrl}
      />

      <div className="flex-1 overflow-y-auto p-6 md:p-8 space-y-8 custom-scrollbar scroll-smooth bg-mesh">
        {messages.map((message) => (
          <div key={message.id}>
            <MessageBubble message={message} />
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start animate-entrance">
            <div className="bg-white border border-slate-100 rounded-2xl px-6 py-4 shadow-xl shadow-slate-200/50 flex items-center gap-4">
              <div className="flex space-x-2">
                <div className="w-2.5 h-2.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                <div className="w-2.5 h-2.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                <div className="w-2.5 h-2.5 bg-indigo-500 rounded-full animate-bounce"></div>
              </div>
              <span className="text-xs text-slate-400 font-black uppercase tracking-widest">Analyzing Data Engine...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} className="h-4" />
      </div>

      <div className="p-6 md:p-10 bg-gradient-to-t from-white via-white/95 to-transparent backdrop-blur-md">
        {showSuggestions && (
          <div className="max-w-6xl mx-auto mb-10 animate-entrance">
            <div className="glass-card rounded-[3rem] p-10 shadow-2xl shadow-indigo-500/10 relative overflow-hidden group/modal border-white/60">
              {/* Background Glows */}
              <div className="absolute -top-32 -right-32 w-80 h-80 bg-indigo-500/20 blur-[100px] rounded-full"></div>
              <div className="absolute -bottom-32 -left-32 w-80 h-80 bg-purple-500/20 blur-[100px] rounded-full"></div>

              <div className="flex items-center justify-between mb-10 relative z-10">
                <div className="flex items-center gap-5">
                  <div className="p-4 bg-amber-50 rounded-2xl group-hover/modal:bg-amber-100 group-hover:rotate-6 transition-all duration-500 shadow-sm shadow-amber-200/50">
                    <Lightbulb className="w-8 h-8 text-amber-500 animate-pulse" />
                  </div>
                  <div>
                    <span className="font-black text-slate-950 text-2xl tracking-tight">Intelligence Directory</span>
                    <p className="text-[10px] text-slate-400 font-extrabold uppercase tracking-[0.2em] mt-1.5 opacity-80">Empower your analysis with AI</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowSuggestions(false)}
                  className="p-3 hover:bg-slate-100 rounded-2xl text-slate-400 hover:text-slate-900 transition-all font-black text-xs flex items-center gap-2 group/close"
                >
                  <X className="w-5 h-5 group-hover/close:rotate-90 transition-transform duration-500" />
                  Dismiss
                </button>
              </div>

              {/* Categories Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 max-h-[450px] overflow-y-auto pr-6 custom-scrollbar relative z-10">
                <div className="space-y-6">
                  {renderCategory('Employee Performance', SUGGESTED_QUESTIONS['Employee Performance'])}
                  {renderCategory('Team Overview', SUGGESTED_QUESTIONS['Team Overview'])}
                </div>

                <div className="space-y-6">
                  {renderCategory('Top Performers', SUGGESTED_QUESTIONS['Top Performers'])}
                  {renderCategory('Need Attention', SUGGESTED_QUESTIONS['Need Attention'])}
                  {renderCategory('Metrics & Stats', SUGGESTED_QUESTIONS['Metrics & Stats'])}
                </div>

                <div className="space-y-6">
                  {renderCategory('Billing & Projects', SUGGESTED_QUESTIONS['Billing & Projects'])}
                  {renderCategory('SOW Compliance', SUGGESTED_QUESTIONS['SOW Compliance'])}
                  {renderCategory('Analytical', SUGGESTED_QUESTIONS['Analytical'])}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="max-w-5xl mx-auto relative z-10 animate-entrance">
          <div className="relative group/input">
            {/* Pulsing Aura */}
            <div className="absolute -inset-1.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-[3rem] blur opacity-10 group-focus-within/input:opacity-25 transition-all duration-1000 group-focus-within/input:duration-500 group-hover/input:opacity-20 animate-pulse"></div>

            <div className="relative flex items-center bg-white/95 backdrop-blur-3xl border border-white shadow-2xl shadow-indigo-500/20 rounded-[2.5rem] focus-within:ring-8 focus-within:ring-indigo-500/5 focus-within:border-indigo-200 transition-all duration-700 p-2.5">
              <button
                type="button"
                onClick={() => setShowSuggestions(!showSuggestions)}
                className={`p-4 rounded-[1.75rem] transition-all duration-500 ${showSuggestions
                  ? 'text-indigo-600 bg-indigo-50 shadow-inner'
                  : 'text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 hover:shadow-lg hover:shadow-indigo-500/5'
                  }`}
                disabled={isLoading}
                title={showSuggestions ? "Hide Suggestions" : "Show Suggestions"}
              >
                <div className="relative">
                  <Lightbulb className={`w-7 h-7 ${showSuggestions ? 'animate-pulse' : ''}`} />
                  {showSuggestions && <div className="absolute inset-0 bg-indigo-400 blur-lg opacity-40 animate-pulse rounded-full"></div>}
                </div>
              </button>

              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Query your employee data engine..."
                className="flex-1 bg-transparent px-6 py-5 text-slate-900 placeholder-slate-400 focus:outline-none text-lg font-bold tracking-tight"
                disabled={isLoading}
                maxLength={500}
              />

              <div className="flex items-center gap-4 pr-3">
                <div className="h-10 w-px bg-slate-100 hidden sm:block mx-1"></div>
                <div className="hidden lg:flex flex-col items-end gap-1">
                  <span className="text-[9px] text-slate-300 font-black tracking-widest uppercase">Buffer</span>
                  <span className={`text-[10px] font-black tracking-widest ${inputText.length > 400 ? 'text-amber-500' : 'text-slate-400'}`}>
                    {inputText.length}/500
                  </span>
                </div>
                <button
                  type="submit"
                  disabled={!inputText.trim() || isLoading}
                  className="p-5 bg-indigo-600 text-white rounded-[1.75rem] hover:bg-indigo-700 disabled:bg-slate-100 disabled:text-slate-300 disabled:cursor-not-allowed transition-all duration-500 shadow-2xl shadow-indigo-600/30 hover:shadow-indigo-600/50 hover:-translate-y-1 active:translate-y-0 active:scale-95 group/submit"
                >
                  <Send className="w-5 h-5 group-hover/submit:translate-x-1 group-hover/submit:-translate-y-1 transition-transform duration-500" />
                </button>
              </div>
            </div>
          </div>
          <div className="mt-6 flex items-center justify-center gap-6">
            <div className="flex items-center gap-3 group/tip cursor-default">
              <span className="text-[9px] font-black text-indigo-600 uppercase tracking-[0.25em] px-3 py-1 bg-indigo-50 rounded-full group-hover/tip:bg-indigo-600 group-hover/tip:text-white transition-all duration-500">Intelli-Tip</span>
              <p className="text-[11px] text-slate-400 font-bold group-hover/tip:text-slate-600 transition-colors">Try "<span className="italic text-indigo-400 font-black group-hover/tip:text-indigo-500">Analyze team workload trends for last quarter</span>"</p>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ChatInterface;