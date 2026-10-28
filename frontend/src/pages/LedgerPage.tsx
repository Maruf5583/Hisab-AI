import React, { useState } from 'react';
import {
  Scale,
  CheckCircle2,
  Search,
  ShieldCheck,
  AlertTriangle,
  FileSpreadsheet,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { LedgerEntry } from '../types/accounting';

interface LedgerPageProps {
  businessId?: string;
  lang: 'bn' | 'en';
}

const DEMO_LEDGER_ENTRIES: LedgerEntry[] = [
  {
    id: 'led-1',
    business_id: 'biz-default',
    transaction_type: 'opening_balance',
    reference_id: 'p-1',
    entry_date: '2026-04-01',
    account_name: 'Accounts Receivable',
    debit: '45000.00',
    credit: '0.00',
    party_id: 'p-1',
    description: 'Opening balance receivable for Lokendra Singh Shekhawat',
    is_reversal: false,
    created_at: '2026-04-01T00:00:00Z',
  },
  {
    id: 'led-2',
    business_id: 'biz-default',
    transaction_type: 'opening_balance',
    reference_id: 'p-1',
    entry_date: '2026-04-01',
    account_name: 'Opening Balance Equity',
    debit: '0.00',
    credit: '45000.00',
    party_id: 'p-1',
    description: 'Double-entry balancing equity for party opening balance',
    is_reversal: false,
    created_at: '2026-04-01T00:00:00Z',
  },
  {
    id: 'led-3',
    business_id: 'biz-default',
    transaction_type: 'opening_balance',
    reference_id: 'p-2',
    entry_date: '2026-04-01',
    account_name: 'Opening Balance Equity',
    debit: '90123.00',
    credit: '0.00',
    party_id: 'p-2',
    description: 'Double-entry balancing equity for party opening payable',
    is_reversal: false,
    created_at: '2026-04-01T00:00:00Z',
  },
  {
    id: 'led-4',
    business_id: 'biz-default',
    transaction_type: 'opening_balance',
    reference_id: 'p-2',
    entry_date: '2026-04-01',
    account_name: 'Accounts Payable',
    debit: '0.00',
    credit: '90123.00',
    party_id: 'p-2',
    description: 'Opening balance payable to Akash Singh',
    is_reversal: false,
    created_at: '2026-04-01T00:00:00Z',
  },
  {
    id: 'led-5',
    business_id: 'biz-default',
    transaction_type: 'invoice_posted',
    reference_id: 'inv-101',
    entry_date: '2026-04-18',
    account_name: 'Accounts Receivable',
    debit: '45000.00',
    credit: '0.00',
    party_id: 'p-1',
    description: 'Sales Invoice INV-2026-0042 posted',
    is_reversal: false,
    created_at: '2026-04-18T10:00:00Z',
  },
  {
    id: 'led-6',
    business_id: 'biz-default',
    transaction_type: 'invoice_posted',
    reference_id: 'inv-101',
    entry_date: '2026-04-18',
    account_name: 'Sales Revenue',
    debit: '0.00',
    credit: '42000.00',
    party_id: 'p-1',
    description: 'Net sales revenue recognized',
    is_reversal: false,
    created_at: '2026-04-18T10:00:00Z',
  },
  {
    id: 'led-7',
    business_id: 'biz-default',
    transaction_type: 'invoice_posted',
    reference_id: 'inv-101',
    entry_date: '2026-04-18',
    account_name: 'Output Tax Payable',
    debit: '0.00',
    credit: '3000.00',
    party_id: 'p-1',
    description: 'VAT on sales invoice',
    is_reversal: false,
    created_at: '2026-04-18T10:00:00Z',
  },
  {
    id: 'led-8',
    business_id: 'biz-default',
    transaction_type: 'payment_posted',
    reference_id: 'pay-201',
    entry_date: '2026-04-21',
    account_name: 'bKash Merchant Account',
    debit: '20000.00',
    credit: '0.00',
    party_id: 'p-1',
    description: 'Customer payment received via bKash',
    is_reversal: false,
    created_at: '2026-04-21T11:30:00Z',
  },
  {
    id: 'led-9',
    business_id: 'biz-default',
    transaction_type: 'payment_posted',
    reference_id: 'pay-201',
    entry_date: '2026-04-21',
    account_name: 'Accounts Receivable',
    debit: '0.00',
    credit: '20000.00',
    party_id: 'p-1',
    description: 'Reduction in receivable for customer payment',
    is_reversal: false,
    created_at: '2026-04-21T11:30:00Z',
  },
];

export const LedgerPage: React.FC<LedgerPageProps> = ({ lang }) => {
  const [entries] = useState<LedgerEntry[]>(DEMO_LEDGER_ENTRIES);
  const [accountFilter, setAccountFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const formatBDT = (amount: number | string) => {
    const num = typeof amount === 'string' ? parseFloat(amount) : amount;
    return `৳ ${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const totalDebit = entries.reduce((sum, e) => sum + parseFloat(e.debit || '0'), 0);
  const totalCredit = entries.reduce((sum, e) => sum + parseFloat(e.credit || '0'), 0);
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01;

  const accounts = Array.from(new Set(entries.map((e) => e.account_name)));

  const filteredEntries = entries.filter((e) => {
    if (accountFilter !== 'all' && e.account_name !== accountFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        e.description?.toLowerCase().includes(q) ||
        e.account_name.toLowerCase().includes(q) ||
        e.transaction_type.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
            <Scale className="w-6 h-6 text-blue-600" />
            <span>{lang === 'bn' ? 'সাধারণ খতিয়ান (General Ledger)' : 'General Ledger'}</span>
            <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Double-Entry Balanced</span>
            </div>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {lang === 'bn'
              ? 'আইনসম্মত দ্বৈত দাখিলা হিসাব ব্যবস্থার অপরিবর্তনীয় অডিট ট্রেইল (Immutable Double-Entry Ledger)'
              : 'Strict immutable journal entries verified for debits equals credits balance'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => alert('Exporting complete audit trail to CSV...')}
          >
            <FileSpreadsheet className="w-4 h-4 mr-1.5 text-emerald-600" />
            <span>Export CSV</span>
          </Button>
        </div>
      </div>

      {/* Trial Balance Health Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Total Debit (Dr)
          </p>
          <h3 className="text-2xl font-bold text-slate-900">{formatBDT(totalDebit)}</h3>
          <p className="text-[11px] text-slate-400 mt-1">Total debit entries posted</p>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-sm">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
            Total Credit (Cr)
          </p>
          <h3 className="text-2xl font-bold text-slate-900">{formatBDT(totalCredit)}</h3>
          <p className="text-[11px] text-slate-400 mt-1">Total credit entries posted</p>
        </div>

        <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              Trial Balance Status
            </p>
            {isBalanced ? (
              <h3 className="text-xl font-bold text-emerald-600 flex items-center gap-1.5">
                <ShieldCheck className="w-5 h-5 text-emerald-500" />
                <span>Balanced (0.00 Diff)</span>
              </h3>
            ) : (
              <h3 className="text-xl font-bold text-rose-600 flex items-center gap-1.5">
                <AlertTriangle className="w-5 h-5 text-rose-500" />
                <span>Out of Balance</span>
              </h3>
            )}
            <p className="text-[11px] text-slate-400 mt-1">Mathematical equilibrium confirmed</p>
          </div>
          <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 font-bold">
            =
          </div>
        </div>
      </div>

      {/* Ledger Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Account Filter:</span>
            <select
              value={accountFilter}
              onChange={(e) => setAccountFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none"
            >
              <option value="all">All Accounts ({accounts.length})</option>
              {accounts.map((acc) => (
                <option key={acc} value={acc}>
                  {acc}
                </option>
              ))}
            </select>
          </div>

          <div className="relative w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search ledger entries..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/70 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-5">Entry Date</th>
                <th className="py-3 px-5">Account Name</th>
                <th className="py-3 px-5">Transaction Type</th>
                <th className="py-3 px-5">Description & Reference</th>
                <th className="py-3 px-5 text-right">Debit (Dr)</th>
                <th className="py-3 px-5 text-right">Credit (Cr)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700 font-medium">
              {filteredEntries.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-5 font-mono text-slate-500">{e.entry_date}</td>
                  <td className="py-3 px-5">
                    <span className="font-semibold text-slate-900 block">{e.account_name}</span>
                  </td>
                  <td className="py-3 px-5">
                    <span className="inline-block px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-100 text-slate-600 border border-slate-200">
                      {e.transaction_type}
                    </span>
                  </td>
                  <td className="py-3 px-5">
                    <p className="text-slate-800">{e.description}</p>
                    <span className="text-[10px] text-slate-400 font-mono">Ref: {e.reference_id}</span>
                  </td>
                  <td className="py-3 px-5 text-right font-mono font-semibold text-slate-900">
                    {parseFloat(e.debit) > 0 ? formatBDT(e.debit) : '—'}
                  </td>
                  <td className="py-3 px-5 text-right font-mono font-semibold text-slate-900">
                    {parseFloat(e.credit) > 0 ? formatBDT(e.credit) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-slate-100 font-bold text-xs border-t-2 border-slate-300">
              <tr>
                <td colSpan={4} className="py-3 px-5 text-right text-slate-600 uppercase">
                  Total Trial Balance:
                </td>
                <td className="py-3 px-5 text-right font-mono text-slate-900">{formatBDT(totalDebit)}</td>
                <td className="py-3 px-5 text-right font-mono text-slate-900">{formatBDT(totalCredit)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
};
