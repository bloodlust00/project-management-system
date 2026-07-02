import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = async () => {
    try {
      const res = await api.get('/users/me');
      if (res.data?.success) {
        setUser(res.data.data);
      } else {
        logoutLocal();
      }
    } catch (err) {
      logoutLocal();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchProfile();
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    if (res.data?.success) {
      const { access_token, refresh_token, user: userData } = res.data.data;
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      setUser(userData);
      return true;
    }
    return false;
  };

  const register = async (email, password, fullName) => {
    const res = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName
    });
    return res.data?.success;
  };

  const logoutLocal = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  const logout = async () => {
    const rToken = localStorage.getItem('refresh_token');
    if (rToken) {
      try {
        await api.post('/auth/logout', { refresh_token: rToken });
      } catch (e) {
        // Log clean fail
      }
    }
    logoutLocal();
  };

  const hasPermission = (permissionCode) => {
    if (!user) return false;
    const roles = user.roles || [];
    // Admin bypasses all checks
    if (roles.some(r => r.name === 'Admin')) return true;
    
    // Check nested permissions codes
    return roles.some(r => 
      (r.permissions || []).some(p => p.code === permissionCode)
    );
  };

  const hasRole = (roleName) => {
    if (!user) return false;
    return (user.roles || []).some(r => r.name === roleName);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, hasPermission, hasRole }}>
      {children}
    </AuthContext.Provider>
  );
};
