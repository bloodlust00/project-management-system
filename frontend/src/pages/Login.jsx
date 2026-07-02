import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { Mail, Lock, Loader2, ArrowRight } from 'lucide-react';

const Login = () => {
  const { login } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // Redirect destination after successful login
  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      showToast('Please fill in all fields', 'warning');
      return;
    }

    setLoading(true);
    try {
      const success = await login(email, password);
      if (success) {
        showToast('Welcome back!', 'success');
        navigate(from, { replace: true });
      }
    } catch (err) {
      const msg = err.response?.data?.message || 'Invalid email or password';
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-dark-950 px-4">
      {/* Background radial highlight */}
      <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-brand-500/10 via-transparent to-transparent pointer-events-none"></div>

      <div className="w-full max-w-md z-10">
        {/* Brand logo top header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-brand-400 text-white font-extrabold text-2xl shadow-premium shadow-brand-500/20 mb-3">
            P
          </div>
          <h2 className="text-2xl font-extrabold text-slate-800 dark:text-white tracking-tight">PMS Enterprise</h2>
          <p className="text-sm text-slate-500 dark:text-dark-400 mt-1.5">Sign in to manage your workspace</p>
        </div>

        {/* Card envelope */}
        <div className="bg-white dark:bg-dark-800 p-8 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Email Address</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
                  <Mail className="w-5 h-5" />
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="block w-full pl-11 pr-4 py-3 text-sm text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition-all"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Password</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
                  <Lock className="w-5 h-5" />
                </span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full pl-11 pr-4 py-3 text-sm text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition-all"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex items-center justify-center gap-2 w-full py-3.5 px-4 bg-brand-500 hover:bg-brand-600 disabled:bg-brand-500/50 text-white font-semibold rounded-xl shadow-premium shadow-brand-500/10 hover:shadow-brand-500/20 active:scale-[0.98] transition-all"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer info link */}
        <p className="text-center text-sm text-slate-500 dark:text-dark-400 mt-6">
          Don't have an account?{' '}
          <Link to="/register" className="font-semibold text-brand-500 hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Login;
