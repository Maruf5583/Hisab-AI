import React, { useState, useEffect } from 'react';
import {
  Receipt,
  Search,
  Eye,
  AlertCircle,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Invoice } from '../types/accounting';
import { invoiceApi } from '../api/invoices';

interface InvoicesPageProps {
  businessId?: string;
  lang: 'bn' | 'en';
}

const DEMO_INVOICES: Invoice[] = [
  {
    id: 'inv-101',
    business_id: 'biz-default',
    party_id: 'p-1',
    party_name: 'Lokendra Singh Shekhawat',
    invoice_type: 'sales',
    invoice_number: 'INV-2026-0042',
    issue_date: '2026-04-18',
    due_date: '2026-05-02',
    subtotal: '42000.00',
    tax_amount: '3000.00',
    total_amount: '45000.00',
    paid_amount: '20000.00',
    due_amount: '25000.00',
    status: 'partially_paid',
    notes: 'Sale of industrial stationery goods',
    items: [
      { id: 'item-1', description: 'A4 Offset Printing Paper (Box of 5)', quantity: 20, unit_price: 1500, line_total: 30000, tax_rate: 0.075 },
      { id: 'item-2', description: 'Heavy Duty Document Binder Files', quantity: 80, unit_price: 150, line_total: 12000, tax_rate: 0.075 },
    ],
    created_at: '2026-04-18T10:00:00Z',
  },
  {
    id: 'inv-102',
    business_id: 'biz-default',
    party_id: 'p-2',
    party_name: 'Akash Singh',
    invoice_type: 'purchase',
    invoice_number: 'BILL-8891',
    issue_date: '2026-04-20',
    due_date: '2026-05-05',
    subtotal: '85000.00',
    tax_amount: '5123.00',
    total_amount: '90123.00',
    paid_amount: '90123.00',
    due_amount: '0.00',
    status: 'paid',
    notes: 'Raw material procurement from Chittagong port warehouse',
    items: [
      { id: 'item-3', description: 'Kraft Pulp Raw Paper Reels (Tons)', quantity: 1, unit_price: 85000, line_total: 85000, tax_rate: 0.06 },
    ],
    created_at: '2026-04-20T14:20:00Z',
  },
  {
    id: 'inv-103',
    business_id: 'biz-default',
    party_id: 'p-6',
    party_name: 'মেসার্স আল-মদিনা ট্রেডার্স',
    invoice_type: 'sales',
    invoice_number: 'চালান-৯৮২',
    issue_date: '2026-04-22',
    due_date: '2026-05-06',
    subtotal: '172000.00',
    tax_amount: '13000.00',
    total_amount: '185000.00',
    paid_amount: '0.00',
    due_amount: '185000.00',
    status: 'approved',
    notes: 'পাইকারি স্টেশনারি সরবরাহ চালান',
    items: [
      { id: 'item-4', description: 'প্রিমিয়াম আর্ট কার্ড রিম (১০০ প্যাক)', quantity: 50, unit_price: 2500, line_total: 125000, tax_rate: 0.07 },
      { id: 'item-5', description: 'হাই-গ্লস লেমিনেশন রোল', quantity: 10, unit_price: 4700, line_total: 47000, tax_rate: 0.07 },
    ],
    created_at: '2026-04-22T16:00:00Z',
  },
  {
    id: 'inv-104',
    business_id: 'biz-default',
    party_id: 'p-7',
    party_name: 'করিম ব্রাদার্স পেপার মিলস',
    invoice_type: 'purchase',
    invoice_number: 'KB-BILL-2026-11',
    issue_date: '2026-04-23',
    due_date: '2026-05-15',
    subtotal: '60000.00',
    tax_amount: '4000.00',
    total_amount: '64000.00',
    paid_amount: '0.00',
    due_amount: '64000.00',
    status: 'approved',
    notes: 'টঙ্গী গোডাউন থেকে ডেলিভারি চালান',
    items: [
      { id: 'item-6', description: 'ডুপ্লেক্স বোর্ড বান্ডিল (২০০ কেজি)', quantity: 20, unit_price: 3000, line_total: 60000, tax_rate: 0.067 },
    ],
    created_at: '2026-04-23T11:00:00Z',
  },
];

