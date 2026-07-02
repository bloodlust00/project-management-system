import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { Mail, Lock, User, Loader2, CheckCircle2, Circle } from 'lucide-react';

const Register = () => {
  const { register } = useAuth();
  const { showToast } = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  // Password requirements state
  const [checks, setChecks] = useState({
    length: false,
    upper: false,
    lower: false,
    number: false,
    special: false,
  });

  // Calculate password strength requirements on change
  useEffect(() => {
    setChecks({
      length: password.length >= 8,
      upper: /[A-Z]/.test(password),
      lower: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
    });
  }, [password]);

  const strengthCount = Object.values(checks).filter(Boolean).length;

  const getStrengthMeta = () => {
    if (password.length === 0) return { label: 'Empty', color: 'bg-slate-200 dark:bg-dark-700', width: 'w-0' };
    if (strengthCount <= 2) return { label: 'Weak', color: 'bg-rose-500', width: 'w-1/3' };
    if (strengthCount <= 4) return { label: 'Medium', color: 'bg-amber-500', width: 'w-2/3' };
    return { label: 'Strong', color: 'bg-emerald-500', width: 'w-full' };
  };

  const strengthMeta = getStrengthMeta();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (strengthCount < 5) {
      showToast('Please fulfill all password strength requirements.', 'warning');
      return;
    }

    setLoading(true);
    try {
      const success = await register(email, password, fullName);
      if (success) {
        showToast('Registration successful! Please login.', 'success');
        navigate('/login');
      }
    } catch (err) {
      const msg = err.response?.data?.message || 'Registration failed. Email might already exist.';
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-dark-950 px-4 py-12">
      <div className="w-full max-w-md z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-600 to-brand-400 text-white font-extrabold text-2xl shadow-premium mb-3">
            P
          </div>
          <h2 className="text-2xl font-extrabold text-slate-800 dark:text-white tracking-tight">PMS Enterprise</h2>
          <p className="text-sm text-slate-500 dark:text-dark-400 mt-1.5 font-medium">Create a new worker account</p>
        </div>

        <div className="bg-white dark:bg-dark-800 p-8 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Full Name</label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
                  <User className="w-5 h-5" />
                </span>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="John Doe"
                  className="block w-full pl-11 pr-4 py-3 text-sm text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 focus:ring-1 focus:ring-brand-500 outline-none transition-all"
                  required
                />
              </div>
            </div>

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
              
              {/* Strength Meter Bar */}
              {password.length > 0 && (
                <div className="mt-3">
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="text-slate-400">Strength:</span>
                    <span className="font-semibold text-slate-700 dark:text-white">{strengthMeta.label}</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-100 dark:bg-dark-700 rounded-full overflow-hidden">
                    <div className={`h-full transition-all duration-300 ${strengthMeta.color} ${strengthMeta.width}`}></div>
                  </div>
                  {/* Validation requirements list */}
                  <div className="grid grid-cols-2 gap-x-2 gap-y-1.5 mt-3 text-[11px] text-slate-500 dark:text-dark-400">
                    <div className="flex items-center gap-1.5">
                      {checks.length ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <Circle className="w-3.5 h-3.5 text-slate-300" />}
                      8+ characters
                    </div>
                    <div className="flex items-center gap-1.5">
                      {checks.upper ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <Circle className="w-3.5 h-3.5 text-slate-300" />}
                      1+ uppercase
                    </div>
                    <div className="flex items-center gap-1.5">
                      {checks.lower ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <Circle className="w-3.5 h-3.5 text-slate-300" />}
                      1+ lowercase
                    </div>
                    <div className="flex items-center gap-1.5">
                      {checks.number ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <Circle className="w-3.5 h-3.5 text-slate-300" />}
                      1+ number
                    </div>
                    <div className="flex items-center gap-1.5 col-span-2">
                      {checks.special ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <Circle className="w-3.5 h-3.5 text-slate-300" />}
                      1+ special character (!@#$%^&*)
                    </div>
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex items-center justify-center gap-2 w-full py-3.5 px-4 bg-brand-500 hover:bg-brand-600 disabled:bg-brand-500/50 text-white font-semibold rounded-xl shadow-premium transition-all mt-6"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Create Account'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-slate-500 dark:text-dark-400 mt-6">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-brand-500 hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </div>
  );
};

export default Register;
