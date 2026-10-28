import React from 'react';
import {
  LayoutDashboard,
  FileText,
  FileCheck2,
  Users,
  Receipt,
  CreditCard,
  Scale,
  BarChart3,
  Settings,
  Building2,
  ChevronDown,
  Sparkles,
  LogIn,
  LogOut,
} from 'lucide-react';
import { Business } from '../../types/business';
import { User } from '../../types/auth';

export type NavTab =
  | 'dashboard'
  | 'documents'
  | 'review'
  | 'parties'
  | 'invoices'
  | 'payments'
  | 'ledger'
  | 'reports'
  | 'settings';

interface SidebarProps {
  currentTab: NavTab;
  onSelectTab: (tab: NavTab) => void;
  businesses: Business[];
  activeBusiness: Business | null;
  onSelectBusiness: (biz: Business) => void;
  user: User | null;
  onOpenAuth: () => void;
  onLogout: () => void;
  lang: 'bn' | 'en';
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  businesses,
  activeBusiness,
  onSelectBusiness,
  user,
  onOpenAuth,
  onLogout,
  lang,
}) => {
  const [bizDropdownOpen, setBizDropdownOpen] = React.useState(false);

  const navItems = [
    { id: 'dashboard' as NavTab, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'documents' as NavTab, label: 'Documents', icon: FileText, badge: 'Inbox' },
    { id: 'review' as NavTab, label: 'Review & Verify', icon: FileCheck2, highlight: true },
    { id: 'parties' as NavTab, label: 'Khata / Parties', icon: Users },
    { id: 'invoices' as NavTab, label: 'Invoices', icon: Receipt },
    { id: 'payments' as NavTab, label: 'Payments', icon: CreditCard },
    { id: 'ledger' as NavTab, label: 'General Ledger', icon: Scale },
    { id: 'reports' as NavTab, label: 'Reports', icon: BarChart3 },
    { id: 'settings' as NavTab, label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col flex-shrink-0 min-h-screen border-r border-slate-800">
      {/* Brand & Workspace Switcher */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 font-bold text-lg tracking-wider">
            হ
          </div>
          <div>
            <h1 className="font-bold text-white text-base tracking-tight flex items-center gap-1.5">
              HisabAI
              <span className="text-[10px] bg-blue-500/20 text-blue-400 font-semibold px-1.5 py-0.5 rounded">
                v1
              </span>
            </h1>
            <p className="text-xs text-slate-400">Smart Accounting OS</p>
          </div>
        </div>

        {/* Business Selector */}
        <div className="relative">
          <button
            onClick={() => setBizDropdownOpen(!bizDropdownOpen)}
            className="w-full flex items-center justify-between p-2 rounded-lg bg-slate-800/80 hover:bg-slate-800 border border-slate-700/60 text-xs font-medium text-white transition-colors"
          >
            <div className="flex items-center gap-2 truncate">
              <Building2 className="w-4 h-4 text-blue-400 flex-shrink-0" />
              <span className="truncate">{activeBusiness?.name || 'Select Business'}</span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {bizDropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-1.5 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-30 py-1 max-h-48 overflow-y-auto">
              {businesses.length === 0 ? (
                <div className="p-2 text-xs text-slate-400 text-center">No businesses found</div>
              ) : (
                businesses.map((b) => (
                  <button
                    key={b.id}
                    onClick={() => {
                      onSelectBusiness(b);
                      setBizDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-700/60 transition-colors ${
                      activeBusiness?.id === b.id ? 'bg-blue-600/20 text-blue-400 font-medium' : 'text-slate-300'
                    }`}
                  >
                    <span className="truncate">{b.name}</span>
                    <span className="text-[10px] text-slate-400 uppercase font-mono">{b.currency}</span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : item.highlight ? 'text-blue-400' : 'text-slate-400'}`} />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge && (
                <span className="text-[10px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded font-medium border border-slate-700">
                  {item.badge}
                </span>
              )}
              {item.highlight && !isActive && (
                <Sparkles className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
              )}
            </button>
          );
        })}
      </nav>

      {/* User Card / Auth Actions */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/40">
        {user ? (
          <div className="flex items-center justify-between p-2 rounded-lg bg-slate-800/40">
            <div className="flex items-center gap-2.5 truncate">
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white flex items-center justify-center font-bold text-xs uppercase shadow flex-shrink-0">
                {user.full_name ? user.full_name.charAt(0) : 'U'}
              </div>
              <div className="truncate">
                <p className="text-xs font-semibold text-white truncate">{user.full_name}</p>
                <p className="text-[10px] text-slate-400 truncate">{user.email}</p>
              </div>
            </div>
            <button
              onClick={onLogout}
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded transition-colors ml-1 flex-shrink-0"
              title={lang === 'bn' ? 'লগআউট' : 'Sign Out'}
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-md shadow-blue-600/20 transition-all"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>{lang === 'bn' ? 'লগইন / সাইন আপ' : 'Sign In / Register'}</span>
          </button>
        )}
      </div>
    </aside>
  );
};
