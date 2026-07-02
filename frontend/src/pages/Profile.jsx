import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import api from '../services/api';
import { User, Mail, Shield, Calendar, Loader2, Save } from 'lucide-react';

const Profile = () => {
  const { user, login } = useAuth();
  const { showToast } = useToast();

  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || '');
  const [loading, setLoading] = useState(false);

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!fullName.trim() || !email.trim()) {
      showToast('Name and Email fields are required', 'warning');
      return;
    }

    setLoading(true);
    try {
      const res = await api.put('/users/me', {
        full_name: fullName,
        email: email,
        avatar_url: avatarUrl || null
      });

      if (res.data?.success) {
        showToast('Profile updated successfully!', 'success');
        // Force refresh session state
        window.location.reload();
      }
    } catch (err) {
      showToast(err.response?.data?.message || 'Failed to update profile settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Side: Avatar Card */}
        <div className="bg-white dark:bg-dark-800 p-6 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium flex flex-col items-center justify-center text-center">
          <div className="w-24 h-24 rounded-full bg-brand-100 dark:bg-brand-950 flex items-center justify-center text-brand-600 dark:text-brand-300 font-bold text-3xl mb-4 border-2 border-brand-200 shadow-sm overflow-hidden">
            {avatarUrl ? (
              <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
            ) : (
              user?.full_name?.charAt(0).toUpperCase()
            )}
          </div>
          <h3 className="font-extrabold text-slate-800 dark:text-white text-md">{user?.full_name}</h3>
          <p className="text-xs text-slate-400 mt-1">{user?.email}</p>
          
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 dark:bg-dark-900 border border-slate-200/50 mt-4 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <Shield className="w-3.5 h-3.5 text-brand-500" />
            {user?.roles?.map(r => r.name).join(', ')}
          </div>
        </div>

        {/* Right Side: Account configurations Form */}
        <div className="md:col-span-2 bg-white dark:bg-dark-800 p-6 md:p-8 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium">
          <h3 className="text-sm font-bold text-slate-700 dark:text-white uppercase mb-6 tracking-wide">Account Configurations</h3>
          
          <form onSubmit={handleUpdate} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Full Name</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
                    <User className="w-4 h-4" />
                  </span>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="block w-full pl-10 pr-4 py-2.5 text-sm text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 outline-none"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Email Address</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
                    <Mail className="w-4 h-4" />
                  </span>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="block w-full pl-10 pr-4 py-2.5 text-sm text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 outline-none"
                    required
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Avatar Image URL</label>
              <input
                type="url"
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
                placeholder="https://example.com/avatar.jpg"
                className="block w-full px-4 py-2.5 text-sm text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 outline-none"
              />
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-brand-500 hover:bg-brand-600 disabled:bg-brand-500/50 text-white font-semibold text-xs rounded-xl shadow-premium shadow-brand-500/10 transition-all"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Save Configurations
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Permissions Check Card */}
      <div className="bg-white dark:bg-dark-800 p-6 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium">
        <h3 className="text-sm font-bold text-slate-700 dark:text-white uppercase mb-4 tracking-wide">Security & Scopes</h3>
        <p className="text-xs text-slate-400 mb-6 leading-relaxed">
          The scopes assigned to your account dictate which actions you can execute.
        </p>
        
        <div className="flex flex-wrap gap-2.5">
          {user?.roles?.flatMap(r => r.permissions || []).map((perm) => (
            <span
              key={perm.id}
              className="text-[10px] font-bold px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-dark-900 border border-slate-200/40 dark:border-dark-700/40 text-slate-600 dark:text-dark-300"
            >
              {perm.name} ({perm.code})
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Profile;
