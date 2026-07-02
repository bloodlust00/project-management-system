import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { useToast } from '../contexts/ToastContext';
import { ShieldAlert, Trash2, Edit, X, Check, Loader2 } from 'lucide-react';

const AdminPanel = () => {
  const { showToast } = useToast();
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // Modals state
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [formLoading, setFormLoading] = useState(false);

  const fetchUsersAndRoles = async () => {
    setLoading(true);
    try {
      const usersRes = await api.get('/users/?limit=100');
      if (usersRes.data?.success) setUsers(usersRes.data.data.items);

      const rolesRes = await api.get('/rbac/roles');
      if (rolesRes.data?.success) setRoles(rolesRes.data.data);
    } catch (err) {
      showToast('Failed to load user records', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsersAndRoles();
  }, []);

  const handleRoleUpdate = async (e) => {
    e.preventDefault();
    if (selectedRoles.length === 0) {
      showToast('Select at least one role', 'warning');
      return;
    }

    setFormLoading(true);
    try {
      const res = await api.put(`/users/${selectedUser.id}/roles`, {
        role_names: selectedRoles,
      });

      if (res.data?.success) {
        showToast('User roles updated successfully!', 'success');
        setIsEditOpen(false);
        fetchUsersAndRoles();
      }
    } catch (err) {
      showToast('Failed to modify user roles', 'error');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to deactivate/soft-delete this user account?')) return;

    try {
      const res = await api.delete(`/users/${userId}`);
      if (res.data?.success) {
        showToast('User deleted successfully', 'success');
        fetchUsersAndRoles();
      }
    } catch (err) {
      showToast('Failed to delete user account', 'error');
    }
  };

  const openRoleEditModal = (u) => {
    setSelectedUser(u);
    setSelectedRoles(u.roles.map(r => r.name));
    setIsEditOpen(true);
  };

  const handleCheckboxChange = (roleName) => {
    setSelectedRoles((prev) =>
      prev.includes(roleName)
        ? prev.filter((r) => r !== roleName)
        : [...prev, roleName]
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-dark-800 rounded-3xl border border-slate-200/50 dark:border-dark-700/50 shadow-premium p-6 md:p-8 animate-fade-in">
      <div className="flex items-center gap-2 mb-6">
        <ShieldAlert className="w-5 h-5 text-brand-500" />
        <h3 className="text-sm font-bold text-slate-700 dark:text-white uppercase tracking-wide">Users RBAC Directory</h3>
      </div>

      {/* Users table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-100 dark:border-dark-700/60 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
              <th className="pb-4 pl-4">Full Name</th>
              <th className="pb-4">Email</th>
              <th className="pb-4">Active Roles</th>
              <th className="pb-4 pr-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-dark-700/30 text-xs font-semibold text-slate-700 dark:text-dark-200">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-slate-50/50 dark:hover:bg-dark-950/20">
                <td className="py-4 pl-4">{u.full_name}</td>
                <td className="py-4 text-slate-500 dark:text-dark-400 font-normal">{u.email}</td>
                <td className="py-4">
                  <div className="flex gap-1.5 flex-wrap">
                    {u.roles?.map((r) => (
                      <span
                        key={r.id}
                        className="text-[9px] font-extrabold px-2 py-0.5 rounded-full bg-brand-50 dark:bg-brand-950 text-brand-600 dark:text-brand-400 uppercase tracking-wide border border-brand-200/20"
                      >
                        {r.name}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-4 pr-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => openRoleEditModal(u)}
                      className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-dark-700 text-slate-500"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => handleDeleteUser(u.id)}
                      className="p-2 rounded-lg hover:bg-rose-50 dark:hover:bg-rose-950/20 text-rose-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal: Edit Roles */}
      {isEditOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-white dark:bg-dark-800 rounded-3xl p-6 shadow-premium border border-slate-200/50 dark:border-dark-700/50 relative">
            <button
              onClick={() => setIsEditOpen(false)}
              className="absolute top-4 right-4 p-2 rounded-lg text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-700"
            >
              <X className="w-5 h-5" />
            </button>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">Configure User Roles</h3>
            <p className="text-[10px] text-slate-400 mb-6">Updating permissions structure for {selectedUser?.full_name}</p>

            <form onSubmit={handleRoleUpdate} className="space-y-6">
              <div className="space-y-3">
                {roles.map((role) => (
                  <label
                    key={role.id}
                    className="flex items-center gap-3 p-3 rounded-xl border border-slate-200/60 dark:border-dark-700/60 hover:bg-slate-50 dark:hover:bg-dark-900 cursor-pointer"
                  >
                    <input
                      type="checkbox"
                      checked={selectedRoles.includes(role.name)}
                      onChange={() => handleCheckboxChange(role.name)}
                      className="w-4 h-4 text-brand-500 border-slate-300 rounded focus:ring-brand-500"
                    />
                    <div>
                      <p className="text-xs font-bold text-slate-700 dark:text-white">{role.name}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">{role.description}</p>
                    </div>
                  </label>
                ))}
              </div>

              <button
                type="submit"
                disabled={formLoading}
                className="flex items-center justify-center gap-2 w-full py-3.5 bg-brand-500 hover:bg-brand-600 disabled:bg-brand-500/50 text-white font-semibold rounded-xl shadow-premium transition-all"
              >
                {formLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Save Roles Configuration'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