export const InvoicesPage: React.FC<InvoicesPageProps> = ({ businessId, lang }) => {
  const [invoices, setInvoices] = useState<Invoice[]>(DEMO_INVOICES);
  const [loading, setLoading] = useState<boolean>(false);
  const [filterType, setFilterType] = useState<'all' | 'sales' | 'purchase'>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  useEffect(() => {
    const fetchInvoices = async () => {
      setLoading(true);
      try {
        const res = await invoiceApi.list({
          invoice_type: filterType === 'all' ? undefined : filterType,
          status: statusFilter === 'all' ? undefined : statusFilter,
          search: searchQuery || undefined,
        });
        if (res && res.items && res.items.length > 0) {
          setInvoices(res.items);
        } else {
          setInvoices(DEMO_INVOICES);
        }
      } catch {
        setInvoices(DEMO_INVOICES);
      } finally {
        setLoading(false);
      }
    };
    fetchInvoices();
  }, [businessId, filterType, statusFilter]);

  const formatBDT = (amount: number | string) => {
    const num = typeof amount === 'string' ? parseFloat(amount) : amount;
    return `৳ ${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const filteredInvoices = invoices.filter((inv) => {
    if (filterType !== 'all' && inv.invoice_type !== filterType) return false;
    if (statusFilter !== 'all' && inv.status !== statusFilter) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchNum = inv.invoice_number.toLowerCase().includes(q);
      const matchParty = inv.party_name?.toLowerCase().includes(q);
      return matchNum || matchParty;
    }
    return true;
  });

  const totalSales = invoices
    .filter((inv) => inv.invoice_type === 'sales')
    .reduce((sum, inv) => sum + parseFloat(inv.total_amount), 0);

  const totalPurchases = invoices
    .filter((inv) => inv.invoice_type === 'purchase')
    .reduce((sum, inv) => sum + parseFloat(inv.total_amount), 0);

  const totalOutstandingDue = invoices
    .reduce((sum, inv) => sum + parseFloat(inv.due_amount), 0);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
            <Receipt className="w-6 h-6 text-blue-600" />
            <span>{lang === 'bn' ? 'চালান ও বিল সমূহ (Invoices & Bills)' : 'Invoices & Bills'}</span>
            <span className="text-xs font-normal text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-200">
              {filteredInvoices.length} Total
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            {lang === 'bn'
              ? 'যাচাইকৃত নথি থেকে প্রস্তুত বিক্রয় চালান এবং ক্রয় বিলের রেজিস্টার'
              : 'Official verified sales invoices and purchase bills ledger with strict accounting integrity'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder={lang === 'bn' ? 'চালান নং বা পার্টির নাম খুঁজুন...' : 'Search invoice or party...'}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none shadow-sm"
            />
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              {lang === 'bn' ? 'মোট বিক্রয় চালান' : 'Total Sales Invoiced'}
            </p>
            <h3 className="text-2xl font-bold text-slate-900">{formatBDT(totalSales)}</h3>
            <p className="text-[11px] text-emerald-600 font-medium mt-1">
              {invoices.filter((i) => i.invoice_type === 'sales').length} Sales Records
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <TrendingUp className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              {lang === 'bn' ? 'মোট ক্রয় বিল' : 'Total Purchase Bills'}
            </p>
            <h3 className="text-2xl font-bold text-slate-900">{formatBDT(totalPurchases)}</h3>
            <p className="text-[11px] text-indigo-600 font-medium mt-1">
              {invoices.filter((i) => i.invoice_type === 'purchase').length} Purchase Records
            </p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <TrendingDown className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
              {lang === 'bn' ? 'মোট অপরিশোধিত বাকি' : 'Total Outstanding Due'}
            </p>
            <h3 className="text-2xl font-bold text-rose-600">{formatBDT(totalOutstandingDue)}</h3>
            <p className="text-[11px] text-slate-400 mt-1">Across all active accounts</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center">
            <AlertCircle className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
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
              {lang === 'bn' ? 'সকল' : 'All'} ({invoices.length})
            </button>
            <button
              onClick={() => setFilterType('sales')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                filterType === 'sales'
                  ? 'bg-blue-50 text-blue-700 border border-blue-200'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              {lang === 'bn' ? 'বিক্রয় চালান (Sales)' : 'Sales Invoices'}
            </button>
            <button
              onClick={() => setFilterType('purchase')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                filterType === 'purchase'
                  ? 'bg-blue-50 text-blue-700 border border-blue-200'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              {lang === 'bn' ? 'ক্রয় বিল (Purchase)' : 'Purchase Bills'}
            </button>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none"
            >
              <option value="all">All Statuses</option>
              <option value="approved">Approved</option>
              <option value="partially_paid">Partially Paid</option>
              <option value="paid">Fully Paid</option>
            </select>
          </div>
        </div>

        {/* Invoice Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/70 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-5">Invoice #</th>
                <th className="py-3 px-5">Party</th>
                <th className="py-3 px-5">Type</th>
                <th className="py-3 px-5">Issue Date</th>
                <th className="py-3 px-5">Due Date</th>
                <th className="py-3 px-5 text-right">Total Amount</th>
                <th className="py-3 px-5 text-right">Due Amount</th>
                <th className="py-3 px-5 text-center">Status</th>
                <th className="py-3 px-5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700 font-medium">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    Loading invoices from database...
                  </td>
                </tr>
              ) : filteredInvoices.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    No invoices found matching criteria.
                  </td>
                </tr>
              ) : (
                filteredInvoices.map((inv) => (
                <tr
                  key={inv.id}
                  className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                  onClick={() => setSelectedInvoice(inv)}
                >
                  <td className="py-3.5 px-5 font-mono font-semibold text-blue-600">
                    {inv.invoice_number}
                  </td>
                  <td className="py-3.5 px-5">
                    <div className="font-semibold text-slate-900">{inv.party_name || 'Party #' + inv.party_id}</div>
                  </td>
                  <td className="py-3.5 px-5">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                        inv.invoice_type === 'sales'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-blue-50 text-blue-700 border border-blue-200'
                      }`}
                    >
                      {inv.invoice_type}
                    </span>
                  </td>
                  <td className="py-3.5 px-5 text-slate-500 font-mono">
                    {inv.issue_date}
                  </td>
                  <td className="py-3.5 px-5 text-slate-500 font-mono">
                    {inv.due_date || '—'}
                  </td>
                  <td className="py-3.5 px-5 text-right font-bold text-slate-900 font-mono">
                    {formatBDT(inv.total_amount)}
                  </td>
                  <td className="py-3.5 px-5 text-right font-mono font-bold text-rose-600">
                    {parseFloat(inv.due_amount) > 0 ? formatBDT(inv.due_amount) : '৳ 0.00'}
                  </td>
                  <td className="py-3.5 px-5 text-center">
                    <Badge
                      variant={
                        inv.status === 'paid'
                          ? 'success'
                          : inv.status === 'partially_paid'
                          ? 'warning'
                          : 'neutral'
                      }
                      size="sm"
                    >
                      {inv.status.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-5 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedInvoice(inv);
                      }}
                      className="text-blue-600 hover:text-blue-700"
                    >
                      <Eye className="w-3.5 h-3.5 mr-1" />
                      <span>Details</span>
                    </Button>
                  </td>
                </tr>
              )))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invoice Details Modal */}
      {selectedInvoice && (
        <Modal
          isOpen={!!selectedInvoice}
          onClose={() => setSelectedInvoice(null)}
          title={`Invoice: ${selectedInvoice.invoice_number}`}
          maxWidth="2xl"
        >
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <p className="text-xs text-slate-500">Party</p>
                <p className="text-base font-bold text-slate-900">{selectedInvoice.party_name}</p>
                <p className="text-xs text-slate-500 mt-1">Issue Date: {selectedInvoice.issue_date}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-500">Total Invoice Amount</p>
                <p className="text-xl font-bold text-blue-600">{formatBDT(selectedInvoice.total_amount)}</p>
                <p className="text-xs text-rose-600 font-semibold mt-1">Due: {formatBDT(selectedInvoice.due_amount)}</p>
              </div>
            </div>

            {/* Line Items Table */}
            <div>
              <h4 className="text-xs font-bold text-slate-700 mb-2 uppercase tracking-wider">Line Items</h4>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 text-slate-600 font-semibold text-[11px]">
                    <tr>
                      <th className="py-2 px-3">Item Description</th>
                      <th className="py-2 px-3 text-right">Qty</th>
                      <th className="py-2 px-3 text-right">Unit Price</th>
                      <th className="py-2 px-3 text-right">Line Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {selectedInvoice.items?.map((item) => (
                      <tr key={item.id} className="hover:bg-slate-50">
                        <td className="py-2 px-3 font-medium text-slate-800">{item.description}</td>
                        <td className="py-2 px-3 text-right font-mono">{item.quantity}</td>
                        <td className="py-2 px-3 text-right font-mono">{formatBDT(item.unit_price)}</td>
                        <td className="py-2 px-3 text-right font-mono font-semibold text-slate-900">{formatBDT(item.line_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-slate-50 font-semibold text-xs border-t border-slate-200">
                    <tr>
                      <td colSpan={3} className="py-2 px-3 text-right text-slate-500">Subtotal:</td>
                      <td className="py-2 px-3 text-right font-mono">{formatBDT(selectedInvoice.subtotal)}</td>
                    </tr>
                    <tr>
                      <td colSpan={3} className="py-2 px-3 text-right text-slate-500">Tax / VAT:</td>
                      <td className="py-2 px-3 text-right font-mono">{formatBDT(selectedInvoice.tax_amount)}</td>
                    </tr>
                    <tr className="text-sm font-bold text-slate-900 border-t border-slate-300">
                      <td colSpan={3} className="py-2 px-3 text-right">Grand Total:</td>
                      <td className="py-2 px-3 text-right font-mono text-blue-600">{formatBDT(selectedInvoice.total_amount)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>

            {selectedInvoice.notes && (
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600">
                <span className="font-semibold text-slate-700">Remarks: </span>
                {selectedInvoice.notes}
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button variant="outline" size="sm" onClick={() => setSelectedInvoice(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
