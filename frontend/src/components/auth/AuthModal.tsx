import React, { useState } from 'react';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { LogIn, UserPlus, Lock, Mail, User as UserIcon, Phone, AlertCircle } from 'lucide-react';
import { authApi } from '../../api/auth';
import { businessApi } from '../../api/businesses';
import { User } from '../../types/auth';
import { Business } from '../../types/business';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: (user: User, businesses: Business[]) => void;
  lang: 'bn' | 'en';
}

export const AuthModal: React.FC<AuthModalProps> = ({
  isOpen,
  onClose,
  onAuthSuccess,
  lang,
}) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === 'login') {
        const tokenRes = await authApi.login(email.trim(), password);
        localStorage.setItem('hisabai_token', tokenRes.access_token);

        // Fetch current user details
        const user = await authApi.getMe();
        localStorage.setItem('hisabai_user', JSON.stringify(user));

        // Fetch businesses
        let bizList: Business[] = [];
        try {
          bizList = await businessApi.list();
          if (bizList.length > 0) {
            localStorage.setItem('hisabai_active_business_id', bizList[0].id);
          }
        } catch {
          console.warn('Could not fetch business list, using default.');
        }

        onAuthSuccess(user, bizList);
        onClose();
      } else {
        // Register flow
        if (!fullName.trim()) {
          setError(lang === 'bn' ? 'সম্পূর্ণ নাম আবশ্যক' : 'Full name is required');
          setLoading(false);
          return;
        }

        await authApi.register({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
          phone: phone.trim() || undefined,
        });

        // Automatically login after successful registration
        const tokenRes = await authApi.login(email.trim(), password);
        localStorage.setItem('hisabai_token', tokenRes.access_token);

        const user = await authApi.getMe();
        localStorage.setItem('hisabai_user', JSON.stringify(user));

        // Create default business for new user
        let bizList: Business[] = [];
        try {
          const autoSlug = fullName.toLowerCase().replace(/[^a-z0-9]/g, '-') || `biz-${Date.now()}`;
          const newBiz = await businessApi.create({
            name: `${fullName}'s Enterprise`,
            slug: `${autoSlug}-${Math.floor(1000 + Math.random() * 9000)}`,
            currency: 'BDT',
          });
          bizList = [newBiz];
          localStorage.setItem('hisabai_active_business_id', newBiz.id);
        } catch {
          bizList = [];
        }

        onAuthSuccess(user, bizList);
        onClose();
      }
    } catch (err: any) {
      setError(
        err.message ||
          (mode === 'login'
            ? lang === 'bn'
              ? 'লগইন ব্যর্থ হয়েছে। ইমেইল বা পাসওয়ার্ড চেক করুন।'
              : 'Login failed. Check your email and password.'
            : lang === 'bn'
            ? 'নিবন্ধন ব্যর্থ হয়েছে। সঠিক তথ্য প্রদান করুন।'
            : 'Registration failed. Check inputs.')
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={
        mode === 'login'
          ? lang === 'bn'
            ? 'হিসাব এআই-তে লগইন করুন'
            : 'Sign in to HisabAI'
          : lang === 'bn'
          ? 'নতুন একাউন্ট খুলুন'
          : 'Create HisabAI Account'
      }
      maxWidth="md"
    >
      <div className="space-y-4">
        {/* Toggle Mode */}
        <div className="flex bg-slate-100 p-1 rounded-xl">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setError(null);
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition ${
              mode === 'login' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {lang === 'bn' ? 'লগইন' : 'Sign In'}
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register');
              setError(null);
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition ${
              mode === 'register' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            {lang === 'bn' ? 'নিবন্ধন' : 'Create Account'}
          </button>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          {mode === 'register' && (
            <>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {lang === 'bn' ? 'আপনার নাম *' : 'Full Name *'}
                </label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    placeholder="Maruf Hasan"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  {lang === 'bn' ? 'মোবাইল নম্বর' : 'Phone Number'}
                </label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="017XXXXXXXX"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {lang === 'bn' ? 'ইমেইল অ্যাড্রেস *' : 'Email Address *'}
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                placeholder="accountant@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              {lang === 'bn' ? 'পাসওয়ার্ড *' : 'Password *'}
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                minLength={6}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-xs font-medium focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>
            {mode === 'register' && (
              <p className="text-[10px] text-slate-400 mt-1">Minimum 6 characters required</p>
            )}
          </div>

          <div className="pt-2">
            <Button variant="primary" type="submit" isLoading={loading} className="w-full justify-center">
              {mode === 'login' ? (
                <>
                  <LogIn className="w-4 h-4 mr-1.5" />
                  <span>{lang === 'bn' ? 'লগইন করুন' : 'Sign In'}</span>
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4 mr-1.5" />
                  <span>{lang === 'bn' ? 'একাউন্ট তৈরি করুন' : 'Create Account'}</span>
                </>
              )}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};
