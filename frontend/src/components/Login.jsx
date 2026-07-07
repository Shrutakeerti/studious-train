import { motion } from "framer-motion";
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { ErrorBanner } from "./Common.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(email, password);
      navigate(location.state?.from?.pathname || "/", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <motion.div
        className="auth-card"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: "easeOut" }}
      >
        <p className="auth-eyebrow">$ zylabs auth login</p>
        <h1 className="auth-title">Welcome back</h1>
        <p className="auth-sub">Sign in to pick up your research sessions.</p>

        <ErrorBanner message={error} />

        <form onSubmit={onSubmit} className="auth-form">
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </label>
          <motion.button
            whileTap={{ scale: 0.97 }}
            className="btn btn-primary auth-submit"
            type="submit"
            disabled={busy}
          >
            {busy ? "Signing in…" : "Sign in"}
          </motion.button>
        </form>

        <p className="auth-switch">
          No account yet? <Link to="/signup">Create one</Link>
        </p>
      </motion.div>
    </div>
  );
}