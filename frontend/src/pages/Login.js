import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import LoadingSpinner from "../components/LoadingSpinner";
import { login } from "../services/auth";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [keepSignedIn, setKeepSignedIn] = useState(true);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Listen for messages from the Google login popup
  React.useEffect(() => {
    const handleMessage = (event) => {
      if (event.data && event.data.type === 'GOOGLE_LOGIN_SUCCESS') {
        // Handle successful Google login
        console.log('Google login successful:', event.data.user);
        
        // Store complete user object
        localStorage.setItem('user', JSON.stringify({
          id: event.data.user.userId,
          email: event.data.user.email,
          displayName: event.data.user.displayName,
          token: event.data.user.token
        }));
        localStorage.setItem('token', event.data.user.token);
        localStorage.setItem('refresh_token', event.data.user.refreshToken);
        
        // Navigate to courses
        navigate("/courses");
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [navigate]);
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const loginResp = await login(email, password);
      navigate("/courses");
    } catch (err) {
      setError(err.detail || "Login failed. Please check credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    try {
      setLoading(true);
      // Open Google login in a new tab with proper opener reference
      const loginUrl = `${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/google-login`;
      const popup = window.open(loginUrl, '_blank', 'width=500,height=600,scrollbars=yes,resizable=yes');
      
      if (!popup) {
        setError("Popup blocked. Please allow popups for this site.");
        setLoading(false);
        return;
      }
      
      setLoading(false);
    } catch (err) {
      setError("Google login failed. Please try again.");
      setLoading(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f7f7f7", display: "flex", justifyContent: "center", alignItems: "center" }}>
      <div style={{
        background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px #0002", padding: 40,
        minWidth: 370, maxWidth: 380, margin: 24, display: "flex", flexDirection: "column", alignItems: "center"
      }}>
        {/* App Icon and Title */}
        <div style={{ display: "flex", alignItems: "center", marginBottom: 24 }}>
          <div style={{
            background: "#2563eb", color: "#fff", borderRadius: 8,
            width: 36, height: 36, display: "flex", alignItems: "center",
            justifyContent: "center", fontWeight: 700, fontSize: 22, marginRight: 12
          }}>
            C
          </div>
          <span style={{ fontWeight: 600, fontSize: 20, color: "#222" }}>Course Copilot</span>
        </div>

        {/* Google Sign-In (Placeholder Only) */}
        <button
          type="button"
          style={{
            width: "100%", background: "#fff", color: "#222", border: "1px solid #ddd",
            borderRadius: 6, padding: "10px 0", fontWeight: 500, fontSize: 16,
            cursor: loading ? "not-allowed" : "pointer", boxShadow: "0 1px 2px #0001",
            display: "flex", alignItems: "center", justifyContent: "center", gap: 8, marginBottom: 24
          }}
          disabled={loading}
          onClick={handleGoogleLogin}
        >
          <svg width="20" height="20" viewBox="0 0 48 48" style={{ marginRight: 8 }}>
            {/* Google Icon */}
            <g><path fill="#4285F4" d="M24 9.5c3.54 0 6.7 1.22 9.19 3.23l6.85-6.85C36.68 2.36 30.74 0 24 0 14.82 0 6.71 5.1 2.69 12.44l8.01 6.22C12.6 13.13 17.88 9.5 24 9.5z" />
              <path fill="#34A853" d="M46.1 24.55c0-1.64-.15-3.22-.42-4.74H24v9.01h12.42c-.54 2.9-2.18 5.36-4.64 7.02l7.19 5.6C43.93 37.13 46.1 31.36 46.1 24.55z" />
              <path fill="#FBBC05" d="M10.7 28.66c-1.01-2.99-1.01-6.33 0-9.32l-8.01-6.22C.68 17.1 0 20.47 0 24c0 3.53.68 6.9 2.69 10.88l8.01-6.22z" />
              <path fill="#EA4335" d="M24 48c6.48 0 11.92-2.15 15.89-5.86l-7.19-5.6c-2.01 1.35-4.6 2.16-8.7 2.16-6.12 0-11.4-3.63-13.3-8.88l-8.01 6.22C6.71 42.9 14.82 48 24 48z" />
              <path fill="none" d="M0 0h48v48H0z" />
            </g>
          </svg>
          Sign in with Google
        </button>

        {/* Email/Password Form */}
        {loading ? (
          <LoadingSpinner />
        ) : (
          <form onSubmit={handleSubmit} style={{ width: "100%" }}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontWeight: 500, fontSize: 14, color: "#444" }}>Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                disabled={loading}
                style={{ width: "100%", padding: "10px 12px", border: "1px solid #ddd", borderRadius: 6, marginTop: 6, fontSize: 15 }}
              />
            </div>
            <div style={{ marginBottom: 8, position: "relative" }}>
              <label style={{ fontWeight: 500, fontSize: 14, color: "#444" }}>Password</label>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                disabled={loading}
                style={{ width: "100%", padding: "10px 12px", border: "1px solid #ddd", borderRadius: 6, marginTop: 6, fontSize: 15 }}
              />
              <span
                style={{
                  position: "absolute", right: 12, top: 36, fontSize: 13, color: "#2563eb",
                  cursor: "pointer", userSelect: "none", fontWeight: 500
                }}
                onClick={() => setShowPassword(s => !s)}
              >
                {showPassword ? "HIDE" : "SHOW"}
              </span>
            </div>

            {/* Remember me and Forgot password */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 18 }}>
              <label style={{ display: "flex", alignItems: "center", fontSize: 15, color: "#444", fontWeight: 500 }}>
                <input
                  type="checkbox"
                  checked={keepSignedIn}
                  onChange={e => setKeepSignedIn(e.target.checked)}
                  style={{ marginRight: 8, accentColor: "#2563eb" }}
                />
                Keep me signed in
              </label>
              <Link to="/forgot-password" style={{ color: "#2563eb", fontSize: 14, textDecoration: "none", fontWeight: 400 }}>Forgot password?</Link>
            </div>

            {/* Error Display */}
            {error && <div style={{ color: "red", marginBottom: 8 }}>{error}</div>}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              style={{
                width: "100%", background: "#2563eb", color: "#fff",
                border: "none", borderRadius: 8, padding: "12px 0",
                fontWeight: 600, fontSize: 17,
                cursor: loading ? "not-allowed" : "pointer", boxShadow: "0 1px 2px #0001"
              }}
            >
              Sign in
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
