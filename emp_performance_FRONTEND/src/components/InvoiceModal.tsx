import React, { useState, useEffect } from 'react';
import { X, Download, FileText, Loader2, Calendar, AlertTriangle, CheckCircle2, ChevronRight, Users, Briefcase, Sparkles } from 'lucide-react';
import { MonthlyInvoice, InvoicePeriod } from '../types';

interface InvoiceModalProps {
    isOpen: boolean;
    onClose: () => void;
    apiBaseUrl: string;
}

const InvoiceModal: React.FC<InvoiceModalProps> = ({ isOpen, onClose, apiBaseUrl }) => {
    const [periods, setPeriods] = useState<InvoicePeriod[]>([]);
    const [selectedPeriod, setSelectedPeriod] = useState<string>('');
    const [invoice, setInvoice] = useState<MonthlyInvoice | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isExporting, setIsExporting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            fetchPeriods();
        }
    }, [isOpen]);

    const fetchPeriods = async () => {
        try {
            const response = await fetch(`${apiBaseUrl}/api/lyell/invoice/list`);
            const data = await response.json();
            if (data.success) {
                setPeriods(data.periods);
                if (data.periods.length > 0) {
                    const first = data.periods[0];
                    setSelectedPeriod(`${first.year}-${first.month}`);
                }
            }
        } catch (err) {
            console.error('Error fetching periods:', err);
            setError('Failed to load invoice periods');
        }
    };

    const generateInvoice = async () => {
        if (!selectedPeriod) return;

        setIsLoading(true);
        setError(null);
        setInvoice(null);

        const [year, month] = selectedPeriod.split('-');

        try {
            const response = await fetch(`${apiBaseUrl}/api/lyell/invoice/monthly/${year}/${month}`);
            const data = await response.json();

            if (data.success) {
                setInvoice(data.invoice);
            } else {
                setError(data.error || 'Failed to generate invoice');
            }
        } catch (err) {
            console.error('Error generating invoice:', err);
            setError('Connection error. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const exportPdf = async () => {
        if (!invoice) return;

        setIsExporting(true);
        try {
            const { year, month } = invoice;
            const downloadUrl = `${apiBaseUrl}/api/lyell/invoice/monthly/${year}/${month}/pdf`;

            // Use a hidden anchor tag to trigger download
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', `Lyell_Invoice_${year}-${month}.pdf`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (err) {
            console.error('Error exporting PDF:', err);
            alert('Failed to export PDF');
        } finally {
            setIsExporting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/60 backdrop-blur-xl animate-entrance">
            <div className="bg-white/95 backdrop-blur-3xl rounded-[3.5rem] shadow-[0_40px_100px_-20px_rgba(0,0,0,0.25)] w-full max-w-6xl max-h-[92vh] flex flex-col overflow-hidden border border-white relative group/modal overflow-hidden">
                {/* Background Blobs for depth */}
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-500/5 blur-[120px] rounded-full -mr-64 -mt-64 animate-pulse"></div>
                <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-emerald-500/5 blur-[100px] rounded-full -ml-48 -mb-48"></div>

                {/* Header */}
                <div className="px-12 py-10 border-b border-slate-100/60 flex items-center justify-between relative z-10 bg-white/40 backdrop-blur-md">
                    <div className="flex items-center gap-8">
                        <div className="p-5 bg-gradient-to-br from-indigo-600 to-indigo-700 text-white rounded-[2.5rem] shadow-2xl shadow-indigo-200 transition-all hover:scale-110 hover:rotate-3">
                            <FileText className="w-10 h-10" />
                        </div>
                        <div>
                            <div className="flex items-center gap-3">
                                <h2 className="text-4xl font-black text-slate-900 tracking-tighter">Enterprise <span className="text-indigo-600">Invoicing</span></h2>
                            </div>

                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-4 bg-slate-50 hover:bg-rose-50 rounded-3xl transition-all duration-500 text-slate-300 hover:text-rose-500 active:scale-90 group border border-slate-100 hover:border-rose-100"
                    >
                        <X className="w-8 h-8 group-hover:rotate-90 transition-transform duration-700" />
                    </button>
                </div>

                {/* Controls */}
                <div className="px-12 py-8 bg-white/30 border-b border-slate-100/60 flex flex-wrap items-center gap-10 relative z-10">
                    <div className="flex flex-col gap-3 min-w-[280px]">
                        <label className="text-[11px] font-black text-slate-400 uppercase tracking-[0.25em] pl-1">Billing Sequence</label>
                        <div className="relative group">
                            <Calendar className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-indigo-400 group-focus-within:text-indigo-600 transition-colors pointer-events-none z-10" />
                            <select
                                value={selectedPeriod}
                                onChange={(e) => setSelectedPeriod(e.target.value)}
                                className="w-full pl-14 pr-8 py-4.5 bg-slate-50 border border-slate-100 rounded-3xl text-[15px] font-black text-slate-800 focus:ring-8 focus:ring-indigo-500/5 focus:border-indigo-300 focus:bg-white outline-none transition-all cursor-pointer appearance-none shadow-sm hover:shadow-md"
                            >
                                <option value="" disabled>Select Reporting Window</option>
                                {periods.map((p) => (
                                    <option key={`${p.year}-${p.month}`} value={`${p.year}-${p.month}`}>
                                        {p.period.toUpperCase()}
                                    </option>
                                ))}
                            </select>
                            <div className="absolute right-5 top-1/2 -translate-y-1/2 pointer-events-none text-indigo-300 group-hover:text-indigo-500 transition-colors">
                                <ChevronRight className="w-5 h-5 rotate-90" />
                            </div>
                        </div>
                    </div>

                    <div className="flex items-end gap-6 mt-auto ml-auto">
                        <button
                            onClick={generateInvoice}
                            disabled={!selectedPeriod || isLoading}
                            className="px-12 py-4.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white rounded-3xl text-[15px] font-black shadow-2xl shadow-indigo-600/30 transition-all flex items-center gap-4 hover:-translate-y-1.5 hover:shadow-indigo-600/50 active:translate-y-0 active:scale-95 group/btn relative overflow-hidden btn-premium shimmer-effect"
                        >
                            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5 animate-pulse" />}
                            <span className="relative z-10">Execute Performance Audit</span>
                        </button>

                        {invoice && (
                            <button
                                onClick={exportPdf}
                                disabled={isExporting}
                                className="px-10 py-4.5 bg-white border border-slate-200 hover:border-indigo-400 text-slate-700 hover:text-indigo-600 rounded-3xl text-[15px] font-black transition-all flex items-center gap-4 shadow-sm hover:shadow-xl hover:shadow-indigo-500/10 active:scale-95 group/down"
                            >
                                {isExporting ? <Loader2 className="w-5 h-5 animate-spin text-indigo-600" /> : <Download className="w-5 h-5 group-hover/down:translate-y-1 transition-transform duration-500" />}
                                Export Invoice
                            </button>
                        )}
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-12 bg-slate-50/10 custom-scrollbar relative z-10">
                    {isLoading ? (
                        <div className="h-full flex flex-col items-center justify-center gap-10 animate-entrance">
                            <div className="relative">
                                <div className="absolute inset-0 bg-indigo-500 blur-[100px] opacity-10 animate-pulse"></div>
                                <div className="p-12 bg-white rounded-[3.5rem] shadow-2xl relative border border-slate-50">
                                    <div className="relative">
                                        <Loader2 className="w-20 h-20 animate-spin text-indigo-600" />
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <div className="w-3 h-3 bg-indigo-200 rounded-full animate-ping"></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="text-center space-y-4">
                                <p className="text-2xl font-black text-slate-900 tracking-tight">Synthesizing Ledger Intelligence</p>
                                <p className="text-sm font-extrabold text-slate-400 uppercase tracking-[0.3em] max-w-md mx-auto leading-relaxed opacity-60">
                                    Mapping activity streams • Calculating variance ratios • Validating SOW compliance matrix
                                </p>
                            </div>
                        </div>
                    ) : error ? (
                        <div className="h-full flex flex-col items-center justify-center gap-8 animate-entrance">
                            <div className="p-8 bg-rose-50 rounded-[3rem] border border-rose-100 shadow-xl shadow-rose-500/5">
                                <AlertTriangle className="w-20 h-20 text-rose-500 animate-bounce" />
                            </div>
                            <div className="text-center space-y-3">
                                <p className="text-3xl font-black text-rose-600 tracking-tight">{error}</p>
                                <p className="text-sm font-extrabold text-slate-400 uppercase tracking-widest">Protocol interrupted • Validate parameters and retry sequence</p>
                            </div>
                        </div>
                    ) : invoice ? (
                        <div className="space-y-16 animate-entrance">
                            {/* Summary Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                                <SummaryCard
                                    title="Ledger Trace ID"
                                    value={invoice.invoice_number}
                                    icon={<FileText className="w-6 h-6" />}
                                    color="slate"
                                />
                                <SummaryCard
                                    title="Aggregate Hours"
                                    value={`${invoice.total_hours.toFixed(1)}h`}
                                    icon={<Briefcase className="w-6 h-6" />}
                                    color="indigo"
                                />
                                <SummaryCard
                                    title="Certified Billable"
                                    value={`${invoice.total_billable_hours.toFixed(1)}h`}
                                    icon={<CheckCircle2 className="w-6 h-6" />}
                                    color="emerald"
                                />
                                <SummaryCard
                                    title="Budget Variance"
                                    value={`${invoice.total_extra_hours.toFixed(1)}h`}
                                    icon={<AlertTriangle className="w-6 h-6" />}
                                    color={invoice.has_sow_violations ? "rose" : "emerald"}
                                    subtitle={invoice.has_sow_violations ? "Compliance Alert: Overage" : "Positive SOW Delta"}
                                />
                            </div>

                            {/* Status Banner */}
                            <div className={`p-10 rounded-[3rem] flex items-center gap-8 border transition-all relative overflow-hidden group/audit ${invoice.has_sow_violations
                                ? 'bg-white border-rose-200 shadow-2xl shadow-rose-500/10'
                                : 'bg-white border-emerald-200 shadow-2xl shadow-emerald-500/10'}`}>

                                <div className={`absolute top-0 right-0 w-64 h-full opacity-5 ${invoice.has_sow_violations ? 'bg-rose-500' : 'bg-emerald-500'} blur-3xl`}></div>

                                <div className={`p-5 rounded-[2rem] relative z-10 transition-transform group-hover/audit:scale-110 duration-700 ${invoice.has_sow_violations ? 'bg-rose-50 text-rose-600' : 'bg-emerald-50 text-emerald-600'}`}>
                                    {invoice.has_sow_violations ? <AlertTriangle className="w-8 h-8" /> : <CheckCircle2 className="w-8 h-8" />}
                                </div>
                                <div className="relative z-10">
                                    <h4 className="text-lg font-black text-slate-900 tracking-tight uppercase">System Compliance Certification</h4>
                                    <p className="text-[15px] font-bold text-slate-500 mt-1 max-w-3xl leading-relaxed">
                                        {invoice.has_sow_violations
                                            ? `Critical Alert: Performance data for this period indicates a variance of ${invoice.total_extra_hours.toFixed(2)} hours exceeding the agreed SOW framework. Internal audit required before client submission.`
                                            : 'Ledger Verified: All work  categories successfully passed the automated SOW compliance validation logic.'}
                                    </p>
                                </div>
                            </div>

                            {/* Tables Container */}
                            <div className="space-y-16 pb-10">
                                {/* Category Summary */}
                                <section className="bg-white rounded-[3.5rem] border border-slate-100 overflow-hidden shadow-2xl shadow-slate-200/50">
                                    <div className="px-10 py-8 bg-slate-50/40 border-b border-slate-100/60 flex items-center justify-between">
                                        <div className="flex items-center gap-5">
                                            <div className="p-3 bg-white rounded-2xl shadow-sm border border-slate-100">
                                                <Briefcase className="w-5 h-5 text-indigo-600" />
                                            </div>
                                            <h3 className="font-black text-xs uppercase tracking-[0.3em] text-slate-400">Resource Allocation Matrix</h3>
                                        </div>
                                    </div>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left">
                                            <thead>
                                                <tr className="text-slate-400 text-[11px] uppercase font-black tracking-[0.2em] border-b border-slate-100/60">
                                                    <th className="px-10 py-6">Labor Category Index</th>
                                                    <th className="px-10 py-6 text-center">Gross Utilization</th>
                                                    <th className="px-10 py-6 text-center text-indigo-600">SOW Billable</th>
                                                    <th className="px-10 py-6 text-center">Variance Delta</th>
                                                    <th className="px-10 py-6 text-center">Compliance Cap</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-50/50">
                                                {invoice.category_breakdown.map((cat, idx) => (
                                                    <tr key={idx} className="hover:bg-indigo-50/10 transition-all duration-500 group">
                                                        <td className="px-10 py-7">
                                                            <div className="flex items-center gap-4">
                                                                <div className="w-2 h-8 bg-indigo-100 rounded-full group-hover:bg-indigo-500 transition-colors"></div>
                                                                <span className="font-black text-slate-800 text-base tracking-tight capitalize">{cat.category_label}</span>
                                                            </div>
                                                        </td>
                                                        <td className="px-10 py-7 text-center font-black text-slate-500 text-[14px]">{cat.total_hours.toFixed(2)}h</td>
                                                        <td className="px-10 py-7 text-center">
                                                            <span className="px-5 py-2 bg-indigo-50 text-indigo-700 rounded-2xl font-black text-[13px] border border-indigo-100 shadow-sm">{cat.billable_hours.toFixed(2)}h</span>
                                                        </td>
                                                        <td className="px-10 py-7 text-center">
                                                            <span className={`font-black text-base ${cat.extra_hours > 0 ? 'text-rose-500' : 'text-slate-200'}`}>
                                                                {cat.extra_hours > 0 ? `+${cat.extra_hours.toFixed(2)}` : '0.00'}
                                                            </span>
                                                        </td>
                                                        <td className="px-10 py-7 text-center">
                                                            <span className={`px-5 py-2.5 rounded-2xl text-[10px] font-black uppercase tracking-widest ${cat.has_cap ? 'bg-amber-50 text-amber-600 border border-amber-100' : 'bg-slate-50 text-slate-400 border border-slate-100'}`}>
                                                                {cat.cap_value}
                                                            </span>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </section>

                                {/* Employee Contributions */}
                                <section className="bg-white rounded-[3.5rem] border border-slate-100 overflow-hidden shadow-2xl shadow-slate-200/50">
                                    <div className="px-10 py-8 bg-slate-50/40 border-b border-slate-100/60 flex items-center justify-between">
                                        <div className="flex items-center gap-5">
                                            <div className="p-3 bg-white rounded-2xl shadow-sm border border-slate-100">
                                                <Users className="w-5 h-5 text-indigo-600" />
                                            </div>
                                            <h3 className="font-black text-xs uppercase tracking-[0.3em] text-slate-400"> Performance Audit</h3>
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <span className="text-[11px] font-black uppercase tracking-widest text-indigo-500 bg-indigo-50 px-4 py-2 rounded-xl border border-indigo-100">{invoice.employee_breakdown.length} Records Analyzed</span>
                                        </div>
                                    </div>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-left">
                                            <thead>
                                                <tr className="text-slate-400 text-[11px] uppercase font-black tracking-[0.2em] border-b border-slate-100/60">
                                                    <th className="px-10 py-6">Employee Name</th>
                                                    <th className="px-10 py-6 text-center">Work Category</th>
                                                    <th className="px-10 py-6 text-center">Gross Sum</th>
                                                    <th className="px-10 py-6 text-center text-emerald-600">Net Billable</th>
                                                    <th className="px-10 py-6 text-center">Variance Delta</th>
                                                    <th className="px-10 py-6 text-center">Yield Analysis</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-50/50">
                                                {invoice.employee_breakdown.map((emp, idx) => (
                                                    <tr key={idx} className="hover:bg-slate-50/50 transition-all duration-500 group">
                                                        <td className="px-10 py-7">
                                                            <div className="flex flex-col">
                                                                <span className="font-black text-slate-900 group-hover:text-indigo-600 transition-colors text-[16px] tracking-tight">{emp.employee_name}</span>
                                                                <span className="text-[11px] text-slate-400 font-bold tracking-widest uppercase mt-0.5 opacity-60 group-hover:opacity-100 transition-opacity">{emp.employee_email}</span>
                                                            </div>
                                                        </td>
                                                        <td className="px-10 py-7 text-center">
                                                            <span className="px-4 py-1.5 bg-slate-50 text-slate-600 rounded-xl font-black text-sm border border-slate-100">{emp.days_worked}d</span>
                                                        </td>
                                                        <td className="px-10 py-7 text-center font-black text-slate-500 text-sm">{emp.total_hours.toFixed(1)}h</td>
                                                        <td className="px-10 py-7 text-center">
                                                            <span className="font-black text-emerald-600 text-base">{emp.billable_hours.toFixed(1)}h</span>
                                                        </td>
                                                        <td className="px-10 py-7 text-center">
                                                            <span className={`font-black text-sm ${emp.extra_hours > 0 ? 'text-rose-500' : 'text-slate-100'}`}>
                                                                {emp.extra_hours > 0 ? `+${emp.extra_hours.toFixed(1)}h` : '0.0h'}
                                                            </span>
                                                        </td>
                                                        <td className="px-10 py-7 text-center">
                                                            <div className="flex flex-col items-center gap-2 justify-center">
                                                                <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-100 shadow-inner p-0.5">
                                                                    <div
                                                                        className={`h-full rounded-full transition-all duration-1000 ${emp.billing_efficiency >= 95 ? 'bg-emerald-500' : emp.billing_efficiency >= 80 ? 'bg-amber-500' : 'bg-rose-500'}`}
                                                                        style={{ width: `${emp.billing_efficiency}%` }}
                                                                    ></div>
                                                                </div>
                                                                <span className={`text-[12px] font-black ${emp.billing_efficiency >= 95 ? 'text-emerald-600' : 'text-slate-700'}`}>
                                                                    {emp.billing_efficiency.toFixed(0)}%
                                                                </span>
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </section>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center gap-14 animate-entrance">
                            <div className="relative group cursor-pointer" onClick={fetchPeriods}>
                                <div className="absolute inset-0 bg-indigo-500 blur-[120px] opacity-10 group-hover:opacity-20 transition-all rounded-full animate-pulse"></div>
                                <div className="relative p-16 bg-white rounded-[4rem] shadow-2xl border border-slate-50 transform group-hover:scale-105 transition-all duration-700 hover:rotate-2">
                                    <div className="p-10 bg-slate-50 rounded-[3rem] text-slate-200 group-hover:bg-indigo-50 transition-colors duration-700">
                                        <FileText className="w-32 h-32 group-hover:text-indigo-200 transition-colors" />
                                    </div>
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <div className="w-16 h-16 bg-indigo-600 rounded-[2rem] rotate-45 flex items-center justify-center shadow-2xl shadow-indigo-300 group-hover:rotate-[225deg] transition-all duration-1000">
                                            <ChevronRight className="w-8 h-8 text-white -rotate-45 group-hover:scale-125" />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

interface SummaryCardProps {
    title: string;
    value: string;
    icon: React.ReactNode;
    color: 'indigo' | 'emerald' | 'rose' | 'slate';
    subtitle?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ title, value, icon, color, subtitle }) => {
    const variants = {
        indigo: 'bg-white border-indigo-100/80 text-indigo-600 shadow-indigo-500/5',
        emerald: 'bg-white border-emerald-100/80 text-emerald-600 shadow-emerald-500/5',
        rose: 'bg-white border-rose-100/80 text-rose-600 shadow-rose-500/5',
        slate: 'bg-white border-slate-100/80 text-slate-800 shadow-slate-500/5',
    };

    const iconBg = {
        indigo: 'bg-indigo-50',
        emerald: 'bg-emerald-50',
        rose: 'bg-rose-50',
        slate: 'bg-slate-50',
    };

    return (
        <div className={`p-10 rounded-[3rem] border shadow-xl transition-all duration-700 group cursor-default hover:shadow-2xl hover:-translate-y-2 relative overflow-hidden ${variants[color]}`}>
            <div className={`absolute top-0 right-0 w-24 h-24 blur-3xl opacity-10 transition-opacity group-hover:opacity-30 ${iconBg[color].replace('bg-', 'bg-')}`}></div>

            <div className="flex items-center justify-between mb-8 relative z-10">
                <span className="text-[11px] font-black uppercase tracking-[0.3em] text-slate-400 group-hover:text-indigo-600 transition-colors uppercase">{title}</span>
                <div className={`p-3 rounded-2xl transition-all duration-700 group-hover:scale-110 group-hover:rotate-12 border border-transparent group-hover:border-current/20 ${iconBg[color]} text-slate-400 group-hover:text-current`}>
                    {icon}
                </div>
            </div>
            <div className="text-4xl font-black tracking-tighter text-slate-900 group-hover:text-indigo-600 transition-colors relative z-10">{value}</div>
            {subtitle && (
                <div className="mt-5 flex items-center gap-3 relative z-10">
                    <div className="h-1 w-6 bg-current/20 rounded-full group-hover:w-10 transition-all duration-700"></div>
                    <span className="text-[10px] font-black uppercase tracking-[0.2em] opacity-60 italic group-hover:opacity-100 transition-opacity">{subtitle}</span>
                </div>
            )}
        </div>
    );
};

export default InvoiceModal;
