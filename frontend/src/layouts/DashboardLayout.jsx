import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  LayoutDashboard,
  FolderKanban,
  CheckSquare,
  User,
  Shield,
  LogOut,
  Sun,
  Moon,
  Menu,
  X
} from 'lucide-react';

const DashboardLayout = ({ children }) => {
  const { user, logout, hasRole } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem('theme') === 'dark' ||
    (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
  );

  // Toggle Dark Mode
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const navLinks = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Projects', path: '/projects', icon: FolderKanban },
    { name: 'Tasks', path: '/tasks', icon: CheckSquare },
    { name: 'Profile', path: '/profile', icon: User },
  ];

  // Admin Panel link is visible only to Admins
  const isAdmin = hasRole('Admin');
  if (isAdmin) {
    navLinks.push({ name: 'Admin Panel', path: '/admin', icon: Shield });
  }

  const isActive = (path) => location.pathname === path;

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-dark-900 transition-colors duration-200">
      {/* Sidebar for Desktop */}
      <aside className="hidden md:flex md:flex-col md:w-64 bg-white dark:bg-dark-800 border-r border-slate-200/60 dark:border-dark-700/60">
        {/* Brand Logo Header */}
        <div className="flex items-center gap-2 px-6 h-16 border-b border-slate-200/60 dark:border-dark-700/60">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-600 to-brand-400 text-white font-extrabold text-lg">
            P
          </div>
          <span className="font-bold text-slate-800 dark:text-white tracking-wide text-md">PMS Enterprise</span>
        </div>
        {/* Navigation list */}
        <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const active = isActive(link.path);
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all duration-200 ${
                  active
                    ? 'bg-brand-500 text-white shadow-premium shadow-brand-500/25'
                    : 'text-slate-600 dark:text-dark-300 hover:bg-slate-100 dark:hover:bg-dark-700'
                }`}
              >
                <Icon className="w-5 h-5" />
                {link.name}
              </Link>
            );
          })}
        </nav>
        {/* Sidebar Footer */}
        <div className="p-4 border-t border-slate-200/60 dark:border-dark-700/60 bg-slate-50/50 dark:bg-dark-950/20">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-brand-100 dark:bg-brand-950 flex items-center justify-center text-brand-600 dark:text-brand-300 font-semibold border border-brand-200/50">
                {user?.full_name?.charAt(0).toUpperCase()}
              </div>
              <div className="truncate max-w-[120px]">
                <p className="text-xs font-semibold text-slate-800 dark:text-white truncate">{user?.full_name}</p>
                <p className="text-[10px] text-slate-400 dark:text-dark-400 truncate">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Mobile Sidebar overlay Drawer */}
      {sidebarOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden bg-slate-900/60 backdrop-blur-sm">
          <div className="relative flex flex-col w-full max-w-xs bg-white dark:bg-dark-800 h-full p-6 shadow-premium">
            <button
              onClick={() => setSidebarOpen(false)}
              className="absolute top-4 right-4 p-2 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-700"
            >
              <X className="w-6 h-6" />
            </button>
            <div className="flex items-center gap-2 mb-8">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-brand-600 text-white font-extrabold text-lg">P</div>
              <span className="font-bold text-slate-800 dark:text-white">PMS Enterprise</span>
            </div>
            <nav className="flex-1 space-y-2">
              {navLinks.map((link) => {
                const Icon = link.icon;
                const active = isActive(link.path);
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    onClick={() => setSidebarOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-colors ${
                      active
                        ? 'bg-brand-500 text-white shadow-premium shadow-brand-500/25'
                        : 'text-slate-600 dark:text-dark-300 hover:bg-slate-100 dark:hover:bg-dark-700'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {link.name}
                  </Link>
                );
              })}
            </nav>
            <div className="pt-6 border-t border-slate-200 dark:border-dark-700">
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 w-full px-4 py-3 text-sm font-medium rounded-xl text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/20 transition-colors"
              >
                <LogOut className="w-5 h-5" />
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content Layout Block */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header bar */}
        <header className="flex items-center justify-between px-6 h-16 bg-white dark:bg-dark-800 border-b border-slate-200/60 dark:border-dark-700/60">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 -ml-2 rounded-lg text-slate-600 dark:text-dark-300 md:hidden hover:bg-slate-100 dark:hover:bg-dark-700"
            >
              <Menu className="w-6 h-6" />
            </button>
            <h1 className="text-lg font-bold text-slate-800 dark:text-white capitalize">
              {location.pathname === '/' ? 'Overview' : location.pathname.substring(1).replace('-', ' ')}
            </h1>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Dark Mode toggle button */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg text-slate-500 dark:text-dark-400 hover:bg-slate-100 dark:hover:bg-dark-700 transition-colors"
            >
              {darkMode ? <Sun className="w-5 h-5 text-amber-500" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>
        </header>

        {/* Content main block */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-slate-50 dark:bg-dark-900">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
