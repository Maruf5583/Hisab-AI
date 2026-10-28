import React from 'react';
import { Calendar, Globe2 } from 'lucide-react';

interface HeaderProps {
  title: string;
  subtitle?: string;
  lang: 'bn' | 'en';
  onToggleLang: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  title,
  subtitle,
  lang,
  onToggleLang,
}) => {
  return (
    <header className="h-16 bg-white border-b border-slate-200/80 px-6 flex items-center justify-between flex-shrink-0">
      <div>
        <h2 className="text-xl font-bold text-slate-800 tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {/* Backend Connected Pill */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span>FastAPI v1 Live</span>
        </div>

        {/* Date Filter Pill matching Reference Image 1 */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 transition-colors cursor-pointer">
          <Calendar className="w-3.5 h-3.5 text-slate-500" />
          <span>2026-04-01</span>
          <span className="text-slate-400">—</span>
          <span>2026-10-31</span>
        </div>

        {/* Language Switcher */}
        <button
          onClick={onToggleLang}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-xs font-medium text-slate-700 transition-colors shadow-sm"
          title="Toggle Language (বাংলা / English)"
        >
          <Globe2 className="w-3.5 h-3.5 text-blue-600" />
          <span>{lang === 'bn' ? 'বাংলা' : 'EN'}</span>
        </button>
      </div>
    </header>
  );
};
