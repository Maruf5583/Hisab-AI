import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge, BadgeVariant } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import {
  FileText,
  UploadCloud,
  Search,
  Eye,
  Download,
  AlertCircle,
  Clock,
  CheckCircle2,
  RefreshCw,
} from 'lucide-react';
import { documentApi } from '../api/documents';
import { DocumentItem, DocumentStatus } from '../types/document';

interface DocumentsPageProps {
  onSelectDocumentForReview: (docId: string) => void;
  lang: 'bn' | 'en';
}

export const DocumentsPage: React.FC<DocumentsPageProps> = ({
  onSelectDocumentForReview,
  lang,
}) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [uploadModalOpen, setUploadModalOpen] = useState<boolean>(false);
  const [uploading, setUploading] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadDocType, setUploadDocType] = useState<string>('sales_invoice');

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await documentApi.list({
        status: activeFilter === 'all' ? undefined : activeFilter,
        search: searchQuery || undefined,
      });
      setDocuments(res.items || []);
    } catch (err: any) {
      console.warn('Live document list fetch error:', err);
      setError('Could not connect to live documents API. Showing mock inbox data.');
      // Fallback realistic demo documents matching Reference Image 2
      setDocuments([
        {
          id: 'doc-6dc2kt23',
          business_id: 'biz-1',
          original_filename: 'rahim_traders_sales_inv.pdf',
          file_hash_sha256: '9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d',
          mime_type: 'application/pdf',
          file_size_bytes: 245000,
          page_count: 1,
          document_type: 'sales_invoice',
          status: 'needs_review',
          created_at: '2026-10-28T10:30:00Z',
          updated_at: '2026-10-28T10:32:00Z',
          extraction: {
            id: 'ext-1',
            document_id: 'doc-6dc2kt23',
            party_name_candidate: 'মেসার্স রহিম ট্রেডার্স',
            document_number_candidate: 'INV-2026-0042',
            total_amount_candidate: '15500.00',
            paid_amount_candidate: '5500.00',
            due_amount_candidate: '10000.00',
            confidence_score: '0.96',
            is_human_corrected: false,
            created_at: '2026-10-28T10:31:00Z',
            updated_at: '2026-10-28T10:31:00Z',
          },
        },
        {
          id: 'doc-e6b9fa6a',
          business_id: 'biz-1',
          original_filename: 'bismillah_paper_bill.pdf',
          file_hash_sha256: '8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e',
          mime_type: 'application/pdf',
          file_size_bytes: 480000,
          page_count: 2,
          document_type: 'purchase_invoice',
          status: 'needs_review',
          created_at: '2026-10-27T14:15:00Z',
          updated_at: '2026-10-27T14:16:00Z',
          extraction: {
            id: 'ext-2',
            document_id: 'doc-e6b9fa6a',
            party_name_candidate: 'বিসমিল্লাহ পেপার সাপ্লায়ার্স',
            document_number_candidate: 'BILL-8891',
            total_amount_candidate: '40000.00',
            confidence_score: '0.92',
            is_human_corrected: false,
            created_at: '2026-10-27T14:15:30Z',
            updated_at: '2026-10-27T14:15:30Z',
          },
        },
        {
          id: 'doc-4jhf1a16',
          business_id: 'biz-1',
          original_filename: 'cash_memo_vouch_301.png',
          file_hash_sha256: '7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f',
          mime_type: 'image/png',
          file_size_bytes: 1250000,
          page_count: 1,
          document_type: 'payment_receipt',
          status: 'posted',
          created_at: '2026-10-25T09:00:00Z',
          updated_at: '2026-10-25T09:05:00Z',
          extraction: {
            id: 'ext-3',
            document_id: 'doc-4jhf1a16',
            party_name_candidate: 'করিম ব্রাদার্স',
            document_number_candidate: 'REC-301',
            total_amount_candidate: '5000.00',
            confidence_score: '0.98',
            is_human_corrected: true,
            created_at: '2026-10-25T09:01:00Z',
            updated_at: '2026-10-25T09:04:00Z',
          },
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [activeFilter]);

  const handleFileUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    try {
      setUploading(true);
      const uploadedDoc = await documentApi.upload(selectedFile, uploadDocType);
      // Auto trigger processing
      await documentApi.process(uploadedDoc.id);
      setUploadModalOpen(false);
      setSelectedFile(null);
      await fetchDocuments();
      onSelectDocumentForReview(uploadedDoc.id);
    } catch (err: any) {
      alert(err.message || 'File upload failed');
    } finally {
      setUploading(false);
    }
  };

  const statusMap: Record<DocumentStatus, { label: string; variant: BadgeVariant }> = {
    uploaded: { label: 'Uploaded', variant: 'neutral' },
    processing: { label: 'Processing', variant: 'info' },
    needs_review: { label: 'Needs Review', variant: 'warning' },
    approved: { label: 'Approved', variant: 'success' },
    posted: { label: 'Posted', variant: 'success' },
    rejected: { label: 'Rejected', variant: 'danger' },
  };

  const counts = {
    total: documents.length,
    needs_review: documents.filter((d) => d.status === 'needs_review').length,
    processing: documents.filter((d) => d.status === 'processing').length,
    posted: documents.filter((d) => d.status === 'posted').length,
  };

  return (
    <div className="space-y-6">
      {/* Top Header matching Reference Image 2 */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <FileText className="w-6 h-6 text-blue-600" />
            <span>{lang === 'bn' ? 'ডকুমেন্ট ইনবক্স' : 'Documents & Invoices'}</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'bn' ? 'সকল আপলোডকৃত চালানের তালিকা এবং পর্যালোচনার অবস্থা' : 'Central repository for uploaded invoices, receipts, and vouchers'}
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button variant="secondary" onClick={fetchDocuments} className="text-xs">
            <RefreshCw className="w-3.5 h-3.5 text-slate-500" />
            Refresh
          </Button>
          <Button variant="primary" onClick={() => setUploadModalOpen(true)} className="text-xs">
            <UploadCloud className="w-4 h-4" />
            {lang === 'bn' ? 'ডকুমেন্ট আপলোড' : 'Upload Document'}
          </Button>
        </div>
      </div>

      {/* 4 Status Counter Cards matching Reference Image 2 */}
      {error && (
        <div className="p-3 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-xl flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Total Documents</span>
            <FileText className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-slate-900 font-mono">{counts.total}</span>
            <span className="text-xs text-slate-400 font-medium">All Files</span>
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>AI Processing</span>
            <Clock className="w-4 h-4 text-blue-500" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-blue-600 font-mono">{counts.processing}</span>
            <span className="text-xs text-blue-500 font-medium">Extracting</span>
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Needs Review</span>
            <AlertCircle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-amber-600 font-mono">{counts.needs_review}</span>
            <span className="text-xs text-amber-600 font-medium bg-amber-50 px-2 py-0.5 rounded">Action Required</span>
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between text-xs text-slate-500 font-medium">
            <span>Verified & Posted</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-bold text-emerald-600 font-mono">{counts.posted}</span>
            <span className="text-xs text-emerald-600 font-medium">In Ledger</span>
          </div>
        </Card>
      </div>

      {/* Filter Tabs & Search Bar matching Reference Image 2 */}
      <Card className="p-4 space-y-4">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          {/* Status Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 text-xs">
            {[
              { id: 'all', label: `All (${counts.total})` },
              { id: 'needs_review', label: `Needs Review (${counts.needs_review})`, color: 'amber' },
              { id: 'posted', label: `Posted (${counts.posted})`, color: 'emerald' },
              { id: 'uploaded', label: 'Uploaded' },
              { id: 'rejected', label: 'Rejected' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setActiveFilter(f.id)}
                className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                  activeFilter === f.id
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-600'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          {/* Search Input */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search filename or party..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Documents Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50/80 text-slate-500 font-semibold border-b border-slate-100">
              <tr>
                <th className="py-3 px-3">Document ID</th>
                <th className="py-3 px-3">Date</th>
                <th className="py-3 px-3">Party / Vendor</th>
                <th className="py-3 px-3">Filename</th>
                <th className="py-3 px-3">Amount</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-10 text-slate-400">
                    Loading documents...
                  </td>
                </tr>
              ) : documents.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400">
                    <FileText className="w-8 h-8 mx-auto text-slate-300 mb-2" />
                    No documents found. Upload your first invoice or receipt!
                  </td>
                </tr>
              ) : (
                documents.map((doc) => {
                  const statusInfo = statusMap[doc.status] || { label: doc.status, variant: 'neutral' };
                  const amount = doc.extraction?.total_amount_candidate || '0.00';
                  const party = doc.extraction?.party_name_candidate || '—';

                  return (
                    <tr key={doc.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-3 font-mono text-slate-500">
                        {doc.id.substring(0, 10)}...
                      </td>
                      <td className="py-3 px-3 text-slate-600">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-3 font-medium text-slate-900">
                        {party}
                      </td>
                      <td className="py-3 px-3 text-slate-600 font-mono text-[11px] truncate max-w-[180px]">
                        {doc.original_filename}
                      </td>
                      <td className="py-3 px-3 font-bold text-slate-900 font-mono">
                        ৳ {amount}
                      </td>
                      <td className="py-3 px-3">
                        <Badge variant={statusInfo.variant}>
                          {statusInfo.label}
                        </Badge>
                      </td>
                      <td className="py-3 px-3 text-right space-x-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => onSelectDocumentForReview(doc.id)}
                          className="text-[11px] font-semibold text-blue-600 border-blue-200 hover:bg-blue-50"
                        >
                          <Eye className="w-3 h-3 text-blue-600" />
                          Review
                        </Button>
                        <a
                          href={documentApi.getDownloadUrl(doc.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
                          title="Download original file"
                        >
                          <Download className="w-3.5 h-3.5" />
                        </a>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Upload Modal */}
      <Modal
        isOpen={uploadModalOpen}
        onClose={() => setUploadModalOpen(false)}
        title="Upload Business Document"
        maxWidth="lg"
      >
        <form onSubmit={handleFileUpload} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Select Document File (PDF, PNG, JPG, WebP)
            </label>
            <div className="border-2 border-dashed border-slate-200 hover:border-blue-400 rounded-xl p-6 text-center cursor-pointer bg-slate-50/50 hover:bg-blue-50/20 transition-all">
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg,.webp"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                className="hidden"
                id="doc-upload-input"
              />
              <label htmlFor="doc-upload-input" className="cursor-pointer">
                <UploadCloud className="w-10 h-10 text-blue-500 mx-auto mb-2" />
                <p className="text-xs font-medium text-slate-700">
                  {selectedFile ? selectedFile.name : 'Click to browse or drag file here'}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">Maximum file size: 25 MB</p>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Document Type Hint
            </label>
            <select
              value={uploadDocType}
              onChange={(e) => setUploadDocType(e.target.value)}
              className="w-full text-xs p-2.5 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="sales_invoice">বিক্রয় চালান (Sales Invoice)</option>
              <option value="purchase_invoice">ক্রয় চালান (Purchase Invoice)</option>
              <option value="payment_receipt">টাকা জমা রসিদ (Payment Receipt)</option>
              <option value="voucher">খরচ ভাউচার (Expense Voucher)</option>
            </select>
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
            <Button variant="secondary" onClick={() => setUploadModalOpen(false)} type="button">
              Cancel
            </Button>
            <Button variant="primary" type="submit" isLoading={uploading} disabled={!selectedFile}>
              Upload & Extract
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
