import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  X,
  Loader2,
  FileSpreadsheet,
  Calendar,
  CheckCircle,
  Clock,
  User,
  AlertTriangle
} from 'lucide-react';

const Tasks = () => {
  const { user, hasPermission } = useAuth();
  const { showToast } = useToast();

  const [tasks, setTasks] = useState([]);
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedProject, setSelectedProject] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('');
  const [selectedAssignee, setSelectedAssignee] = useState('');

  // Modals state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  // Form fields
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [status, setStatus] = useState('TODO');
  const [priority, setPriority] = useState('MEDIUM');
  const [dueDate, setDueDate] = useState('');
  const [assigneeIds, setAssigneeIds] = useState([]);
  const [formLoading, setFormLoading] = useState(false);

  const fetchDropdownData = async () => {
    try {
      const projRes = await api.get('/projects/?limit=100');
      if (projRes.data?.success) setProjects(projRes.data.data.items);

      const usersRes = await api.get('/users/?limit=100');
      if (usersRes.data?.success) setUsers(usersRes.data.data.items);
    } catch (e) {
      // ignore
    }
  };

  const fetchTasks = async () => {
    setLoading(true);
    try {
      let query = `?limit=1000`;
      if (selectedProject) query += `&project_id=${selectedProject}`;
      if (selectedPriority) query += `&priority=${selectedPriority}`;
      if (selectedAssignee) query += `&assignee_id=${selectedAssignee}`;

      const res = await api.get(`/tasks/${query}`);
      if (res.data?.success) {
        setTasks(res.data.data.items);
      }
    } catch (err) {
      showToast('Failed to load tasks list', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDropdownData();
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [selectedProject, selectedPriority, selectedAssignee]);

  const handleExportCSV = async () => {
    try {
      const query = selectedProject ? `?project_id=${selectedProject}` : '';
      const response = await api.get(`/tasks/export/csv${query}`, { responseType: 'blob' });
      
      const blob = new Blob([response.data], { type: 'text/csv' });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      link.download = 'tasks_export.csv';
      link.click();
      showToast('CSV export downloaded successfully', 'success');
    } catch (err) {
      showToast('Failed to export tasks', 'error');
    }
  };

  const openCreateModal = () => {
    if (!selectedProject) {
      showToast('Please select a project filter before creating a task', 'warning');
      return;
    }
    setSelectedTask(null);
    setTitle('');
    setDescription('');
    setStatus('TODO');
    setPriority('MEDIUM');
    setDueDate('');
    setAssigneeIds([]);
    setIsModalOpen(true);
  };

  const openEditModal = (task) => {
    setSelectedTask(task);
    setTitle(task.title);
    setDescription(task.description || '');
    setStatus(task.status);
    setPriority(task.priority);
    setDueDate(task.due_date ? task.due_date.substring(0, 16) : '');
    setAssigneeIds(task.assignees.map(u => u.id));
    setIsModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormLoading(true);

    try {
      const payload = {
        title,
        description,
        status,
        priority,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        assignee_ids: assigneeIds
      };

      if (selectedTask) {
        // Enforce Employee role editing boundaries
        const userRoles = user.roles.map(r => r.name);
        const isMgr = userRoles.includes('Admin') || userRoles.includes('Manager');
        
        let updatePayload = payload;
        if (!isMgr) {
          // Employee: only submit status updates
          updatePayload = { status };
        }

        await api.put(`/tasks/${selectedTask.id}`, updatePayload);
        showToast('Task updated successfully', 'success');
      } else {
        await api.post(`/tasks/project/${selectedProject}`, payload);
        showToast('Task created successfully', 'success');
      }
      setIsModalOpen(false);
      fetchTasks();
    } catch (err) {
      showToast(err.response?.data?.message || 'Transaction failed', 'error');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return;
    try {
      await api.delete(`/tasks/${id}`);
      showToast('Task deleted successfully', 'success');
      fetchTasks();
    } catch (err) {
      showToast('Failed to delete task', 'error');
    }
  };

  // Group tasks by status columns
  const columns = {
    TODO: { name: 'To Do', color: 'border-t-slate-400 bg-slate-500/5' },
    IN_PROGRESS: { name: 'In Progress', color: 'border-t-sky-400 bg-sky-500/5' },
    REVIEW: { name: 'Under Review', color: 'border-t-amber-400 bg-amber-500/5' },
    DONE: { name: 'Completed', color: 'border-t-emerald-400 bg-emerald-500/5' }
  };

  const canCreate = hasPermission('task:create');
  const canDelete = hasPermission('task:delete');

  // Enforce Employee check for detail fields edit accessibility
  const isManagerOrAdmin = hasPermission('task:create');

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top Filter and Actions Bar */}
      <div className="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-4 bg-white dark:bg-dark-800 p-6 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 flex-1">
          {/* Project filter */}
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Project Space</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="block w-full px-3 py-2 text-xs text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-lg outline-none"
            >
              <option value="">All Projects</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>

          {/* Priority filter */}
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Priority</label>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="block w-full px-3 py-2 text-xs text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-lg outline-none"
            >
              <option value="">All Priorities</option>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </select>
          </div>

          {/* Assignee filter */}
          <div>
            <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">Assignee</label>
            <select
              value={selectedAssignee}
              onChange={(e) => setSelectedAssignee(e.target.value)}
              className="block w-full px-3 py-2 text-xs text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-lg outline-none"
            >
              <option value="">All Assignees</option>
              {users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
            </select>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCSV}
            className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-dark-700 dark:hover:bg-dark-600 text-slate-700 dark:text-white font-semibold text-xs rounded-xl transition-all"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            Export CSV
          </button>
          
          {canCreate && (
            <button
              onClick={openCreateModal}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white font-semibold text-xs rounded-xl shadow-premium shadow-brand-500/10 transition-all"
            >
              <Plus className="w-4 h-4" />
              Add Task
            </button>
          )}
        </div>
      </div>

      {/* Kanban Board columns */}
      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 overflow-x-auto pb-4">
          {Object.entries(columns).map(([colId, colMeta]) => {
            const columnTasks = tasks.filter((t) => t.status === colId);
            return (
              <div
                key={colId}
                className={`flex flex-col min-w-[250px] p-4 rounded-2xl border border-slate-200/40 dark:border-dark-700/40 border-t-4 ${colMeta.color}`}
              >
                {/* Column header */}
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-bold text-slate-600 dark:text-dark-300 uppercase tracking-wider">{colMeta.name}</span>
                  <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-slate-200/50 dark:bg-dark-700 text-slate-500">
                    {columnTasks.length}
                  </span>
                </div>

                {/* Task Cards list */}
                <div className="flex-1 space-y-4">
                  {columnTasks.map((task) => (
                    <div
                      key={task.id}
                      className="bg-white dark:bg-dark-800 p-4 rounded-xl border border-slate-200/50 dark:border-dark-700/50 shadow-sm hover:shadow-premium transition-all duration-200 group relative"
                    >
                      <h4 className="font-bold text-slate-800 dark:text-white text-xs mb-2 line-clamp-1">{task.title}</h4>
                      <p className="text-[10px] text-slate-400 dark:text-dark-400 line-clamp-2 leading-relaxed mb-4">
                        {task.description || 'No description provided.'}
                      </p>

                      {/* Info lines */}
                      <div className="space-y-1.5 border-t border-slate-100 dark:border-dark-700/50 pt-3">
                        {task.due_date && (
                          <div className="flex items-center gap-1.5 text-[9px] font-semibold text-slate-400">
                            <Calendar className="w-3 h-3 text-brand-400" />
                            {new Date(task.due_date).toLocaleDateString()}
                          </div>
                        )}
                        {/* Assignees badges */}
                        {task.assignees?.length > 0 && (
                          <div className="flex items-center gap-1 flex-wrap">
                            <User className="w-3 h-3 text-slate-400 flex-shrink-0" />
                            {task.assignees.map(u => (
                              <span key={u.id} className="text-[8px] font-bold px-1.5 py-0.5 rounded bg-slate-100 dark:bg-dark-900 text-slate-500">
                                {u.full_name.split(' ')[0]}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>

                      {/* Card hover actions */}
                      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                        <button
                          onClick={() => openEditModal(task)}
                          className="p-1 rounded bg-slate-100 dark:bg-dark-700 hover:bg-slate-200 text-slate-500"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                        {canDelete && (
                          <button
                            onClick={() => handleDelete(task.id)}
                            className="p-1 rounded bg-rose-50 dark:bg-rose-950/20 hover:bg-rose-100 text-rose-500"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                  {columnTasks.length === 0 && (
                    <div className="text-center py-10 border border-dashed border-slate-200 dark:border-dark-700 rounded-xl text-[10px] text-slate-400">
                      Empty column
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal: Create/Edit Task */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white dark:bg-dark-800 rounded-3xl p-6 shadow-premium border border-slate-200/50 dark:border-dark-700/50 relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 p-2 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-700"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-6">
              {selectedTask ? 'Task Configuration' : 'Create Task'}
            </h3>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* If Employee is editing, detail fields are disabled */}
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Write backend seeds"
                  className="block w-full px-4 py-2.5 text-sm text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 outline-none disabled:opacity-60"
                  disabled={selectedTask && !isManagerOrAdmin}
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Write clear instructions..."
                  rows={3}
                  className="block w-full px-4 py-2.5 text-sm text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 outline-none disabled:opacity-60"
                  disabled={selectedTask && !isManagerOrAdmin}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Priority */}
                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Priority</label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="block w-full px-3 py-2 text-xs text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-lg outline-none disabled:opacity-60"
                    disabled={selectedTask && !isManagerOrAdmin}
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                  </select>
                </div>

                {/* Status */}
                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Status</label>
                  <select
                    value={status}
                    onChange={(e) => setStatus(e.target.value)}
                    className="block w-full px-3 py-2 text-xs text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-lg outline-none"
                  >
                    <option value="TODO">To Do</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="REVIEW">Under Review</option>
                    <option value="DONE">Completed</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Due Date</label>
                <input
                  type="datetime-local"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="block w-full px-4 py-2.5 text-xs text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 outline-none disabled:opacity-60"
                  disabled={selectedTask && !isManagerOrAdmin}
                />
              </div>

              {/* Assignees multi select */}
              {isManagerOrAdmin && (
                <div>
                  <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Assignees</label>
                  <select
                    multiple
                    value={assigneeIds}
                    onChange={(e) => setAssigneeIds(Array.from(e.target.selectedOptions, option => option.value))}
                    className="block w-full px-3 py-2.5 text-xs text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-lg outline-none h-24"
                  >
                    {users.map((u) => <option key={u.id} value={u.id}>{u.full_name}</option>)}
                  </select>
                  <span className="text-[10px] text-slate-400 block mt-1">Hold Ctrl/Cmd to select multiple members.</span>
                </div>
              )}

              {/* Employee notification banner inside edit modal */}
              {selectedTask && !isManagerOrAdmin && (
                <div className="flex gap-2 p-3 bg-amber-50 dark:bg-amber-950/20 text-[10px] leading-relaxed text-amber-800 dark:text-amber-300 rounded-xl border border-amber-500/10">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <p>Security limit: As an Employee, you can only edit the status parameter of your assigned task tasks.</p>
                </div>
              )}

              <button
                type="submit"
                disabled={formLoading}
                className="flex items-center justify-center gap-2 w-full py-3 bg-brand-500 hover:bg-brand-600 disabled:bg-brand-500/50 text-white font-semibold rounded-xl shadow-premium transition-all mt-6"
              >
                {formLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : selectedTask ? 'Save Updates' : 'Add Task'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tasks;
