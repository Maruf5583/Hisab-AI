import React, { useState } from 'react';
import {
  BarChart3,
  Download,
} from 'lucide-react';
import { Button } from '../components/ui/Button';

interface ReportsPageProps {
  businessId?: string;
  lang: 'bn' | 'en';
}

export const ReportsPage: React.FC<ReportsPageProps> = ({ lang }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('apr_2026');

  const formatBDT = (amount: number) => {
    return `৳ ${amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
            <BarChart3 className="w-6 h-6 text-blue-600" />
            <span>{lang === 'bn' ? 'আর্থিক প্রতিবেদন ও রিপোর্ট (Financial Reports)' : 'Financial Reports'}</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {lang === 'bn'
              ? 'ব্যবসায়িক সিদ্ধান্ত গ্রহণে সাহায্যকারী দেনা-পাওনা বিবরণী ও ক্যাশফ্লো রিপোর্ট'
              : 'Actionable accounting reports, aged receivables, payables, and VAT statements'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-semibold text-slate-700 shadow-sm focus:outline-none"
          >
            <option value="apr_2026">April 2026 (Current Period)</option>
            <option value="q1_2026">Q1 2026 (Jan - Mar)</option>
            <option value="fy_2025_26">Fiscal Year 2025-26</option>
          </select>

          <Button variant="outline" size="sm" onClick={() => alert('Downloading PDF Financial Statement...')}>
            <Download className="w-4 h-4 mr-1.5" />
            <span>Download PDF</span>
          </Button>
        </div>
      </div>

      {/* Quick Financial Snapshot */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Gross Revenue</p>
          <p className="text-xl font-bold text-slate-900 mt-1">{formatBDT(230000)}</p>
          <p className="text-[10px] text-emerald-600 mt-0.5">+18.4% vs last period</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Total Procurement</p>
          <p className="text-xl font-bold text-slate-900 mt-1">{formatBDT(154123)}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Purchases & expenses</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Total Outstanding Due</p>
          <p className="text-xl font-bold text-rose-600 mt-1">{formatBDT(7076273)}</p>
          <p className="text-[10px] text-rose-500 mt-0.5">Customer receivables pending</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Net Output VAT</p>
          <p className="text-xl font-bold text-purple-700 mt-1">{formatBDT(16000)}</p>
          <p className="text-[10px] text-purple-600 mt-0.5">Calculated at standard rate</p>
        </div>
      </div>

      {/* Aged Receivables & Payables Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Receivables Aging */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Aged Receivables Schedule (দেনা বিবরণী)</h3>
              <p className="text-xs text-slate-500">Breakdown of pending customer dues by age</p>
            </div>
            <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              {formatBDT(7076273)} Total
            </span>
          </div>

          <div className="mt-4 space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-600 font-medium">Current (0 - 15 days)</span>
                <span className="font-bold text-slate-900">{formatBDT(210000)}</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-emerald-500 h-full w-[25%] rounded-full"></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-600 font-medium">16 - 30 days overdue</span>
                <span className="font-bold text-slate-900">{formatBDT(45000)}</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-blue-500 h-full w-[10%] rounded-full"></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-600 font-medium">31 - 60 days overdue</span>
                <span className="font-bold text-slate-900">{formatBDT(0)}</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-amber-500 h-full w-[0%] rounded-full"></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-600 font-medium">60+ days overdue (Historic)</span>
                <span className="font-bold text-rose-600">{formatBDT(6821273)}</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-rose-500 h-full w-[65%] rounded-full"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Payables Aging */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 className="font-bold text-slate-900 text-sm">Aged Payables Schedule (পাওনা বিবরণী)</h3>
              <p className="text-xs text-slate-500">Vendor liabilities organized by payment due dates</p>
            </div>
            <span className="text-xs font-bold text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200">
              {formatBDT(102396)} Total
            </span>
          </div>

          <div className="mt-4 space-y-3">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-600 font-medium">Current (Due within 15 days)</span>
                <span className="font-bold text-slate-900">{formatBDT(64000)}</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-blue-500 h-full w-[60%] rounded-full"></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-600 font-medium">16 - 30 days</span>
                <span className="font-bold text-slate-900">{formatBDT(26123)}</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-amber-500 h-full w-[25%] rounded-full"></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-600 font-medium">31 - 60 days</span>
                <span className="font-bold text-slate-900">{formatBDT(12273)}</span>
              </div>
              <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                <div className="bg-rose-500 h-full w-[15%] rounded-full"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
