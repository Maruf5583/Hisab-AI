import React, { useState } from 'react';
import {
  CreditCard,
  Plus,
  Search,
  ArrowDownLeft,
  ArrowUpRight,
  Wallet,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Payment } from '../types/accounting';

interface PaymentsPageProps {
  businessId?: string;
  lang: 'bn' | 'en';
}

const DEMO_PAYMENTS: Payment[] = [
  {
    id: 'pay-201',
    business_id: 'biz-default',
    party_id: 'p-1',
    party_name: 'Lokendra Singh Shekhawat',
    payment_type: 'customer_receipt',
    payment_method: 'bkash',
    payment_date: '2026-04-21',
    amount: '20000.00',
    allocated_amount: '20000.00',
    unapplied_amount: '0.00',
    reference_number: 'BK-992817261',
    status: 'posted',
    created_at: '2026-04-21T11:30:00Z',
  },
  {
    id: 'pay-202',
    business_id: 'biz-default',
    party_id: 'p-2',
    party_name: 'Akash Singh',
    payment_type: 'supplier_payment',
    payment_method: 'bank',
    payment_date: '2026-04-22',
    amount: '90123.00',
    allocated_amount: '90123.00',
    unapplied_amount: '0.00',
    reference_number: 'EBL-TRX-871625',
    status: 'posted',
    created_at: '2026-04-22T14:45:00Z',
  },
  {
    id: 'pay-203',
    business_id: 'biz-default',
    party_id: 'p-4',
    party_name: 'Nikhil Yadav',
    payment_type: 'customer_receipt',
    payment_method: 'nagad',
    payment_date: '2026-04-23',
    amount: '5000.00',
    allocated_amount: '2273.00',
    unapplied_amount: '2727.00',
    reference_number: 'NGD-6652418',
    status: 'posted',
    created_at: '2026-04-23T16:10:00Z',
  },
  {
    id: 'pay-204',
    business_id: 'biz-default',
    party_id: 'p-7',
    party_name: 'করিম ব্রাদার্স পেপার মিলস',
    payment_type: 'supplier_payment',
    payment_method: 'cash',
    payment_date: '2026-04-24',
    amount: '15000.00',
    allocated_amount: '15000.00',
    unapplied_amount: '0.00',
    reference_number: 'CASH-VOUCHER-08',
    status: 'posted',
    created_at: '2026-04-24T12:00:00Z',
  },
];

