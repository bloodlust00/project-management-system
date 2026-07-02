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
  ChevronLeft,
  ChevronRight,
  FolderOpen
} from 'lucide-react';

const Projects = () => {
  const { user, hasPermission } = useAuth();
  const { showToast } = useToast();

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  
  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  
  // Form fields
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [formLoading, setFormLoading] = useState(false);

  const fetchProjects = async () => {
    setLoading(true);
    try {
      const skip = (page - 1) * 6;
      const res = await api.get(`/projects/?skip=${skip}&limit=6&search=${search}`);
      if (res.data?.success) {
        setProjects(res.data.data.items);
        setTotal(res.data.data.pagination.total);
      }
    } catch (err) {
      showToast('Failed to load projects list', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [page, search]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setFormLoading(true);
    try {
      const res = await api.post('/projects/', { name, description });
      if (res.data?.success) {
        showToast('Project created successfully', 'success');
        setIsCreateOpen(false);
        setName('');
        setDescription('');
        fetchProjects();
      }
    } catch (err) {
      showToast(err.response?.data?.message || 'Failed to create project', 'error');
    } finally {
      setFormLoading(false);
    }
  };

  const handleEdit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setFormLoading(true);
    try {
      const res = await api.put(`/projects/${selectedProject.id}`, { name, description });
      if (res.data?.success) {
        showToast('Project updated successfully', 'success');
        setIsEditOpen(false);
        setSelectedProject(null);
        setName('');
        setDescription('');
        fetchProjects();
      }
    } catch (err) {
      showToast(err.response?.data?.message || 'Failed to update project', 'error');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this project? All associated tasks will be removed.')) return;

    try {
      const res = await api.delete(`/projects/${id}`);
      if (res.data?.success) {
        showToast('Project deleted successfully', 'success');
        fetchProjects();
      }
    } catch (err) {
      showToast(err.response?.data?.message || 'Failed to delete project', 'error');
    }
  };

  const openEditModal = (proj) => {
    setSelectedProject(proj);
    setName(proj.name);
    setDescription(proj.description || '');
    setIsEditOpen(true);
  };

  const canCreate = hasPermission('project:create');
  const canUpdate = hasPermission('project:update');
  const canDelete = hasPermission('project:delete');

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Top action bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        {/* Search */}
        <div className="relative w-full sm:max-w-xs">
          <span className="absolute inset-y-0 left-0 flex items-center pl-3.5 pointer-events-none text-slate-400">
            <Search className="w-5 h-5" />
          </span>
          <input
            type="text"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search projects..."
            className="block w-full pl-11 pr-4 py-2.5 text-sm text-slate-800 dark:text-white bg-white dark:bg-dark-800 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 outline-none shadow-sm transition-all"
          />
        </div>

        {/* Create project button */}
        {canCreate && (
          <button
            onClick={() => { setName(''); setDescription(''); setIsCreateOpen(true); }}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm rounded-xl shadow-premium shadow-brand-500/10 transition-all"
          >
            <Plus className="w-5 h-5" />
            Add Project
          </button>
        )}
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : projects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <div
              key={proj.id}
              className="bg-white dark:bg-dark-800 p-6 rounded-2xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium flex flex-col justify-between"
            >
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center text-indigo-500">
                    <FolderOpen className="w-5 h-5" />
                  </div>
                  <h3 className="font-bold text-slate-800 dark:text-white truncate">{proj.name}</h3>
                </div>
                <p className="text-xs text-slate-500 dark:text-dark-400 line-clamp-3 leading-relaxed mb-6">
                  {proj.description || 'No description provided.'}
                </p>
              </div>

              {/* Card Footer Actions */}
              <div className="flex items-center justify-between border-t border-slate-100 dark:border-dark-700 pt-4 text-xs font-semibold text-slate-400">
                <span className="truncate max-w-[100px]">Owner: {proj.owner?.full_name}</span>
                <div className="flex items-center gap-1">
                  {canUpdate && (
                    <button
                      onClick={() => openEditModal(proj)}
                      className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-dark-700 text-slate-500"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  )}
                  {canDelete && (
                    <button
                      onClick={() => handleDelete(proj.id)}
                      className="p-2 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/20 text-rose-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20 bg-white dark:bg-dark-800 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium">
          <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="font-bold text-slate-700 dark:text-white">No projects found</h3>
          <p className="text-xs text-slate-400 mt-1">Get started by creating a new workspace project</p>
        </div>
      )}

      {/* Pagination */}
      {total > 6 && (
        <div className="flex items-center justify-center gap-3 pt-6">
          <button
            onClick={() => setPage((p) => Math.max(p - 1, 1))}
            disabled={page === 1}
            className="p-2 rounded-lg border border-slate-200 dark:border-dark-700 hover:bg-slate-50 dark:hover:bg-dark-800 disabled:opacity-50 transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <span className="text-sm font-semibold text-slate-600 dark:text-dark-300">
            Page {page} of {Math.ceil(total / 6)}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(p + 1, Math.ceil(total / 6)))}
            disabled={page >= Math.ceil(total / 6)}
            className="p-2 rounded-lg border border-slate-200 dark:border-dark-700 hover:bg-slate-50 dark:hover:bg-dark-800 disabled:opacity-50 transition-colors"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Modal: Create/Edit Form */}
      {(isCreateOpen || isEditOpen) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white dark:bg-dark-800 rounded-3xl p-6 shadow-premium border border-slate-200/50 dark:border-dark-700/50 relative">
            <button
              onClick={() => { setIsCreateOpen(false); setIsEditOpen(false); }}
              className="absolute top-4 right-4 p-2 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-700"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-6">
              {isCreateOpen ? 'Create Project' : 'Edit Project'}
            </h3>
            
            <form onSubmit={isCreateOpen ? handleCreate : handleEdit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Project Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Website Redesign"
                  className="block w-full px-4 py-2.5 text-sm text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-500 dark:text-dark-400 uppercase tracking-wider mb-2">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Summarize project goals..."
                  rows={4}
                  className="block w-full px-4 py-2.5 text-sm text-slate-800 dark:text-white bg-slate-50 dark:bg-dark-900 border border-slate-200/60 dark:border-dark-700/60 rounded-xl focus:border-brand-500 outline-none"
                />
              </div>

              <button
                type="submit"
                disabled={formLoading}
                className="flex items-center justify-center gap-2 w-full py-3 bg-brand-500 hover:bg-brand-600 disabled:bg-brand-500/50 text-white font-semibold rounded-xl shadow-premium transition-all mt-6"
              >
                {formLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : isCreateOpen ? 'Create Project' : 'Save Changes'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Projects;
