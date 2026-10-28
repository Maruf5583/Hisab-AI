import React, { useState, useEffect } from 'react';
import {
  Search,
  Plus,
  ArrowDownLeft,
  ArrowUpRight,
  TrendingDown,
  TrendingUp,
  FileText,
  Phone,
  Calendar,
  X,
  AlertCircle,
  Eye,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { partyApi } from '../api/parties';
import { Party, PartyBalance, PartyType, OpeningBalanceType } from '../types/party';
import { LedgerEntry } from '../types/accounting';

interface PartiesPageProps {
  businessId?: string;
  lang: 'bn' | 'en';
}

// Realistic synthetic demo data matching UI Reference Image 4
const DEMO_PARTIES: (Party & { due_date?: string; balance_type?: 'receivable' | 'payable' })[] = [
  {
    id: 'demo-p-1',
    business_id: 'biz-default',
    name: 'Lokendra Singh Shekhawat',
    party_type: 'buyer',
    phone: '01712-345678',
    email: 'lokendra@example.com',
    address: 'Chawkbazar, Dhaka',
    opening_balance: '45000.00',
    opening_balance_type: 'receivable',
    is_active: true,
    created_at: '2026-04-22T10:00:00Z',
    updated_at: '2026-04-22T10:00:00Z',
    due_date: '2026-04-28',
    balance_type: 'receivable',
  },
  {
    id: 'demo-p-2',
    business_id: 'biz-default',
    name: 'Akash Singh',
    party_type: 'supplier',
    phone: '01819-987654',
    email: 'akash@example.com',
    address: 'Agrabad, Chattogram',
    opening_balance: '90123.00',
    opening_balance_type: 'payable',
    is_active: true,
    created_at: '2026-04-22T11:15:00Z',
    updated_at: '2026-04-22T11:15:00Z',
    due_date: '2026-04-28',
    balance_type: 'payable',
  },
  {
    id: 'demo-p-3',
    business_id: 'biz-default',
    name: 'Gaurav Sharma',
    party_type: 'supplier',
    phone: '01911-223344',
    email: 'gaurav@example.com',
    address: 'Narayanganj Commercial Area',
    opening_balance: '12273.00',
    opening_balance_type: 'payable',
    is_active: true,
    created_at: '2026-04-22T12:00:00Z',
    updated_at: '2026-04-22T12:00:00Z',
    due_date: '2026-04-28',
    balance_type: 'payable',
  },
  {
    id: 'demo-p-4',
    business_id: 'biz-default',
    name: 'Nikhil Yadav',
    party_type: 'buyer',
    phone: '01678-554433',
    email: 'nikhil@example.com',
    address: 'Bogura Sadar',
    opening_balance: '2273.00',
    opening_balance_type: 'receivable',
    is_active: true,
    created_at: '2026-04-22T14:30:00Z',
    updated_at: '2026-04-22T14:30:00Z',
    due_date: '2026-04-28',
    balance_type: 'receivable',
  },
  {
    id: 'demo-p-5',
    business_id: 'biz-default',
    name: 'Rishabh Singh',
    party_type: 'buyer',
    phone: '01552-443322',
    email: 'rishabh@example.com',
    address: 'Rajshahi New Market',
    opening_balance: '7012273.00',
    opening_balance_type: 'receivable',
    is_active: true,
    created_at: '2026-04-22T15:45:00Z',
    updated_at: '2026-04-22T15:45:00Z',
    due_date: '2026-04-28',
    balance_type: 'receivable',
  },
  {
    id: 'demo-p-6',
    business_id: 'biz-default',
    name: 'মেসার্স আল-মদিনা ট্রেডার্স',
    party_type: 'buyer',
    phone: '01711-002233',
    email: 'almadina@example.com',
    address: 'কাওরান বাজার, ঢাকা',
    opening_balance: '185000.00',
    opening_balance_type: 'receivable',
    is_active: true,
    created_at: '2026-04-23T09:00:00Z',
    updated_at: '2026-04-23T09:00:00Z',
    due_date: '2026-05-05',
    balance_type: 'receivable',
  },
  {
    id: 'demo-p-7',
    business_id: 'biz-default',
    name: 'করিম ব্রাদার্স পেপার মিলস',
    party_type: 'supplier',
    phone: '01819-445566',
    email: 'karim.paper@example.com',
    address: 'টঙ্গী শিল্প এলাকা, গাজীপুর',
    opening_balance: '64000.00',
    opening_balance_type: 'payable',
    is_active: true,
    created_at: '2026-04-24T10:30:00Z',
    updated_at: '2026-04-24T10:30:00Z',
    due_date: '2026-05-10',
    balance_type: 'payable',
  },
];

export const PartiesPage: React.FC<PartiesPageProps> = ({ businessId, lang }) => {
  const [parties, setParties] = useState<Party[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [partyTypeFilter, setPartyTypeFilter] = useState<'all' | 'buyer' | 'supplier'>('all');
  const [sortBy, setSortBy] = useState<'recent' | 'amount_high' | 'name'>('recent');
  const [isUsingDemo, setIsUsingDemo] = useState<boolean>(false);

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);
  const [selectedParty, setSelectedParty] = useState<Party | null>(null);
  const [partyBalance, setPartyBalance] = useState<PartyBalance | null>(null);
  const [partyLedger, setPartyLedger] = useState<LedgerEntry[]>([]);
  const [loadingLedger, setLoadingLedger] = useState<boolean>(false);

  // Form state
  const [formName, setFormName] = useState('');
  const [formType, setFormType] = useState<PartyType>('buyer');
  const [formPhone, setFormPhone] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formAddress, setFormAddress] = useState('');
  const [formOpeningBalance, setFormOpeningBalance] = useState('0.00');
  const [formOpeningBalanceType, setFormOpeningBalanceType] = useState<OpeningBalanceType>('receivable');
  const [formSubmitting, setFormSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchParties = async () => {
    setLoading(true);
    try {
      const res = await partyApi.list({
        party_type: partyTypeFilter === 'all' ? undefined : partyTypeFilter,
        search: searchQuery || undefined,
      });
      if (res && res.items && res.items.length > 0) {
        setParties(res.items);
        setIsUsingDemo(false);
      } else {
        // Fallback to synthetic demo data
        setParties(DEMO_PARTIES);
        setIsUsingDemo(true);
      }
    } catch {
      // In offline / preview mode, show synthetic demo data
      setParties(DEMO_PARTIES);
      setIsUsingDemo(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchParties();
  }, [businessId, partyTypeFilter]);

  const handleOpenPartyLedger = async (party: Party) => {
    setSelectedParty(party);
    setLoadingLedger(true);
    try {
      const [bal, ledger] = await Promise.all([
        partyApi.getBalance(party.id).catch(() => null),
        partyApi.getLedger(party.id).catch(() => []),
      ]);
      setPartyBalance(bal);
      setPartyLedger(ledger);
    } catch {
      setPartyBalance(null);
      setPartyLedger([]);
    } finally {
      setLoadingLedger(false);
    }
  };

  const handleCreateParty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formName.trim()) {
      setFormError(lang === 'bn' ? 'পার্টির নাম প্রদান করুন' : 'Party name is required');
      return;
    }
    setFormSubmitting(true);
    setFormError(null);

    try {
      const newParty = await partyApi.create({
        name: formName.trim(),
        party_type: formType,
        phone: formPhone.trim() || undefined,
        email: formEmail.trim() || undefined,
        address: formAddress.trim() || undefined,
        opening_balance: formOpeningBalance || '0.00',
        opening_balance_type: formOpeningBalanceType,
      });

      setParties([newParty, ...parties]);
      setIsAddModalOpen(false);
      // Reset form
      setFormName('');
      setFormPhone('');
      setFormEmail('');
      setFormAddress('');
      setFormOpeningBalance('0.00');
    } catch (err: any) {
      setFormError(err.message || 'Failed to create party. Check inputs.');
    } finally {
      setFormSubmitting(false);
    }
  };

  // Compute Summary KPI Numbers
  const totalReceivable = parties
    .filter((p) => p.opening_balance_type === 'receivable')
    .reduce((sum, p) => sum + parseFloat(p.opening_balance || '0'), 0);

  const totalPayable = parties
    .filter((p) => p.opening_balance_type === 'payable')
    .reduce((sum, p) => sum + parseFloat(p.opening_balance || '0'), 0);

  const netBalance = totalReceivable - totalPayable;

  // Filter & Sort
  const filteredParties = parties.filter((p) => {
    if (partyTypeFilter !== 'all' && p.party_type !== partyTypeFilter && p.party_type !== 'both') {
      return false;
    }
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchName = p.name.toLowerCase().includes(q);
      const matchPhone = p.phone?.toLowerCase().includes(q);
      return matchName || matchPhone;
    }
    return true;
  }).sort((a, b) => {
    if (sortBy === 'amount_high') {
      return parseFloat(b.opening_balance || '0') - parseFloat(a.opening_balance || '0');
    }
    if (sortBy === 'name') {
      return a.name.localeCompare(b.name);
    }
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  const formatBDT = (amount: number | string) => {
    const num = typeof amount === 'string' ? parseFloat(amount) : amount;
    return `৳ ${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Top Banner / Breadcrumb Matching Reference Image 4 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-xs font-medium text-slate-400 mb-1 flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            <span>22 Apr, 2026</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
            <span>{lang === 'bn' ? 'খাতা (Khata)' : 'Khata'}</span>
            <span className="text-xs font-normal text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-200">
              {filteredParties.length} {lang === 'bn' ? 'টি পার্টি' : 'Parties'}
            </span>
            {isUsingDemo && (
              <span className="text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200/80 px-2 py-0.5 rounded-full">
                Demo Preview Mode
              </span>
            )}
          </h1>
        </div>

        {/* Search & Add New button */}
        <div className="flex items-center gap-3">
          <div className="relative w-64 sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder={lang === 'bn' ? 'নাম বা ফোন নম্বর খুঁজুন...' : 'Search Name or Contact'}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-white border border-slate-200 rounded-full text-xs font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm transition"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <button
            onClick={() => setIsAddModalOpen(true)}
            className="flex items-center gap-1.5 px-5 py-2.5 bg-purple-700 hover:bg-purple-800 text-white rounded-full font-medium text-xs shadow-md shadow-purple-600/20 transition active:scale-95"
          >
            <Plus className="w-4 h-4" />
            <span>{lang === 'bn' ? 'নতুন পার্টি যুক্ত করুন' : 'Add New'}</span>
          </button>
        </div>
      </div>

      {/* 3 Summary KPI Cards Matching Reference Image 4 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* You'll get */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm hover:shadow transition relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                {lang === 'bn' ? 'পাবেন (You\'ll get)' : 'You\'ll get'}
              </p>
              <h3 className="text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight">
                {formatBDT(totalReceivable)}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
              <ArrowDownLeft className="w-5 h-5 stroke-[2.5]" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>{lang === 'bn' ? 'মোট দেনাদারদের থেকে প্রাপ্য' : 'Total accounts receivable'}</span>
          </div>
        </div>

        {/* You'll give */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm hover:shadow transition relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                {lang === 'bn' ? 'দেবেন (You\'ll give)' : 'You\'ll give'}
              </p>
              <h3 className="text-2xl lg:text-3xl font-extrabold text-slate-900 tracking-tight">
                {formatBDT(totalPayable)}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
              <ArrowUpRight className="w-5 h-5 stroke-[2.5]" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-1.5 text-xs text-rose-600 font-medium">
            <TrendingDown className="w-3.5 h-3.5" />
            <span>{lang === 'bn' ? 'মোট পাওনাদারদের প্রদেয়' : 'Total accounts payable'}</span>
          </div>
        </div>

        {/* Net Balance */}
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-sm hover:shadow transition relative overflow-hidden">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                {lang === 'bn' ? 'নীট ব্যালেন্স (Net Balance)' : 'Net Balance'}
              </p>
              <h3 className={`text-2xl lg:text-3xl font-extrabold tracking-tight ${netBalance >= 0 ? 'text-purple-900' : 'text-rose-700'}`}>
                {formatBDT(netBalance)}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-600">
              <ArrowDownLeft className="w-5 h-5 stroke-[2.5]" />
            </div>
          </div>
          <div className="mt-3 flex items-center gap-1.5 text-xs text-purple-600 font-medium">
            <span>{lang === 'bn' ? 'ব্যবসায়ের সমন্বিত উদ্বৃত্ত' : 'Consolidated net standing'}</span>
          </div>
        </div>
      </div>

      {/* Main Party Table Section */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        {/* Table Filter Header */}
        <div className="p-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            {/* View Selector */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPartyTypeFilter('all')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  partyTypeFilter === 'all'
                    ? 'bg-purple-50 text-purple-700 border border-purple-200'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {lang === 'bn' ? 'সকল পার্টি' : 'All Parties'} ({parties.length})
              </button>
              <button
                onClick={() => setPartyTypeFilter('supplier')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  partyTypeFilter === 'supplier'
                    ? 'bg-purple-50 text-purple-700 border border-purple-200'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {lang === 'bn' ? 'সাপ্লায়ার তালিকা' : 'Supplier List'} (
                {parties.filter((p) => p.party_type === 'supplier' || p.party_type === 'both').length})
              </button>
              <button
                onClick={() => setPartyTypeFilter('buyer')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                  partyTypeFilter === 'buyer'
                    ? 'bg-purple-50 text-purple-700 border border-purple-200'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {lang === 'bn' ? 'কাস্টমার তালিকা' : 'Customer List'} (
                {parties.filter((p) => p.party_type === 'buyer' || p.party_type === 'both').length})
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Sort selector */}
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-none"
            >
              <option value="recent">Most Recent</option>
              <option value="amount_high">Highest Amount</option>
              <option value="name">Name A-Z</option>
            </select>

            <button
              onClick={() => alert(lang === 'bn' ? 'পার্টি বিবরণী রিপোর্ট তৈরির প্রক্রিয়াধীন...' : 'Generating Party Khata Report...')}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-purple-700 bg-purple-50 hover:bg-purple-100 rounded-lg border border-purple-200 transition"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>{lang === 'bn' ? 'রিপোর্ট দেখুন' : 'View Report'}</span>
            </button>
          </div>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/70 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                <th className="py-3 px-5">Supplier / Party Name</th>
                <th className="py-3 px-5">Entry Date</th>
                <th className="py-3 px-5">Due Date</th>
                <th className="py-3 px-5 text-right">Amount</th>
                <th className="py-3 px-5 text-center">Action / Status</th>
                <th className="py-3 px-5 text-right">Ledger</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs text-slate-700 font-medium">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    Loading party records...
                  </td>
                </tr>
              ) : filteredParties.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    No parties found matching criteria.
                  </td>
                </tr>
              ) : (
                filteredParties.map((p: any) => {
                  const isReceivable = p.opening_balance_type === 'receivable';
                  const entryDateFormatted = new Date(p.created_at).toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                  });
                  const dueDateFormatted = p.due_date || '28 Apr, 2026';

                  return (
                    <tr
                      key={p.id}
                      className="hover:bg-slate-50/80 transition-colors group cursor-pointer"
                      onClick={() => handleOpenPartyLedger(p)}
                    >
                      {/* Name & Contact */}
                      <td className="py-3.5 px-5">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500 font-bold text-xs flex-shrink-0 group-hover:bg-purple-100 group-hover:text-purple-700 transition">
                            {p.name.charAt(0)}
                          </div>
                          <div>
                            <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1">
                              <Phone className="w-2.5 h-2.5" />
                              <span>{p.phone || 'No Contact'}</span>
                            </div>
                            <div className="font-semibold text-slate-900 group-hover:text-purple-700 transition">
                              {p.name}
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Entry Date */}
                      <td className="py-3.5 px-5 text-slate-500">
                        {entryDateFormatted}
                      </td>

                      {/* Due Date */}
                      <td className="py-3.5 px-5 text-slate-500">
                        {dueDateFormatted}
                      </td>

                      {/* Amount */}
                      <td className="py-3.5 px-5 text-right font-bold text-slate-900">
                        {formatBDT(p.opening_balance)}
                      </td>

                      {/* Action status pill */}
                      <td className="py-3.5 px-5 text-center">
                        {isReceivable ? (
                          <span className="inline-flex items-center gap-1 font-semibold text-emerald-600 text-xs">
                            You'll get
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 font-semibold text-rose-600 text-xs">
                            You'll give
                          </span>
                        )}
                      </td>

                      {/* View Ledger */}
                      <td className="py-3.5 px-5 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenPartyLedger(p);
                          }}
                          className="text-purple-700 hover:text-purple-800 hover:bg-purple-50"
                        >
                          <Eye className="w-3.5 h-3.5 mr-1" />
                          <span>Ledger</span>
                        </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Party Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title={lang === 'bn' ? 'নতুন পার্টি যুক্ত করুন' : 'Add New Party'}
        maxWidth="md"
      >
        <form onSubmit={handleCreateParty} className="space-y-4">
          {formError && (
            <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {lang === 'bn' ? 'পার্টির নাম (বাংলা / English) *' : 'Party Name *'}
            </label>
            <input
              type="text"
              required
              placeholder="e.g. মেসার্স রহিম ট্রেডার্স / Rahim Traders"
              value={formName}
              onChange={(e) => setFormName(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {lang === 'bn' ? 'পার্টির ধরন' : 'Party Type'}
              </label>
              <select
                value={formType}
                onChange={(e) => setFormType(e.target.value as PartyType)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
                <option value="buyer">Customer (ক্রেতা)</option>
                <option value="supplier">Supplier (সরবরাহকারী)</option>
                <option value="both">Both (উভয়)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                {lang === 'bn' ? 'মোবাইল নম্বর' : 'Phone Number'}
              </label>
              <input
                type="text"
                placeholder="017XXXXXXXX"
                value={formPhone}
                onChange={(e) => setFormPhone(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
              >
              </input>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {lang === 'bn' ? 'ইমেইল (ঐচ্ছিক)' : 'Email (Optional)'}
            </label>
            <input
              type="email"
              placeholder="contact@business.com"
              value={formEmail}
              onChange={(e) => setFormEmail(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {lang === 'bn' ? 'ঠিকানা' : 'Address'}
            </label>
            <input
              type="text"
              placeholder="দোকান নং, বাজার, জেলা"
              value={formAddress}
              onChange={(e) => setFormAddress(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80 space-y-3">
            <div className="text-xs font-semibold text-slate-800">
              {lang === 'bn' ? 'প্রারম্ভিক জের (Opening Balance)' : 'Opening Balance'}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] text-slate-500 mb-1">
                  {lang === 'bn' ? 'পরিমাণ (টাকা)' : 'Amount (BDT)'}
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={formOpeningBalance}
                  onChange={(e) => setFormOpeningBalance(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono font-semibold focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-[11px] text-slate-500 mb-1">
                  {lang === 'bn' ? 'জের এর ধরন' : 'Balance Nature'}
                </label>
                <select
                  value={formOpeningBalanceType}
                  onChange={(e) => setFormOpeningBalanceType(e.target.value as OpeningBalanceType)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  <option value="receivable">You'll get (পাবেন)</option>
                  <option value="payable">You'll give (দেবেন)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <Button variant="outline" type="button" onClick={() => setIsAddModalOpen(false)}>
              {lang === 'bn' ? 'বাতিল' : 'Cancel'}
            </Button>
            <Button variant="primary" type="submit" isLoading={formSubmitting}>
              {lang === 'bn' ? 'সংরক্ষণ করুন' : 'Save Party'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Party Ledger Drawer / Modal */}
      {selectedParty && (
        <Modal
          isOpen={!!selectedParty}
          onClose={() => setSelectedParty(null)}
          title={`Ledger: ${selectedParty.name}`}
          maxWidth="2xl"
        >
          <div className="space-y-4">
            {/* Quick balance summary */}
            <div className="grid grid-cols-3 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <p className="text-[11px] text-slate-500 uppercase font-semibold">Opening Balance</p>
                <p className="text-sm font-bold text-slate-900">{formatBDT(selectedParty.opening_balance)}</p>
                <p className="text-[10px] text-slate-400 capitalize">{selectedParty.opening_balance_type}</p>
              </div>
              <div>
                <p className="text-[11px] text-slate-500 uppercase font-semibold">Current Balance</p>
                <p className="text-sm font-bold text-purple-700">
                  {partyBalance ? formatBDT(partyBalance.current_balance) : formatBDT(selectedParty.opening_balance)}
                </p>
                <p className="text-[10px] text-slate-400 capitalize">
                  {partyBalance?.balance_type || selectedParty.opening_balance_type}
                </p>
              </div>
              <div>
                <p className="text-[11px] text-slate-500 uppercase font-semibold">Contact</p>
                <p className="text-xs font-medium text-slate-800">{selectedParty.phone || 'N/A'}</p>
                <p className="text-[10px] text-slate-400 truncate">{selectedParty.address || 'No address'}</p>
              </div>
            </div>

            {/* Ledger Transactions */}
            <div>
              <h4 className="text-xs font-bold text-slate-800 mb-2 uppercase tracking-wider">
                Chronological Journal Entries
              </h4>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-100 text-slate-600 font-semibold text-[11px]">
                    <tr>
                      <th className="py-2 px-3">Date</th>
                      <th className="py-2 px-3">Description</th>
                      <th className="py-2 px-3 text-right">Debit (Dr)</th>
                      <th className="py-2 px-3 text-right">Credit (Cr)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {loadingLedger ? (
                      <tr>
                        <td colSpan={4} className="py-6 text-center text-slate-400">
                          Fetching verified ledger from database...
                        </td>
                      </tr>
                    ) : partyLedger.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="py-6 text-center text-slate-400">
                          Opening balance recorded. No additional invoices or vouchers posted yet.
                        </td>
                      </tr>
                    ) : (
                      partyLedger.map((entry) => (
                        <tr key={entry.id} className="hover:bg-slate-50">
                          <td className="py-2 px-3 font-mono text-[11px] text-slate-500">
                            {new Date(entry.entry_date).toLocaleDateString()}
                          </td>
                          <td className="py-2 px-3">
                            <span className="font-medium text-slate-800">{entry.description || entry.transaction_type}</span>
                            <span className="text-[10px] text-slate-400 block">{entry.account_name}</span>
                          </td>
                          <td className="py-2 px-3 text-right font-mono font-medium text-slate-800">
                            {parseFloat(entry.debit) > 0 ? formatBDT(entry.debit) : '—'}
                          </td>
                          <td className="py-2 px-3 text-right font-mono font-medium text-slate-800">
                            {parseFloat(entry.credit) > 0 ? formatBDT(entry.credit) : '—'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button variant="outline" size="sm" onClick={() => setSelectedParty(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
