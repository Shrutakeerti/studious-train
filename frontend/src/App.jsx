// eslint-disable-next-line no-unused-vars
import { AnimatePresence, motion } from "framer-motion";
import { Link, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import HomePage from "./components/HomePage.jsx";
import Login from "./components/Login.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import SessionDetail from "./components/SessionDetail.jsx";
import Signup from "./components/Signup.jsx";
import { useAuth } from "./context/AuthContext.jsx";

function PageTransition({ children }) {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -6 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

export default function App() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="brand">
          <span className="brand-mark">ZY</span>
          <span className="brand-name">Research Copilot</span>
        </Link>
        <span className="brand-tagline">Your sellers run the conversation. We do everything else.</span>
        <div className="header-auth">
          {user ? (
            <>
              <span className="header-user">{user.name || user.email}</span>
              <button
                className="btn btn-ghost"
                onClick={() => {
                  logout();
                  navigate("/login");
                }}
              >
                Log out
              </button>
            </>
          ) : (
            <Link className="btn btn-ghost" to="/login">
              Sign in
            </Link>
          )}
        </div>
      </header>
      <main className="app-main">
        <PageTransition>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <HomePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/sessions/:sessionId"
              element={
                <ProtectedRoute>
                  <SessionDetail />
                </ProtectedRoute>
              }
            />
            <Route
              path="*"
              element={
                <div>
                  <p>Page not found.</p>
                  <Link to="/">Return home</Link>
                </div>
              }
            />
          </Routes>
        </PageTransition>
      </main>
    </div>
  );
}