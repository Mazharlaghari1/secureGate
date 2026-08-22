import React, { createContext, useState, useEffect, useContext } from 'react';
import api, { setAuthToken, registerUnauthorizedHandler } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [token, setTokenState] = useState(() => localStorage.getItem('token') || '');
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [initializing, setInitializing] = useState(true);

  const logout = (wasExpired = false) => {
    setUser(null);
    setTokenState('');
    setAuthToken('');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    if (wasExpired) {
      window.location.href = '/login?expired=true';
    }
  };

  const login = async (email, password) => {
    try {
      const res = await api.post('/api/auth/login', { email, password });
      // The API returns structure: { success: true, data: { token: "JWT", user: { name, email, role } } }
      const { token: jwtToken, user: userData } = res.data.data;
      setTokenState(jwtToken);
      setAuthToken(jwtToken);
      setUser(userData);
      localStorage.setItem('token', jwtToken);
      localStorage.setItem('user', JSON.stringify(userData));
      return { success: true, user: userData };
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.error?.message || 'Login failed.'
      };
    }
  };

  useEffect(() => {
    const verifyToken = async () => {
      const storedToken = localStorage.getItem('token');
      if (storedToken) {
        setAuthToken(storedToken);
        try {
          const res = await api.get('/api/auth/me');
          setUser(res.data.data);
          localStorage.setItem('user', JSON.stringify(res.data.data));
        } catch (err) {
          console.error('Session restoration failed:', err);
          logout(true);
        }
      } else {
        logout(false);
      }
      setInitializing(false);
    };

    verifyToken();

    registerUnauthorizedHandler(() => {
      logout(true);
    });
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, token, login, logout, initializing }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
export default AuthContext;