export const PaymentsPage: React.FC<PaymentsPageProps> = ({ lang }) => {
  const [payments, setPayments] = useState<Payment[]>(DEMO_PAYMENTS);
  const [filterType, setFilterType] = useState<'all' | 'customer_receipt' | 'supplier_payment'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // Form states
  const [formParty, setFormParty] = useState('');
  const [formType, setFormType] = useState<'customer_receipt' | 'supplier_payment'>('customer_receipt');
  const [formMethod, setFormMethod] = useState<'cash' | 'bank' | 'bkash' | 'nagad'>('bank');
  const [formAmount, setFormAmount] = useState('');
  const [formRef, setFormRef] = useState('');

  const formatBDT = (amount: number | string) => {
    const num = typeof amount === 'string' ? parseFloat(amount) : amount;
    return `৳ ${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const handleRecordPayment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formParty || !formAmount) return;

    const newPayment: Payment = {
      id: `pay-${Date.now()}`,
      business_id: 'biz-default',
      party_id: 'temp',
      party_name: formParty,
      payment_type: formType,
      payment_method: formMethod,
      payment_date: new Date().toISOString().split('T')[0],
      amount: parseFloat(formAmount).toFixed(2),
      allocated_amount: parseFloat(formAmount).toFixed(2),
      unapplied_amount: '0.00',
      reference_number: formRef || 'N/A',
      status: 'posted',
      created_at: new Date().toISOString(),
    };

    setPayments([newPayment, ...payments]);
    setIsAddModalOpen(false);
    setFormParty('');
    setFormAmount('');
    setFormRef('');
  };

  const totalReceipts = payments
    .filter((p) => p.payment_type === 'customer_receipt')
    .reduce((sum, p) => sum + parseFloat(p.amount), 0);

  const totalDisbursements = payments
    .filter((p) => p.payment_type === 'supplier_payment')
    .reduce((sum, p) => sum + parseFloat(p.amount), 0);

  const netCashFlow = totalReceipts - totalDisbursements;

  const filteredPayments = payments.filter((p) => {
    if (filterType !== 'all' && p.payment_type !== filterType) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return p.party_name?.toLowerCase().includes(q) || p.reference_number?.toLowerCase().includes(q);
    }
    return true;
  });

  const getMethodBadge = (method: string) => {
    switch (method) {
      case 'bkash':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-pink-50 text-pink-700 border border-pink-200">bKash</span>;
      case 'nagad':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-orange-50 text-orange-700 border border-orange-200">Nagad</span>;
      case 'bank':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">Bank Transfer</span>;
      case 'cash':
        return <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Cash</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-100 text-slate-700">{method}</span>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
            <CreditCard className="w-6 h-6 text-blue-600" />
            <span>{lang === 'bn' ? 'পেমেন্ট ও লেনদেন (Payments & Transactions)' : 'Payments & Transactions'}</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {lang === 'bn'
              ? 'গ্রাহক সংগ্রহ (Receipts) এবং সরবরাহকারী পরিশোধের (Disbursements) সম্পূর্ণ খতিয়ান'
              : 'Complete register for incoming customer receipts, supplier disbursements, and bank reconciliation'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="primary" onClick={() => setIsAddModalOpen(true)}>
            <Plus className="w-4 h-4 mr-1.5" />
            <span>{lang === 'bn' ? 'পেমেন্ট রেকর্ড করুন' : 'Record Payment'}</span>
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              {lang === 'bn' ? 'মোট প্রাপ্তি (Customer Receipts)' : 'Total Received'}
            </p>
            <h3 className="text-2xl font-bold text-emerald-600">{formatBDT(totalReceipts)}</h3>
            <p className="text-[11px] text-slate-400 mt-1">Money In to business</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <ArrowDownLeft className="w-5 h-5 stroke-[2.5]" />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              {lang === 'bn' ? 'মোট পরিশোধ (Supplier Payments)' : 'Total Paid Out'}
            </p>
            <h3 className="text-2xl font-bold text-rose-600">{formatBDT(totalDisbursements)}</h3>
            <p className="text-[11px] text-slate-400 mt-1">Money Out to vendors</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <ArrowUpRight className="w-5 h-5 stroke-[2.5]" />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              {lang === 'bn' ? 'নীট ক্যাশ প্রবাহ (Net Cash Flow)' : 'Net Cash Flow'}
            </p>
            <h3 className={`text-2xl font-bold ${netCashFlow >= 0 ? 'text-blue-700' : 'text-rose-700'}`}>
              {formatBDT(netCashFlow)}
            </h3>
            <p className="text-[11px] text-slate-400 mt-1">Period net movement</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Wallet className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setFilterType('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                filterType === 'all'
                  ? 'bg-blue-50 text-blue-700 border border-blue-200'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              All Transactions ({payments.length})
            </button>
            <button
              onClick={() => setFilterType('customer_receipt')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                filterType === 'customer_receipt'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Customer Receipts
            </button>
            <button
              onClick={() => setFilterType('supplier_payment')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                filterType === 'supplier_payment'
                  ? 'bg-rose-50 text-rose-700 border border-rose-200'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              Supplier Payments
            </button>
          </div>

          <div className="relative w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search party or ref..."
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
                <th className="py-3 px-5">Date</th>
                <th className="py-3 px-5">Party</th>
                <th className="py-3 px-5">Type</th>
                <th className="py-3 px-5">Method</th>
                <th className="py-3 px-5">Reference / TrxID</th>
                <th className="py-3 px-5 text-right">Amount</th>
                <th className="py-3 px-5 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700 font-medium">
              {filteredPayments.map((p) => {
                const isReceipt = p.payment_type === 'customer_receipt';
                return (
                  <tr key={p.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-5 font-mono text-slate-500">{p.payment_date}</td>
                    <td className="py-3.5 px-5 font-semibold text-slate-900">{p.party_name}</td>
                    <td className="py-3.5 px-5">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                          isReceipt
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-rose-50 text-rose-700 border border-rose-200'
                        }`}
                      >
                        {isReceipt ? 'Receipt' : 'Payment'}
                      </span>
                    </td>
                    <td className="py-3.5 px-5">{getMethodBadge(p.payment_method)}</td>
                    <td className="py-3.5 px-5 font-mono text-slate-500">{p.reference_number || '—'}</td>
                    <td className="py-3.5 px-5 text-right font-mono font-bold">
                      <span className={isReceipt ? 'text-emerald-600' : 'text-slate-900'}>
                        {isReceipt ? '+' : '-'}{formatBDT(p.amount)}
                      </span>
                    </td>
                    <td className="py-3.5 px-5 text-center">
                      <Badge variant="success" size="sm">
                        {p.status}
                      </Badge>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Record Payment Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title={lang === 'bn' ? 'নতুন পেমেন্ট রেকর্ড করুন' : 'Record New Payment'}
        maxWidth="md"
      >
        <form onSubmit={handleRecordPayment} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Payment Type</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setFormType('customer_receipt')}
                className={`p-2.5 rounded-lg border text-xs font-semibold text-center transition ${
                  formType === 'customer_receipt'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-700 ring-1 ring-emerald-500'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                Customer Receipt (Money In)
              </button>
              <button
                type="button"
                onClick={() => setFormType('supplier_payment')}
                className={`p-2.5 rounded-lg border text-xs font-semibold text-center transition ${
                  formType === 'supplier_payment'
                    ? 'border-rose-500 bg-rose-50 text-rose-700 ring-1 ring-rose-500'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                Supplier Payment (Money Out)
              </button>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Party Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Lokendra Singh Shekhawat"
              value={formParty}
              onChange={(e) => setFormParty(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Payment Method</label>
              <select
                value={formMethod}
                onChange={(e) => setFormMethod(e.target.value as any)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="bank">Bank Transfer</option>
                <option value="bkash">bKash Merchant</option>
                <option value="nagad">Nagad</option>
                <option value="cash">Cash in Hand</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Amount (BDT)</label>
              <input
                type="number"
                step="0.01"
                min="1"
                required
                placeholder="0.00"
                value={formAmount}
                onChange={(e) => setFormAmount(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono font-semibold focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Reference / TrxID</label>
            <input
              type="text"
              placeholder="e.g. EBL-TRX-10928 / BK-992817261"
              value={formRef}
              onChange={(e) => setFormRef(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button variant="outline" type="button" onClick={() => setIsAddModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Post to Ledger
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
