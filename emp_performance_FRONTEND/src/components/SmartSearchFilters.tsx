import { useState, useEffect, useRef } from 'react';
import { Filter, X, Calendar, ChevronDown, Users, Briefcase, TrendingUp, RotateCcw, Sparkles } from 'lucide-react';

// Types
interface Employee {
  id: number;
  name: string;
  email: string;
}

export interface FilterOptions {
  projects: string[];
  statuses: string[];
  dateRange: {
    start: string | null;
    end: string | null;
  };
}

interface SmartFiltersProps {
  onFiltersApply: (filters: FilterOptions) => void;
  apiBaseUrl: string;
}

const SmartFilters = ({ onFiltersApply, apiBaseUrl }: SmartFiltersProps) => {
  // State
  const [showFilters, setShowFilters] = useState(false);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [isLoadingEmployees, setIsLoadingEmployees] = useState(false);

  // Filter states
  const [selectedProjects, setSelectedProjects] = useState<string[]>([]);
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [activeFiltersCount, setActiveFiltersCount] = useState(0);

  // Refs
  const filtersRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);

  // Available options
  const availableProjects = ['Lyell', 'DataPlatr'];
  const availableStatuses = ['Excellent', 'Good', 'Inconsistent', 'Poor', 'Very Poor', 'Non-Reporter'];

  const QUICK_FILTERS = [
    { id: 'top-performers', label: 'Top Performers' },
    { id: 'need-attention', label: 'Need Attention' },
    { id: 'lyell-project', label: 'Lyell Project' },
    { id: 'dataplatr-project', label: 'DataPlatr' },
    { id: 'this-week', label: 'This Week' },
    { id: 'this-month', label: 'This Month' }
  ];

  // Fetch employees on mount
  useEffect(() => {
    fetchEmployees();
  }, []);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        filtersRef.current &&
        !filtersRef.current.contains(event.target as Node) &&
        buttonRef.current &&
        !buttonRef.current.contains(event.target as Node)
      ) {
        setShowFilters(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Update active filters count
  useEffect(() => {
    let count = 0;
    if (selectedProjects.length > 0) count++;
    if (selectedStatuses.length > 0) count++;
    if (startDate || endDate) count++;
    setActiveFiltersCount(count);
  }, [selectedProjects, selectedStatuses, startDate, endDate]);

  // Fetch employees from backend
  const fetchEmployees = async () => {
    setIsLoadingEmployees(true);
    try {
      const response = await fetch(`${apiBaseUrl}/employees`);
      if (!response.ok) throw new Error('Failed to fetch employees');
      const data = await response.json();
      setEmployees(data);
    } catch (error) {
      console.error('Error fetching employees:', error);
    } finally {
      setIsLoadingEmployees(false);
    }
  };

  // Toggle project filter
  const toggleProject = (project: string) => {
    setSelectedProjects(prev =>
      prev.includes(project)
        ? prev.filter(p => p !== project)
        : [...prev, project]
    );
  };

  // Toggle status filter
  const toggleStatus = (status: string) => {
    setSelectedStatuses(prev =>
      prev.includes(status)
        ? prev.filter(s => s !== status)
        : [...prev, status]
    );
  };

  // Apply filters
  const applyFilters = () => {
    const filters: FilterOptions = {
      projects: selectedProjects,
      statuses: selectedStatuses,
      dateRange: {
        start: startDate || null,
        end: endDate || null
      }
    };

    onFiltersApply(filters);
    setShowFilters(false);
  };

  // Reset filters
  const resetFilters = () => {
    setSelectedProjects([]);
    setSelectedStatuses([]);
    setStartDate('');
    setEndDate('');

    onFiltersApply({
      projects: [],
      statuses: [],
      dateRange: { start: null, end: null }
    });
  };

  // Quick filter presets - sets filters and applies them
  const applyQuickFilter = (type: string) => {
    // Reset all filters first
    setSelectedProjects([]);
    setSelectedStatuses([]);
    setStartDate('');
    setEndDate('');

    let newFilters: FilterOptions = {
      projects: [],
      statuses: [],
      dateRange: { start: null, end: null }
    };

    switch (type) {
      case 'top-performers':
        newFilters.statuses = ['Excellent', 'Good'];
        setSelectedStatuses(['Excellent', 'Good']);
        break;
      case 'need-attention':
        newFilters.statuses = ['Poor', 'Very Poor', 'Non-Reporter'];
        setSelectedStatuses(['Poor', 'Very Poor', 'Non-Reporter']);
        break;
      case 'lyell-project':
        newFilters.projects = ['Lyell'];
        setSelectedProjects(['Lyell']);
        break;
      case 'dataplatr-project':
        newFilters.projects = ['DataPlatr'];
        setSelectedProjects(['DataPlatr']);
        break;
      case 'this-week':
        const today = new Date();
        const weekAgo = new Date(today);
        weekAgo.setDate(today.getDate() - 7);
        const weekStart = weekAgo.toISOString().split('T')[0];
        const weekEnd = today.toISOString().split('T')[0];
        newFilters.dateRange = { start: weekStart, end: weekEnd };
        setStartDate(weekStart);
        setEndDate(weekEnd);
        break;
      case 'this-month':
        const monthStart = new Date();
        monthStart.setDate(1);
        const monthStartStr = monthStart.toISOString().split('T')[0];
        const monthEndStr = new Date().toISOString().split('T')[0];
        newFilters.dateRange = { start: monthStartStr, end: monthEndStr };
        setStartDate(monthStartStr);
        setEndDate(monthEndStr);
        break;
    }

    // Apply the filters immediately
    onFiltersApply(newFilters);
  };

  return (
    <div className="glass-card border-x-0 border-t-0 sticky top-0 z-20 animate-entrance backdrop-blur-3xl bg-white/60">
      <div className="max-w-7xl mx-auto px-6 py-5">
        <div className="flex flex-wrap items-center justify-between gap-6">
          <div className="flex items-center gap-4 overflow-x-auto no-scrollbar pb-1">
            <div className="flex items-center gap-2 mr-4 border-r border-slate-200 pr-6">
              <div className="p-2 bg-indigo-50 rounded-xl">
                <Filter className="w-5 h-5 text-indigo-600" />
              </div>
              <span className="text-xs font-black text-slate-400 uppercase tracking-widest">Insights</span>
            </div>

            {QUICK_FILTERS.map((filter) => (
              <button
                key={filter.id}
                onClick={() => applyQuickFilter(filter.id)}
                className="flex items-center gap-2.5 px-6 py-2.5 rounded-2xl text-[13px] font-black transition-all duration-500 whitespace-nowrap border shadow-sm hover:shadow-xl hover:shadow-indigo-500/5 active:scale-95 group"
                style={{
                  backgroundColor: 'white',
                  borderColor: '#f1f5f9',
                  color: '#475569'
                }}
              >
                <div className="w-1.5 h-1.5 rounded-full bg-slate-200 group-hover:bg-indigo-400 group-hover:scale-125 transition-all duration-500"></div>
                {filter.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-5">
            <button
              ref={buttonRef}
              onClick={() => setShowFilters(!showFilters)}
              className={`flex items-center gap-3 px-6 py-3 rounded-2xl text-sm font-black transition-all duration-500 border ${showFilters
                ? 'bg-indigo-600 text-white border-indigo-600 shadow-2xl shadow-indigo-600/30'
                : 'bg-white text-slate-700 border-slate-100 hover:border-indigo-200 hover:bg-slate-50 shadow-sm hover:shadow-xl hover:shadow-indigo-500/5'
                }`}
            >
              <div className={`p-1 rounded-lg transition-colors ${showFilters ? 'bg-white/20' : 'bg-indigo-50'}`}>
                <Filter className={`w-4 h-4 ${showFilters ? 'text-white' : 'text-indigo-600'}`} />
              </div>
              <span>{showFilters ? 'Hide Filters' : 'Refine Search'}</span>
              {activeFiltersCount > 0 && !showFilters && (
                <span className="flex items-center justify-center w-5 h-5 bg-indigo-600 text-white text-[10px] font-black rounded-lg shadow-lg">
                  {activeFiltersCount}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Advanced Filters Panel */}
        {showFilters && (
          <div ref={filtersRef} className="mt-8 p-10 bg-white/95 backdrop-blur-3xl rounded-[3rem] border border-white shadow-[0_32px_64px_-16px_rgba(0,0,0,0.1)] relative z-50 overflow-hidden group/panel animate-entrance">
            <div className="absolute -top-32 -right-32 w-80 h-80 bg-indigo-500/5 blur-[100px] rounded-full group-hover/panel:bg-indigo-500/10 transition-all duration-1000"></div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-12 relative z-10">
              {/* Project Filter */}
              <div className="space-y-6">
                <label className="text-[11px] font-black text-slate-400 uppercase tracking-[0.15em] flex items-center gap-4">
                  <div className="p-3 bg-indigo-50 rounded-2xl shadow-sm">
                    <Briefcase className="w-5 h-5 text-indigo-600" />
                  </div>
                  Projects Focus
                </label>
                <div className="space-y-3.5">
                  {availableProjects.map(project => (
                    <label key={project} className="flex items-center gap-5 cursor-pointer group p-4 hover:bg-white rounded-2xl transition-all border border-transparent hover:border-indigo-100 hover:shadow-xl hover:shadow-indigo-500/5">
                      <div className="relative flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedProjects.includes(project)}
                          onChange={() => toggleProject(project)}
                          className="w-6 h-6 text-indigo-600 rounded-lg border-slate-300 focus:ring-offset-0 focus:ring-4 focus:ring-indigo-500/10 cursor-pointer transition-all"
                        />
                      </div>
                      <span className="font-black text-slate-700 group-hover:text-slate-950 transition-colors">{project}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Status Filter */}
              <div className="space-y-6">
                <label className="text-[11px] font-black text-slate-400 uppercase tracking-[0.15em] flex items-center gap-4">
                  <div className="p-3 bg-emerald-50 rounded-2xl shadow-sm">
                    <TrendingUp className="w-5 h-5 text-emerald-600" />
                  </div>
                  Performance Status
                </label>
                <div className="space-y-2 max-h-80 overflow-y-auto pr-4 custom-scrollbar">
                  {availableStatuses.map(status => (
                    <label key={status} className="flex items-center gap-5 cursor-pointer group p-3.5 hover:bg-white rounded-2xl transition-all border border-transparent hover:border-indigo-100 hover:shadow-xl hover:shadow-indigo-500/5">
                      <div className="relative flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedStatuses.includes(status)}
                          onChange={() => toggleStatus(status)}
                          className="w-5 h-5 text-indigo-600 rounded-lg border-slate-300 focus:ring-offset-0 focus:ring-4 focus:ring-indigo-500/10 cursor-pointer"
                        />
                      </div>
                      <span className="text-sm font-black text-slate-600 group-hover:text-slate-900 transition-colors">{status}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Date Range Filter */}
              <div className="space-y-6">
                <label className="text-[11px] font-black text-slate-400 uppercase tracking-[0.15em] flex items-center gap-4">
                  <div className="p-3 bg-rose-50 rounded-2xl shadow-sm">
                    <Calendar className="w-5 h-5 text-rose-600" />
                  </div>
                  Custom Date Range
                </label>
                <div className="space-y-5">
                  <div className="relative group/date">
                    <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest pl-1 mb-2 block">Start Point</label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-100 rounded-2xl text-[13px] font-black text-slate-700 outline-none focus:ring-8 focus:ring-indigo-500/5 focus:border-indigo-200 focus:bg-white transition-all appearance-none cursor-pointer"
                    />
                  </div>
                  <div className="relative group/date">
                    <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest pl-1 mb-2 block">Terminal Point</label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-6 py-4 bg-slate-50 border border-slate-100 rounded-2xl text-[13px] font-black text-slate-700 outline-none focus:ring-8 focus:ring-indigo-500/5 focus:border-indigo-200 focus:bg-white transition-all appearance-none cursor-pointer"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-12 pt-8 border-t border-slate-100/60 flex items-center justify-between relative z-10">
              <button
                onClick={resetFilters}
                className="flex items-center gap-3 px-6 py-3.5 rounded-2xl text-[13px] font-black text-slate-400 hover:text-rose-500 hover:bg-rose-50 transition-all duration-500 group"
              >
                <RotateCcw className="w-5 h-5 group-hover:rotate-90 transition-transform duration-500" />
                Reset all parameters
              </button>

              <div className="flex items-center gap-5">
                <button
                  onClick={() => setShowFilters(false)}
                  className="px-8 py-3.5 rounded-2xl text-[13px] font-black text-slate-600 hover:bg-slate-100 transition-all duration-500"
                >
                  Discard
                </button>
                <button
                  onClick={applyFilters}
                  className="px-12 py-3.5 bg-indigo-600 text-white rounded-2xl text-[13px] font-black shadow-2xl shadow-indigo-600/20 hover:shadow-indigo-600/40 hover:-translate-y-1 active:translate-y-0 active:scale-95 transition-all duration-500 btn-premium shimmer-effect"
                >
                  Refine Intelligence
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Active Filters Display */}
        {activeFiltersCount > 0 && !showFilters && (
          <div className="mt-6 flex flex-wrap gap-3.5 items-center animate-entrance bg-indigo-50/30 p-3 rounded-[1.75rem] border border-indigo-100/50">
            <div className="flex items-center gap-2.5 ml-3 mr-1">
              <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-pulse"></div>
              <span className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.25em]">Criteria Active</span>
            </div>
            {selectedProjects.map(project => (
              <span key={project} className="px-4 py-2 bg-white text-indigo-700 border border-indigo-100 shadow-sm rounded-xl text-[11px] flex items-center gap-3 font-black hover:shadow-md transition-all">
                {project}
                <button onClick={() => toggleProject(project)} className="p-1 hover:bg-indigo-50 text-indigo-300 hover:text-indigo-600 rounded-lg transition-all">
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            ))}
            {selectedStatuses.map(status => (
              <span key={status} className="px-4 py-2 bg-white text-indigo-700 border border-indigo-100 shadow-sm rounded-xl text-[11px] flex items-center gap-3 font-black hover:shadow-md transition-all">
                {status}
                <button onClick={() => toggleStatus(status)} className="p-1 hover:bg-indigo-50 text-indigo-300 hover:text-indigo-600 rounded-lg transition-all">
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            ))}
            {(startDate || endDate) && (
              <span key="date" className="px-4 py-2 bg-white text-indigo-700 border border-indigo-100 shadow-sm rounded-xl text-[11px] flex items-center gap-3 font-black hover:shadow-md transition-all">
                <Calendar className="w-4 h-4 text-indigo-400" />
                {startDate && endDate ? `${startDate} to ${endDate}` : startDate || endDate}
                <button onClick={() => { setStartDate(''); setEndDate(''); }} className="p-1 hover:bg-indigo-50 text-indigo-300 hover:text-indigo-600 rounded-lg transition-all">
                  <X className="w-3.5 h-3.5" />
                </button>
              </span>
            )}
            <button
              onClick={resetFilters}
              className="px-4 py-2 text-[10px] text-rose-500 font-black uppercase tracking-[0.2em] hover:bg-rose-50 rounded-xl transition-all ml-1"
            >
              Clear All
            </button>
          </div>
        )}
      </div>
    </div>
  );
};



export default SmartFilters;