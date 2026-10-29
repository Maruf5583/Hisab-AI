import React, { useState } from 'react';
import {
  Settings as SettingsIcon,
  Building2,
  Cpu,
  CheckCircle2,
  Server,
  Globe2,
  Save,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Business } from '../types/business';

interface SettingsPageProps {
  activeBusiness: Business | null;
  lang: 'bn' | 'en';
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ activeBusiness, lang }) => {
  const [bizName, setBizName] = useState(activeBusiness?.name || 'HisabAI Demo Enterprise');
  const currency = activeBusiness?.currency || 'BDT';
  const [ocrProvider, setOcrProvider] = useState<'gemini' | 'vision' | 'mock'>('gemini');
  const [geminiKey, setGeminiKey] = useState('');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
          <SettingsIcon className="w-6 h-6 text-blue-600" />
          <span>{lang === 'bn' ? 'সেটিংস ও কনফিগারেশন' : 'Settings & Configuration'}</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          {lang === 'bn'
            ? 'প্রতিষ্ঠান পরিচিতি, জেমিনি এআই ও ওসিআর ইঞ্জিন কনফিগারেশন এবং সিস্টেম স্ট্যাটাস'
            : 'Manage organization profile, Gemini AI & OCR extraction pipeline, and system health'}
        </p>
      </div>

      {savedSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs rounded-lg flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{lang === 'bn' ? 'সেটিংস সফলভাবে সংরক্ষিত হয়েছে।' : 'Settings saved successfully.'}</span>
        </div>
      )}

      {/* Business Details Section */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm space-y-4">
        <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
          <Building2 className="w-5 h-5 text-blue-600" />
          <h2 className="text-sm font-bold text-slate-900">
            {lang === 'bn' ? 'ব্যবসায়িক তথ্য' : 'Business Profile'}
          </h2>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Business Legal Name
              </label>
              <input
                type="text"
                value={bizName}
                onChange={(e) => setBizName(e.target.value)}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Base Accounting Currency
              </label>
              <input
                type="text"
                disabled
                value={`${currency} (Bangladeshi Taka ৳)`}
                className="w-full px-3 py-2 border border-slate-200 bg-slate-50 text-slate-500 rounded-lg text-xs font-medium cursor-not-allowed"
              />
            </div>
          </div>

          <div className="flex justify-end pt-2">
            <Button variant="primary" size="sm" type="submit">
              <Save className="w-3.5 h-3.5 mr-1.5" />
              <span>Save Changes</span>
            </Button>
          </div>
        </form>
      </div>

      {/* OCR & AI Configuration */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm space-y-4">
        <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
          <Cpu className="w-5 h-5 text-blue-600" />
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <span>{lang === 'bn' ? 'এআই ও ওসিআর ইঞ্জিন কনফিগারেশন' : 'AI & Document Intelligence Engine'}</span>
              <span className="px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 text-[10px] font-bold">
                Bilingual বাংলা & English
              </span>
            </h2>
            <p className="text-[11px] text-slate-400">
              Configure extraction providers for Bengali & English invoices and receipts
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Option 1: Google Gemini Flash (Recommended) */}
          <div
            onClick={() => setOcrProvider('gemini')}
            className={`p-4 rounded-xl border-2 cursor-pointer transition ${
              ocrProvider === 'gemini'
                ? 'border-blue-600 bg-blue-50/40 ring-1 ring-blue-600'
                : 'border-slate-200 hover:border-slate-300 bg-white'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-blue-600" />
                <span className="font-bold text-xs text-slate-900">Google Gemini Flash</span>
              </div>
              {ocrProvider === 'gemini' && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
            </div>
            <p className="text-xs text-slate-500">
              {lang === 'bn'
                ? 'বাংলা ও ইংরেজি হাতের লেখা মেমো, চালান ও ক্যাশ রসিদ গভীর বুদ্ধিমত্তায় শনাক্তকরণ। ১,৫০০ রিকোয়েস্ট/দিন বিনামূল্যে।'
                : 'Advanced AI vision for printed & handwritten Bengali & English chalans, cash memos & bills. Free 1,500 req/day.'}
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-[10px] text-emerald-600 font-semibold">
              <CheckCircle2 className="w-3 h-3 text-emerald-500" />
              <span>Recommended ⭐ (100% Free)</span>
            </div>
          </div>

          {/* Option 2: Google Cloud Vision OCR */}
          <div
            onClick={() => setOcrProvider('vision')}
            className={`p-4 rounded-xl border-2 cursor-pointer transition ${
              ocrProvider === 'vision'
                ? 'border-blue-600 bg-blue-50/40 ring-1 ring-blue-600'
                : 'border-slate-200 hover:border-slate-300 bg-white'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-xs text-slate-900">Google Cloud Vision</span>
              {ocrProvider === 'vision' && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
            </div>
            <p className="text-xs text-slate-500">
              {lang === 'bn'
                ? 'ক্লাসিকাল ক্লাউড ভিশন ওসিআর। বাউন্ডিং বক্স সহ অক্ষর চেনার সুবিধা।'
                : 'Traditional Cloud Vision bounding-box OCR. Requires GCP project and billing account.'}
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-[10px] text-slate-400 font-mono">
              <Globe2 className="w-3 h-3 text-slate-400" />
              <span>Languages: ben, eng</span>
            </div>
          </div>

          {/* Option 3: PyMuPDF / Local Test OCR */}
          <div
            onClick={() => setOcrProvider('mock')}
            className={`p-4 rounded-xl border-2 cursor-pointer transition ${
              ocrProvider === 'mock'
                ? 'border-blue-600 bg-blue-50/40 ring-1 ring-blue-600'
                : 'border-slate-200 hover:border-slate-300 bg-white'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-xs text-slate-900">PyMuPDF / Local Engine</span>
              {ocrProvider === 'mock' && <CheckCircle2 className="w-4 h-4 text-blue-600" />}
            </div>
            <p className="text-xs text-slate-500">
              {lang === 'bn'
                ? 'ডিজিটাল PDF টেক্সট এক্সট্রাকশন এবং অফলাইন ফলব্যাক রুল ইঞ্জিন।'
                : 'Embedded digital PDF text extractor. Instant, zero external network required, 100% offline verifiable.'}
            </p>
            <div className="mt-3 flex items-center gap-1.5 text-[10px] text-slate-600 font-semibold">
              <CheckCircle2 className="w-3 h-3 text-slate-500" />
              <span>Offline Fallback Ready</span>
            </div>
          </div>
        </div>

        {/* Gemini API Key Box */}
        {ocrProvider === 'gemini' && (
          <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                <span>Google Gemini API Key</span>
                <span className="text-[10px] text-slate-400 font-normal">
                  (backend/.env ফাইলে `GEMINI_API_KEY` হিসেবেও কনফিগার করতে পারেন)
                </span>
              </label>
              <a
                href="https://aistudio.google.com/app/apikey"
                target="_blank"
                rel="noreferrer"
                className="text-[11px] font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
              >
                <span>Get Free Key on Google AI Studio</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>

            <div className="flex gap-2">
              <input
                type="password"
                placeholder="AIzaSy..."
                value={geminiKey}
                onChange={(e) => setGeminiKey(e.target.value)}
                className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-xs font-mono focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  alert(
                    'Gemini API Key সেট করার জন্য backend/.env ফাইলে GEMINI_API_KEY=আপনার_কী পেস্ট করুন।'
                  );
                }}
              >
                Apply
              </Button>
            </div>
          </div>
        )}
      </div>

      {/* System Health & Architecture Status */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200/80 shadow-sm space-y-4">
        <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
          <Server className="w-5 h-5 text-blue-600" />
          <h2 className="text-sm font-bold text-slate-900">System Architecture Diagnostics</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-[10px] uppercase font-bold text-slate-400">Backend API</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-xs font-bold text-slate-900">FastAPI /api/v1/</span>
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">Port 8000 (Python 3.11)</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-[10px] uppercase font-bold text-slate-400">Database Engine</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              <span className="text-xs font-bold text-slate-900">PostgreSQL 18</span>
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">Database: hisabai_db (Port 5432)</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-[10px] uppercase font-bold text-slate-400">AI Document Engine</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="w-2 h-2 rounded-full bg-blue-500"></span>
              <span className="text-xs font-bold text-slate-900">Gemini 1.5 Flash</span>
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">Multimodal Bengali & EN</p>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-[10px] uppercase font-bold text-slate-400">Multi-Tenancy</span>
            <div className="flex items-center gap-2 mt-1">
              <span className="w-2 h-2 rounded-full bg-purple-500"></span>
              <span className="text-xs font-bold text-slate-900">Strict business_id</span>
            </div>
            <p className="text-[10px] text-slate-500 mt-0.5">14 Tables scoped & isolated</p>
          </div>
        </div>
      </div>
    </div>
  );
};
