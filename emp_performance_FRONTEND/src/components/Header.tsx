// src/components/Header.tsx
import { Menu, FileText } from 'lucide-react';

interface HeaderProps {
  onMenuClick: () => void;
  onInvoiceClick: () => void;
}

function Header({ onMenuClick, onInvoiceClick }: HeaderProps) {
  return (
    <header className="glass-card px-8 py-5 flex items-center justify-between sticky top-0 z-30 animate-entrance premium-shadow">
      <div className="flex items-center gap-6">
        <button
          onClick={onMenuClick}
          className="p-3 bg-slate-50/50 hover:bg-white rounded-2xl transition-all duration-300 text-slate-600 hover:text-indigo-600 group border border-slate-100 hover:border-indigo-100 hover:shadow-lg hover:shadow-indigo-500/5"
        >
          <Menu className="w-6 h-6 group-hover:scale-110 transition-all duration-500" />
        </button>
        |
        <div className="flex items-center gap-4">
          <div className="p-2 bg-gradient-to-br from-indigo-50 to-white rounded-2xl border border-indigo-100 shadow-sm transition-transform hover:scale-105 duration-500">
            <img
              src="Favicon Blue.png"
              alt="Dataplatr Logo"
              className="h-9 w-9 object-contain"
            />
          </div>

          <div>
            <h1 className="text-xl font-black text-slate-900 leading-none tracking-tight">
              Dataplatr <span className="text-indigo-600">Analytics</span>
            </h1>
            <p className="text-[10px] text-slate-400 font-extrabold uppercase tracking-[0.2em] mt-1.5 opacity-80">
              Employee Performance Dashboard
            </p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-5">
        <button
          onClick={onInvoiceClick}
          className="btn-premium shimmer-effect flex items-center gap-2.5 px-6 py-3 bg-indigo-600 text-white hover:bg-indigo-700 rounded-2xl shadow-xl shadow-indigo-600/20 hover:shadow-indigo-600/40 transition-all duration-500 font-black text-sm group"
          title="Generate Monthly Invoice"
        >
          <div className="p-1 bg-white/20 rounded-lg group-hover:bg-white/30 transition-colors">
            <FileText className="w-4 h-4 group-hover:rotate-12 transition-transform duration-500" />
          </div>
          <span>Generate Invoice</span>
        </button>
      </div>
    </header>
  );
}

export default Header;