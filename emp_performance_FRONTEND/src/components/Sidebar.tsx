import { X, Users, CheckCircle, XCircle, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';
import { Employee, EmployeeSummary } from '../types';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  employees: Employee[];
  summary: EmployeeSummary;
  onEmployeeClick: (employee: Employee) => void;
}

function Sidebar({ isOpen, onClose, employees, summary, onEmployeeClick }: SidebarProps) {
  const [showEmployees, setShowEmployees] = useState(true); // Changed to true by default

  return (
    <>
      <div
        className={`fixed inset-0 bg-black bg-opacity-50 transition-opacity z-40 ${isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
        onClick={onClose}
      />

      <aside
        className={`fixed left-0 top-0 h-full w-85 glass-card transform transition-transform duration-500 ease-out z-50 border-r border-white/20 ${isOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
      >
        <div className="flex flex-col h-full bg-mesh">
          <div className="flex items-center justify-between p-8 border-b border-slate-100 bg-white/60 backdrop-blur-md">
            <div>
              <h2 className="text-2xl font-black text-slate-900 tracking-tight">Team Overview</h2>
              <p className="text-[10px] text-slate-400 font-extrabold uppercase tracking-[0.2em] mt-1.5 opacity-80">Live Statistics</p>
            </div>
            <button
              onClick={onClose}
              className="p-3 hover:bg-slate-200/50 rounded-2xl transition-all duration-500 text-slate-400 hover:text-slate-900 group border border-transparent hover:border-slate-200"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5 group-hover:rotate-90 transition-transform duration-500" />
            </button>
          </div>

          <div className="p-8 space-y-6 border-b border-slate-100 bg-slate-50/40">
            <div className="bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-700 rounded-3xl p-6 shadow-2xl shadow-indigo-200 transition-all hover:shadow-indigo-300 hover:-translate-y-1 duration-500 group relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 blur-[40px] rounded-full -mr-16 -mt-16"></div>
              <div className="flex items-center gap-5 relative z-10">
                <div className="p-4 bg-white/15 rounded-2xl backdrop-blur-xl border border-white/20">
                  <Users className="w-8 h-8 text-white" />
                </div>
                <div>
                  <p className="text-[10px] font-black text-indigo-100 uppercase tracking-[0.2em]">Total Team</p>
                  <p className="text-4xl font-black text-white tracking-tighter mt-1">{summary.total_employees}</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-5">
              <div className="bg-white/80 backdrop-blur-sm rounded-3xl p-5 shadow-sm border border-slate-100 transition-all hover:shadow-xl hover:shadow-emerald-500/5 hover:border-emerald-200 group">
                <div className="flex flex-col gap-4">
                  <div className="p-2.5 bg-emerald-50 rounded-2xl w-fit group-hover:bg-emerald-100 transition-all duration-500 group-hover:rotate-6">
                    <CheckCircle className="w-6 h-6 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">Submitted</p>
                    <p className="text-3xl font-black text-slate-900 tracking-tighter mt-1">{summary.submitted_today}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white/80 backdrop-blur-sm rounded-3xl p-5 shadow-sm border border-slate-100 transition-all hover:shadow-xl hover:shadow-rose-500/5 hover:border-rose-200 group">
                <div className="flex flex-col gap-4">
                  <div className="p-2.5 bg-rose-50 rounded-2xl w-fit group-hover:bg-rose-100 transition-all duration-500 group-hover:-rotate-6">
                    <XCircle className="w-6 h-6 text-rose-500" />
                  </div>
                  <div>
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">Pending</p>
                    <p className="text-3xl font-black text-slate-900 tracking-tighter mt-1">{summary.not_submitted_today}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-white/20">
            {/* Employee List Header  */}
            <div className="mb-6">
              <button
                onClick={() => setShowEmployees((s) => !s)}
                className="flex items-center justify-between w-full p-5 bg-white/50 backdrop-blur-sm rounded-3xl transition-all duration-500 group border border-slate-100 hover:border-indigo-200 hover:shadow-xl hover:shadow-indigo-500/5"
                aria-expanded={showEmployees}
                aria-controls="employee-list"
              >
                <div className="flex items-center gap-5">
                  <div className={`p-3 rounded-2xl transition-all duration-500 ${showEmployees ? 'bg-indigo-600 text-white shadow-xl shadow-indigo-100 rotate-6' : 'bg-slate-100 text-slate-500'
                    }`}>
                    <Users className="w-5 h-5" />
                  </div>
                  <div className="text-left">
                    <h3 className="text-base font-black text-slate-900 tracking-tight">Employee Directory</h3>
                    <p className="text-[10px] text-slate-400 font-extrabold uppercase tracking-[0.15em] mt-0.5">
                      {employees.length} Members active
                    </p>
                  </div>
                </div>

                {showEmployees ? (
                  <ChevronDown className="w-5 h-5 text-indigo-400 group-hover:-translate-y-0.5 transition-all duration-500" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-indigo-400 group-hover:translate-x-0.5 transition-all duration-500" />
                )}
              </button>
            </div>

            {showEmployees && (
              <div id="employee-list" className="space-y-3 mt-4 animate-entrance">
                {employees.length === 0 ? (
                  <div className="text-center py-16 bg-white/40 rounded-[2.5rem] border-2 border-dashed border-slate-100">
                    <Users className="w-14 h-14 mx-auto mb-5 text-slate-200" />
                    <p className="text-sm font-black text-slate-400 uppercase tracking-widest">No members found</p>
                  </div>
                ) : (
                  <div className="space-y-2.5">
                    {employees.map((employee) => (
                      <button
                        key={employee.id}
                        onClick={() => {
                          onEmployeeClick(employee);
                          onClose();
                        }}
                        className="w-full text-left p-4 bg-transparent hover:bg-white/80 backdrop-blur-sm rounded-2xl transition-all duration-500 border border-transparent hover:border-indigo-100 group flex items-center gap-5 hover:shadow-xl hover:shadow-indigo-500/5"
                      >
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center text-slate-500 text-base font-black shadow-sm group-hover:from-indigo-600 group-hover:to-purple-600 group-hover:text-white group-hover:rotate-3 transition-all duration-500 group-hover:shadow-lg group-hover:shadow-indigo-200">
                          {employee.name.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-black text-slate-800 text-sm truncate group-hover:text-slate-900 transition-colors">
                            {employee.name}
                          </p>
                          <p className="text-[11px] font-bold text-slate-400 truncate mt-1 group-hover:text-indigo-500 transition-colors opacity-80 uppercase tracking-tight">
                            {employee.email}
                          </p>
                        </div>
                        <div className="w-8 h-8 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500 bg-indigo-50 text-indigo-600 transform translate-x-4 group-hover:translate-x-0 scale-50 group-hover:scale-100">
                          <ChevronRight className="w-4 h-4" />
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="p-8 border-t border-slate-100 bg-white/60 backdrop-blur-md">
            <div className="bg-slate-50 border border-slate-100 rounded-2xl p-4 flex items-center gap-4 transition-all hover:bg-white hover:shadow-lg hover:shadow-slate-200/50 duration-500">
              <div className="relative">
                <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse"></div>
                <div className="absolute inset-0 bg-indigo-400 rounded-full animate-ping opacity-30"></div>
              </div>
              <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.25em]">
                System Online <span className="text-slate-200 mx-3">|</span> v3.5
              </p>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;