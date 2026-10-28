import React, { useState, useEffect } from 'react';
import { Sidebar, NavTab } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { AuthModal } from './components/auth/AuthModal';
import { DashboardPage } from './pages/DashboardPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { DocumentReviewPage } from './pages/DocumentReviewPage';
import { PartiesPage } from './pages/PartiesPage';
import { InvoicesPage } from './pages/InvoicesPage';
import { PaymentsPage } from './pages/PaymentsPage';
import { LedgerPage } from './pages/LedgerPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';
import { Business } from './types/business';
import { User } from './types/auth';
import { businessApi } from './api/businesses';
import { authApi } from './api/auth';

// Default synthetic business for fallback/offline preview
const DEFAULT_BUSINESS: Business = {
  id: 'biz-b9281a02-0941',
  name: 'মেসার্স সততা ট্রেডিং অ্যান্ড কোং',
  slug: 'satata-trading',
  currency: 'BDT',
  is_active: true,
  created_at: '2026-04-01T00:00:00Z',
  updated_at: '2026-04-01T00:00:00Z',
};

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('dashboard');
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [lang, setLang] = useState<'bn' | 'en'>('en');
  const [businesses, setBusinesses] = useState<Business[]>([DEFAULT_BUSINESS]);
  const [activeBusiness, setActiveBusiness] = useState<Business | null>(DEFAULT_BUSINESS);
  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('hisabai_user');
    return savedUser ? JSON.parse(savedUser) : null;
  });
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  useEffect(() => {
    // Attempt to verify session and fetch registered businesses
    const initSession = async () => {
      const token = localStorage.getItem('hisabai_token');
      if (token) {
        try {
          const me = await authApi.getMe();
          setUser(me);
          localStorage.setItem('hisabai_user', JSON.stringify(me));
        } catch {
          // Token expired or invalid
          localStorage.removeItem('hisabai_token');
          localStorage.removeItem('hisabai_user');
          setUser(null);
        }
      }

      try {
        const list = await businessApi.list();
        if (list && list.length > 0) {
          setBusinesses(list);
          setActiveBusiness(list[0]);
          localStorage.setItem('hisabai_active_business_id', list[0].id);
        }
      } catch {
        // Keep synthetic fallback
        localStorage.setItem('hisabai_active_business_id', DEFAULT_BUSINESS.id);
      }
    };
    initSession();
  }, []);

  const handleSelectBusiness = (b: Business) => {
    setActiveBusiness(b);
    localStorage.setItem('hisabai_active_business_id', b.id);
  };

  const handleAuthSuccess = (authenticatedUser: User, userBusinesses: Business[]) => {
    setUser(authenticatedUser);
    if (userBusinesses && userBusinesses.length > 0) {
      setBusinesses(userBusinesses);
      setActiveBusiness(userBusinesses[0]);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('hisabai_token');
    localStorage.removeItem('hisabai_user');
    localStorage.removeItem('hisabai_active_business_id');
    setUser(null);
    setBusinesses([DEFAULT_BUSINESS]);
    setActiveBusiness(DEFAULT_BUSINESS);
  };

  const handleSelectDocumentForReview = (docId: string) => {
    setSelectedDocId(docId);
    setCurrentTab('review');
  };

  const getPageTitle = (tab: NavTab) => {
    switch (tab) {
      case 'dashboard':
        return lang === 'bn' ? 'ড্যাশবোর্ড ওভারভিউ' : 'Executive Dashboard';
      case 'documents':
        return lang === 'bn' ? 'নথি ব্যবস্থাপনা (Inbox)' : 'Document Processing Inbox';
      case 'review':
        return lang === 'bn' ? 'নথি নিরীক্ষা ও যাচাই' : 'Document Review & Verification';
      case 'parties':
        return lang === 'bn' ? 'খাতা / পার্টি খতিয়ান' : 'Khata / Parties Register';
      case 'invoices':
        return lang === 'bn' ? 'চালান ও বিল সমূহ' : 'Invoices & Purchase Bills';
      case 'payments':
        return lang === 'bn' ? 'পেমেন্ট ও লেনদেন' : 'Payments & Receipts';
      case 'ledger':
        return lang === 'bn' ? 'সাধারণ খতিয়ান (General Ledger)' : 'General Ledger Audit Trail';
      case 'reports':
        return lang === 'bn' ? 'আর্থিক প্রতিবেদন' : 'Financial Statements & Aging';
      case 'settings':
        return lang === 'bn' ? 'সিস্টেম সেটিংস' : 'System & Organization Settings';
      default:
        return 'HisabAI';
    }
  };

  const getPageSubtitle = (tab: NavTab) => {
    switch (tab) {
      case 'dashboard':
        return lang === 'bn' ? 'আর্থিক পরিস্থিতি, ক্যাশফ্লো ও সাম্প্রতিক তথ্যাদি' : 'Live multi-tenant financial standing and operational KPIs';
      case 'documents':
        return lang === 'bn' ? 'পিডিএফ ও স্ক্যান করা ভাউচার আপলোড ও প্রসেসিং স্ট্যাটাস' : 'PDF text extraction & OCR document processing queue';
      case 'review':
        return lang === 'bn' ? 'স্প্লিট-স্ক্রিনে মূল নথি এবং নিষ্কাশিত ডেটার গাণিতিক সামঞ্জস্য যাচাই' : 'Side-by-side audit of extracted fields, confidence scores, and line items';
      case 'parties':
        return lang === 'bn' ? 'দেনাদার এবং পাওনাদারদের প্রারম্ভিক জের ও বকেয়া হিসাব' : 'Receivables, payables, and customer ledger balances';
      case 'invoices':
        return lang === 'bn' ? 'বিক্রয় চালান ও সরবরাহকারী ক্রয় বিল' : 'Double-entry posted sales and procurement records';
      case 'payments':
        return lang === 'bn' ? 'ক্যাশ, ব্যাংক, বিকাশ এবং নগদ লেনদেন' : 'Cash, Bank, bKash and Nagad payment allocations';
      case 'ledger':
        return lang === 'bn' ? 'অপরিবর্তনীয় দ্বৈত দাখিলা হিসাবের অডিট ট্রেইল' : 'Immutable double-entry debits, credits, and trial balance';
      case 'reports':
        return lang === 'bn' ? 'দেনা-পাওনা বয়স ভিত্তিক বিশ্লেষণ ও ভ্যাট হিসাব' : 'Aged receivables, payables, and period cashbook summaries';
      case 'settings':
        return lang === 'bn' ? 'প্রতিষ্ঠান প্রোফাইল এবং ওসিআর ইঞ্জিন কনফিগারেশন' : 'Multi-tenant organization profile and AI OCR configuration';
      default:
        return '';
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 font-sans text-slate-800 antialiased overflow-hidden">
      {/* Sidebar Navigation */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={(tab) => {
          setCurrentTab(tab);
          if (tab !== 'review') {
            setSelectedDocId(null);
          }
        }}
        businesses={businesses}
        activeBusiness={activeBusiness}
        onSelectBusiness={handleSelectBusiness}
        user={user}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
        lang={lang}
      />

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Global Application Header */}
        <Header
          title={getPageTitle(currentTab)}
          subtitle={getPageSubtitle(currentTab)}
          lang={lang}
          onToggleLang={() => setLang(lang === 'bn' ? 'en' : 'bn')}
        />

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          {currentTab === 'dashboard' && (
            <DashboardPage
              businessId={activeBusiness?.id}
              onNavigateToUpload={() => setCurrentTab('documents')}
              onNavigateToReview={() => {
                setSelectedDocId(null);
                setCurrentTab('review');
              }}
              lang={lang}
            />
          )}

          {currentTab === 'documents' && (
            <DocumentsPage
              onSelectDocumentForReview={handleSelectDocumentForReview}
              lang={lang}
            />
          )}

          {currentTab === 'review' && (
            <DocumentReviewPage
              documentId={selectedDocId}
              onBack={() => setCurrentTab('documents')}
              lang={lang}
            />
          )}

          {currentTab === 'parties' && (
            <PartiesPage
              businessId={activeBusiness?.id}
              lang={lang}
            />
          )}

          {currentTab === 'invoices' && (
            <InvoicesPage
              businessId={activeBusiness?.id}
              lang={lang}
            />
          )}

          {currentTab === 'payments' && (
            <PaymentsPage
              businessId={activeBusiness?.id}
              lang={lang}
            />
          )}

          {currentTab === 'ledger' && (
            <LedgerPage
              businessId={activeBusiness?.id}
              lang={lang}
            />
          )}

          {currentTab === 'reports' && (
            <ReportsPage
              businessId={activeBusiness?.id}
              lang={lang}
            />
          )}

          {currentTab === 'settings' && (
            <SettingsPage
              activeBusiness={activeBusiness}
              lang={lang}
            />
          )}
        </main>
      </div>

      {/* Authentication Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
        lang={lang}
      />
    </div>
  );
};
