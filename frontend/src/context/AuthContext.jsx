import { createContext, useContext, useEffect, useState } from "react";
import { api, setAuthToken } from "../api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const initialToken = localStorage.getItem("zy_token");
  const [token, setToken] = useState(() => initialToken);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(() => initialToken !== null);

  useEffect(() => {
    setAuthToken(token);
    if (!token) {
      return;
    }
    api
      .me()
      .then(setUser)
      .catch(() => {
        setToken(null);
        localStorage.removeItem("zy_token");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, [token]);

  function persistSession(accessToken, userData) {
    localStorage.setItem("zy_token", accessToken);
    setAuthToken(accessToken);
    setToken(accessToken);
    setUser(userData);
  }

  async function login(email, password) {
    const data = await api.login({ email, password });
    persistSession(data.access_token, data.user);
  }

  async function signup(name, email, password) {
    const data = await api.signup({ name, email, password });
    persistSession(data.access_token, data.user);
  }

  function logout() {
    localStorage.removeItem("zy_token");
    setAuthToken(null);
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}