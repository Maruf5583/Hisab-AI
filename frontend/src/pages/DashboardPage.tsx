import React from 'react';
import { Card } from '../components/ui/Card';
import { ArrowUpRight, ArrowDownLeft, Wallet, TrendingUp, UploadCloud, FileCheck2 } from 'lucide-react';
import { Button } from '../components/ui/Button';

interface DashboardPageProps {
  onNavigateToUpload: () => void;
  onNavigateToReview: () => void;
  lang: 'bn' | 'en';
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onNavigateToUpload,
  onNavigateToReview,
  lang,
}) => {
  const t = {
    title: lang === 'bn' ? 'ড্যাশবোর্ড' : 'Dashboard',
    subtitle: lang === 'bn' ? 'স্বাগতম, আপনার নির্বাচিত সময়কালের আর্থিক বিবরণী নিচে দেওয়া হলো।' : "Welcome back, here's your financial overview for your time period.",
    totalReceivables: lang === 'bn' ? 'মোট দেনা (Receivables)' : 'Total Receivables',
    totalPayables: lang === 'bn' ? 'মোট পাওনা (Payables)' : 'Total Payables',
    bankBalance: lang === 'bn' ? 'ক্যাশ ও ব্যাংক ব্যালেন্স' : 'Bank Balance',
    netProfit: lang === 'bn' ? 'নেট ব্যালেন্স' : 'Net Position',
    periodText: lang === 'bn' ? 'নির্বাচিত সময়কালের জন্য' : 'For the selected period',
    endDateText: lang === 'bn' ? 'সমাপ্তির তারিখ অনুযায়ী' : 'As of the end date',
    cashFlow: lang === 'bn' ? 'ক্যাশ ফ্লো (Cash Flow)' : 'Cash Flow',
    invoicesOverview: lang === 'bn' ? 'ইনভয়েস বিবরণী' : 'Invoices Overview',
    incoming: lang === 'bn' ? 'ইনকামিং' : 'Incoming',
    outgoing: lang === 'bn' ? 'আউটগোয়িং' : 'Outgoing',
    net: lang === 'bn' ? 'নেট লাভ' : 'Net',
    paid: lang === 'bn' ? 'পরিশোধিত' : 'Paid',
    overdue: lang === 'bn' ? 'বকেয়া' : 'Overdue',
    pending: lang === 'bn' ? 'পর্যালোচনাধীন' : 'Pending',
    uploadDoc: lang === 'bn' ? 'ডকুমেন্ট আপলোড' : 'Upload Document',
    reviewDoc: lang === 'bn' ? 'রিভিউ করুন' : 'Review & Verify',
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{t.title}</h1>
          <p className="text-sm text-slate-500 mt-0.5">{t.subtitle}</p>
        </div>
        <div className="flex items-center gap-2.5">
          <Button variant="secondary" onClick={onNavigateToReview} className="text-xs">
            <FileCheck2 className="w-3.5 h-3.5 text-blue-600" />
            {t.reviewDoc}
          </Button>
          <Button variant="primary" onClick={onNavigateToUpload} className="text-xs">
            <UploadCloud className="w-3.5 h-3.5" />
            {t.uploadDoc}
          </Button>
        </div>
      </div>

      {/* 4 KPI Cards matching Reference Image 1 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Receivables (Green accent) */}
        <Card accent="green" className="p-5">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
            <span>{t.totalReceivables}</span>
            <span className="p-1.5 rounded-full bg-emerald-50 text-emerald-600">
              <ArrowDownLeft className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-extrabold text-slate-900 font-mono tracking-tight">৳ 51,300.00</span>
          </div>
          <p className="mt-2 text-[11px] font-medium text-emerald-600 flex items-center gap-1">
            <span>↑ 12%</span>
            <span className="text-slate-400 font-normal">{t.periodText}</span>
          </p>
        </Card>

        {/* Total Payables (Red accent) */}
        <Card accent="red" className="p-5">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
            <span>{t.totalPayables}</span>
            <span className="p-1.5 rounded-full bg-rose-50 text-rose-600">
              <ArrowUpRight className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-extrabold text-slate-900 font-mono tracking-tight">৳ 0.00</span>
          </div>
          <p className="mt-2 text-[11px] font-medium text-slate-400">
            {t.periodText}
          </p>
        </Card>

        {/* Bank Balance (Amber accent) */}
        <Card accent="amber" className="p-5">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
            <span>{t.bankBalance}</span>
            <span className="p-1.5 rounded-full bg-amber-50 text-amber-600">
              <Wallet className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-extrabold text-slate-900 font-mono tracking-tight">৳ 51,300.00</span>
          </div>
          <p className="mt-2 text-[11px] font-medium text-slate-400">
            {t.endDateText}
          </p>
        </Card>

        {/* Net Profit (Blue accent) */}
        <Card accent="blue" className="p-5">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-600">
            <span>{t.netProfit}</span>
            <span className="p-1.5 rounded-full bg-blue-50 text-blue-600">
              <TrendingUp className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3">
            <span className="text-2xl font-extrabold text-blue-600 font-mono tracking-tight">৳ 51,300.00</span>
          </div>
          <p className="mt-2 text-[11px] font-medium text-slate-400">
            {t.periodText}
          </p>
        </Card>
      </div>

      {/* Main Charts Row matching Reference Image 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cash Flow Chart (Left 2 cols) */}
        <Card className="lg:col-span-2 p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-base font-bold text-slate-900">{t.cashFlow}</h3>
              <p className="text-xs text-slate-400">Monthly breakdown of inflows and disbursements</p>
            </div>
            <div className="flex items-center gap-4 text-xs font-medium">
              <span className="flex items-center gap-1.5 text-slate-600">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> {t.incoming}
              </span>
              <span className="flex items-center gap-1.5 text-slate-600">
                <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span> {t.outgoing}
              </span>
              <span className="flex items-center gap-1.5 text-slate-600">
                <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span> {t.net}
              </span>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-6">
            {/* Simulated Chart Bars */}
            <div className="flex-1 w-full h-56 flex items-end justify-between gap-3 pt-6 pb-2 border-b border-slate-100">
              {[
                { month: 'Apr', inc: 35, out: 10 },
                { month: 'May', inc: 42, out: 15 },
                { month: 'Jun', inc: 28, out: 12 },
                { month: 'Jul', inc: 55, out: 20 },
                { month: 'Aug', inc: 60, out: 25 },
                { month: 'Sep', inc: 72, out: 30 },
                { month: 'Oct', inc: 88, out: 18 },
              ].map((bar, i) => (
                <div key={i} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                  <div className="w-full flex items-end justify-center gap-1 h-full">
                    <div
                      style={{ height: `${bar.inc}%` }}
                      className="w-3 sm:w-4 bg-emerald-500 rounded-t transition-all hover:bg-emerald-600"
                      title={`Incoming: ৳ ${bar.inc * 1000}`}
                    ></div>
                    <div
                      style={{ height: `${bar.out}%` }}
                      className="w-3 sm:w-4 bg-indigo-500 rounded-t transition-all hover:bg-indigo-600"
                      title={`Outgoing: ৳ ${bar.out * 1000}`}
                    ></div>
                  </div>
                  <span className="text-[11px] text-slate-400 font-medium">{bar.month}</span>
                </div>
              ))}
            </div>

            {/* Right Summary Side */}
            <div className="w-full sm:w-48 bg-slate-50 p-4 rounded-xl border border-slate-100 flex flex-col justify-between gap-3 text-xs">
              <div>
                <span className="text-slate-500">{t.incoming}</span>
                <p className="text-base font-bold text-slate-900 font-mono mt-0.5">৳ 51,300.00</p>
              </div>
              <div className="border-t border-slate-200/80 pt-2">
                <span className="text-slate-500">{t.outgoing}</span>
                <p className="text-base font-bold text-slate-900 font-mono mt-0.5">৳ 0.00</p>
              </div>
              <div className="border-t border-slate-200/80 pt-2">
                <span className="text-slate-500">{t.net}</span>
                <p className="text-lg font-extrabold text-blue-600 font-mono mt-0.5">৳ 51,300.00</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Invoices Overview Donut (Right 1 col) */}
        <Card className="p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">{t.invoicesOverview}</h3>
            <p className="text-xs text-slate-400 mt-0.5">Payment distribution of all posted invoices</p>
          </div>

          {/* SVG Donut Ring matching Reference Image 1 */}
          <div className="my-6 flex items-center justify-center">
            <div className="relative w-40 h-40">
              <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                {/* Background Track */}
                <circle cx="50" cy="50" r="38" stroke="#F1F5F9" strokeWidth="14" fill="transparent" />
                {/* Overdue (Coral) */}
                <circle cx="50" cy="50" r="38" stroke="#EF4444" strokeWidth="14" fill="transparent" strokeDasharray="238.7" strokeDashoffset="60" strokeLinecap="round" />
                {/* Paid (Green) */}
                <circle cx="50" cy="50" r="38" stroke="#10B981" strokeWidth="14" fill="transparent" strokeDasharray="238.7" strokeDashoffset="180" strokeLinecap="round" />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span className="text-xs text-slate-400 font-medium">Total</span>
                <span className="text-base font-bold text-slate-900 font-mono">৳ 51.3K</span>
              </div>
            </div>
          </div>

          {/* Legend Items */}
          <div className="space-y-2 border-t border-slate-100 pt-4 text-xs">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-slate-600">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                {t.paid}
              </span>
              <span className="font-semibold text-slate-900 font-mono">৳ 51,300.00</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-slate-600">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                {t.overdue}
              </span>
              <span className="font-semibold text-slate-900 font-mono">৳ 0.00</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-slate-600">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                {t.pending}
              </span>
              <span className="font-semibold text-slate-900 font-mono">৳ 0.00</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
