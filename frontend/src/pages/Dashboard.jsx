import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import {
  FolderKanban,
  CheckSquare,
  MessageSquare,
  Clock,
  TrendingUp,
  AlertCircle,
  FileText
} from 'lucide-react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';

// Register ChartJS elements
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

const Dashboard = () => {
  const { user, hasPermission } = useAuth();
  const { showToast } = useToast();
  const [stats, setStats] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      // 1. Fetch statistics (cached on backend)
      const statsRes = await api.get('/metrics/stats');
      if (statsRes.data?.success) {
        setStats(statsRes.data.data);
      }

      // 2. Fetch audit logs if permitted
      if (hasPermission('audit:read')) {
        const logsRes = await api.get('/metrics/audit-logs?limit=5');
        if (logsRes.data?.success) {
          setAuditLogs(logsRes.data.data.items);
        }
      }
    } catch (err) {
      showToast('Failed to load dashboard statistics', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // Pre-calculate counts
  const pendingCount =
    (stats?.tasks_by_status?.TODO || 0) +
    (stats?.tasks_by_status?.IN_PROGRESS || 0) +
    (stats?.tasks_by_status?.REVIEW || 0);
  const completedCount = stats?.tasks_by_status?.DONE || 0;

  // Chart 1: Status distribution dataset
  const statusChartData = {
    labels: ['To Do', 'In Progress', 'In Review', 'Completed'],
    datasets: [
      {
        data: [
          stats?.tasks_by_status?.TODO || 0,
          stats?.tasks_by_status?.IN_PROGRESS || 0,
          stats?.tasks_by_status?.REVIEW || 0,
          completedCount,
        ],
        backgroundColor: ['#94a3b8', '#38bdf8', '#fbbf24', '#34d399'],
        borderWidth: 0,
      },
    ],
  };

  // Chart 2: Priority breakdown dataset
  const priorityChartData = {
    labels: ['Low', 'Medium', 'High'],
    datasets: [
      {
        label: 'Tasks Count',
        data: [
          stats?.tasks_by_priority?.LOW || 0,
          stats?.tasks_by_priority?.MEDIUM || 0,
          stats?.tasks_by_priority?.HIGH || 0,
        ],
        backgroundColor: ['#a7f3d0', '#fef08a', '#fecdd3'],
        borderColor: ['#10b981', '#f59e0b', '#f43f5e'],
        borderWidth: 1.5,
      },
    ],
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome banner */}
      <div className="bg-gradient-to-r from-brand-600 to-indigo-600 rounded-3xl p-8 text-white shadow-premium">
        <h2 className="text-3xl font-extrabold tracking-tight">Welcome, {user?.full_name}!</h2>
        <p className="text-brand-100 mt-2 max-w-xl text-sm font-medium">
          Here is your dashboard overview for your active project spaces. Keep track of progress, tasks timeline, and team operations.
        </p>
      </div>

      {/* Numerical Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
        {/* Card 1 */}
        <div className="bg-white dark:bg-dark-800 p-6 rounded-2xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium flex items-center justify-between">
          <div>
            <span className="block text-xs font-semibold text-slate-400 dark:text-dark-400 uppercase tracking-wider">Total Projects</span>
            <span className="block text-2xl font-extrabold text-slate-800 dark:text-white mt-1">{stats?.total_projects || 0}</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-brand-50 dark:bg-brand-950 flex items-center justify-center text-brand-600 dark:text-brand-400">
            <FolderKanban className="w-6 h-6" />
          </div>
        </div>

        {/* Card 2 */}
        <div className="bg-white dark:bg-dark-800 p-6 rounded-2xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium flex items-center justify-between">
          <div>
            <span className="block text-xs font-semibold text-slate-400 dark:text-dark-400 uppercase tracking-wider">Total Tasks</span>
            <span className="block text-2xl font-extrabold text-slate-800 dark:text-white mt-1">{stats?.total_tasks || 0}</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-slate-50 dark:bg-dark-700 flex items-center justify-center text-slate-600 dark:text-dark-300">
            <CheckSquare className="w-6 h-6" />
          </div>
        </div>

        {/* Card 3 */}
        <div className="bg-white dark:bg-dark-800 p-6 rounded-2xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium flex items-center justify-between">
          <div>
            <span className="block text-xs font-semibold text-slate-400 dark:text-dark-400 uppercase tracking-wider">Pending Tasks</span>
            <span className="block text-2xl font-extrabold text-amber-600 mt-1">{pendingCount}</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 dark:bg-amber-950 flex items-center justify-center text-amber-600 dark:text-amber-400">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        {/* Card 4 */}
        <div className="bg-white dark:bg-dark-800 p-6 rounded-2xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium flex items-center justify-between">
          <div>
            <span className="block text-xs font-semibold text-slate-400 dark:text-dark-400 uppercase tracking-wider">Completed</span>
            <span className="block text-2xl font-extrabold text-emerald-600 mt-1">{completedCount}</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-950 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Graphical charts and Audit Logs split view */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Chart 1 Card */}
        <div className="bg-white dark:bg-dark-800 p-6 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium flex flex-col items-center">
          <h3 className="text-sm font-bold text-slate-700 dark:text-white uppercase self-start mb-6 tracking-wide">Tasks Status</h3>
          <div className="w-full max-w-[200px]">
            <Doughnut data={statusChartData} options={{ plugins: { legend: { display: false } } }} />
          </div>
          <div className="grid grid-cols-2 gap-4 w-full mt-6 text-xs font-medium text-slate-500">
            <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-slate-400"></span>To Do</div>
            <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-sky-400"></span>In Progress</div>
            <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span>In Review</div>
            <div className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>Completed</div>
          </div>
        </div>

        {/* Chart 2 Card */}
        <div className="bg-white dark:bg-dark-800 p-6 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium">
          <h3 className="text-sm font-bold text-slate-700 dark:text-white uppercase mb-6 tracking-wide">Tasks Priority</h3>
          <div className="h-[200px] flex items-center justify-center">
            <Bar
              data={priorityChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { ticks: { precision: 0 } } },
              }}
            />
          </div>
        </div>

        {/* Audit Log Card */}
        <div className="bg-white dark:bg-dark-800 p-6 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium flex flex-col">
          <h3 className="text-sm font-bold text-slate-700 dark:text-white uppercase mb-6 tracking-wide">Audit Activity Timeline</h3>
          <div className="flex-1 overflow-y-auto max-h-[220px] space-y-4 pr-2">
            {hasPermission('audit:read') ? (
              auditLogs.length > 0 ? (
                auditLogs.map((log) => (
                  <div key={log.id} className="flex gap-3 text-xs leading-relaxed border-l-2 border-slate-200 dark:border-dark-700 pl-4 py-0.5 relative">
                    <span className="absolute -left-[5px] top-1.5 w-2.5 h-2.5 rounded-full bg-brand-500"></span>
                    <div>
                      <p className="font-semibold text-slate-800 dark:text-white">
                        {log.user?.full_name || 'System'} {log.action.toLowerCase()}d {log.entity_type.toLowerCase()}
                      </p>
                      {log.details && (
                        <p className="text-[10px] text-slate-400 dark:text-dark-400 mt-0.5">
                          {log.details.name || log.details.title || ''}
                        </p>
                      )}
                      <span className="text-[10px] text-slate-400 block mt-1">
                        {new Date(log.created_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-xs text-slate-400">No activity recorded.</div>
              )
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-center text-slate-400 gap-2">
                <AlertCircle className="w-8 h-8 text-slate-300" />
                <p className="text-xs">Security: You do not have permission to view activity logs.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
