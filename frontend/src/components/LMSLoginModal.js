import React, { useState } from "react";
import Modal from "./Modal";

export default function LMSLoginModal({ open, onClose, onLoginSuccess }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [courses, setCourses] = useState([]);
  const [showCourses, setShowCourses] = useState(false);
  const [fetchingCourses, setFetchingCourses] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate inputs
    if (!email || !password) {
      setError("Please enter both email and password");
      return;
    }

    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const token = localStorage.getItem("token");
      
      // ========================================
      // BACKEND INTEGRATION REQUIRED
      // ========================================
      // 
      // ENDPOINT: POST /api/login-lms
      // 
      // REQUEST HEADERS:
      // - Authorization: Bearer <user_auth_token>
      // - Content-Type: application/json
      // 
      // REQUEST BODY:
      // {
      //   "email": "user@example.com",
      //   "password": "userpassword"
      // }
      // 
      // EXPECTED SUCCESS RESPONSE (200):
      // {
      //   "message": "Successfully logged into LMS",
      //   "data": {
      //     "token": "lms_jwt_token_from_platform",
      //     "user": {
      //       "id": "lms_user_id",
      //       "email": "user@example.com",
      //       "name": "User Name"
      //     }
      //   }
      // }
      // 
      // EXPECTED ERROR RESPONSES:
      // - 400: { "detail": "Email and password are required" }
      // - 401: { "detail": "LMS authentication failed" }
      // - 422: { "detail": "Invalid email format" }
      // - 500: { "detail": "LMS base URL is not configured" }
      // - 503: { "detail": "Connection error - Could not connect to LMS server" }
      // 
      // BACKEND IMPLEMENTATION NOTES:
      // 1. Validate email format and required fields
      // 2. Extract user_id from Authorization token (already implemented)
      // 3. Call LMS platform authentication endpoint
      // 4. Handle LMS-specific response format
      // 5. Return standardized response format
      // 6. Implement proper error handling for all scenarios
      // 
      const response = await fetch(
        `${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/login-lms`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            email: email.trim(),
            password: password
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error("❌ LMS Login Error:", errorData);
        const errorMessage = errorData.detail || errorData.message || 'Login failed. Please check your credentials.';
        throw new Error(errorMessage);
      }

      const data = await response.json();
      
      // Store LMS cookies (for session-based auth) and user data
      const lmsCookies = data.cookies || "";
      const lmsUser = data.data?.user || data.user || {};
      const lmsToken = data.token || data.data?.token || "";  // Some APIs might also return a token
      
      localStorage.setItem("lms_cookies", lmsCookies);
      localStorage.setItem("lms_user", JSON.stringify(lmsUser));
      if (lmsToken) {
        localStorage.setItem("lms_token", lmsToken);
      }
      
      console.log("✅ LMS Login Success:", { 
        cookies: lmsCookies ? lmsCookies.substring(0, 50) + "..." : "none",
        token: lmsToken ? lmsToken.substring(0, 30) + "..." : "none",
        user: lmsUser 
      });
      
      // Check if in mock mode
      const isMockMode = data.message?.includes("MOCK MODE");
      if (isMockMode) {
        console.log("⚠️ Running in MOCK MODE - LMS_BASE_URL not configured in backend");
      }
      
      // Automatically fetch LMS courses after successful login
      if (lmsCookies) {
        setFetchingCourses(true);
        try {
          console.log("📚 Fetching LMS courses...");
          
          const coursesResponse = await fetch(
            `${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/courses-lms`,
            {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
              },
              body: JSON.stringify({
                lms_cookies: lmsCookies
              })
            }
          );

          if (coursesResponse.ok) {
            const coursesData = await coursesResponse.json();
            // Normalize various possible response shapes from backend/LMS
            const fetchedCourses = Array.isArray(coursesData)
              ? coursesData
              : (coursesData.data || coursesData.courses || coursesData.results || []);
            
            console.log("✅ LMS Courses fetched successfully!");
            console.log(`📊 Found ${fetchedCourses.length} courses:`, fetchedCourses);
            
            // Log course names for visibility
            if (fetchedCourses.length > 0) {
              fetchedCourses.forEach((course, index) => {
                console.log(`  ${index + 1}. ${course.name || course.title || 'Unnamed Course'} (ID: ${course.id})`);
              });
            }
            
            // Store courses in localStorage for later use
            localStorage.setItem("lms_courses", JSON.stringify(fetchedCourses));
            
            // Show courses in the modal
            setCourses(fetchedCourses);
            setShowCourses(true);
            setFetchingCourses(false);
          } else {
            const errorData = await coursesResponse.json().catch(() => ({}));
            console.error("⚠️ Failed to fetch LMS courses:", errorData);
            setError(errorData.detail || 'Failed to fetch courses from LMS');
            setFetchingCourses(false);
          }
        } catch (err) {
          console.error("⚠️ Error fetching LMS courses:", err);
          setError(err.message || 'Failed to fetch courses');
          setFetchingCourses(false);
        }
      }
    } catch (err) {
      console.error('LMS login error:', err);
      setError(err.message || 'Failed to login to LMS. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading && !fetchingCourses) {
      setEmail("");
      setPassword("");
      setError("");
      setCourses([]);
      setShowCourses(false);
      onClose();
    }
  };


  if (!open) return null;

  return (
    <Modal open={open} onClose={handleClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: 20, minWidth: 500 }}>
        
        {/* Show Login Form */}
        {!showCourses && (
          <>
            {/* Header */}
            <div>
              <div style={{ fontWeight: 700, fontSize: 24, marginBottom: 8, color: "#111827" }}>
                🔐 Login to LMS
              </div>
              <div style={{ fontSize: 14, color: "#6b7280" }}>
                Enter your LMS credentials to see available courses
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Error Message */}
          {error && (
            <div style={{
              background: "#fee2e2",
              border: "1px solid #fecaca",
              color: "#b91c1c",
              padding: "12px 14px",
              borderRadius: 8,
              fontSize: 14,
              display: "flex",
              alignItems: "center",
              gap: 8
            }}>
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* Email Field */}
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontWeight: 600, fontSize: 14, color: "#374151" }}>
              Email Address <span style={{ color: "#ef4444" }}>*</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your.email@example.com"
              disabled={loading}
              style={{
                padding: "10px 14px",
                border: "1px solid #d1d5db",
                borderRadius: 8,
                fontSize: 14,
                outline: "none",
                transition: "border-color 0.2s",
                background: loading ? "#f9fafb" : "#fff",
                cursor: loading ? "not-allowed" : "text"
              }}
              onFocus={(e) => e.target.style.borderColor = "#2563eb"}
              onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
            />
          </div>

          {/* Password Field */}
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontWeight: 600, fontSize: 14, color: "#374151" }}>
              Password <span style={{ color: "#ef4444" }}>*</span>
            </label>
            <div style={{ position: "relative" }}>
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                disabled={loading}
                style={{
                  width: "100%",
                  padding: "10px 40px 10px 14px",
                  border: "1px solid #d1d5db",
                  borderRadius: 8,
                  fontSize: 14,
                  outline: "none",
                  transition: "border-color 0.2s",
                  background: loading ? "#f9fafb" : "#fff",
                  cursor: loading ? "not-allowed" : "text",
                  boxSizing: "border-box"
                }}
                onFocus={(e) => e.target.style.borderColor = "#2563eb"}
                onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                disabled={loading}
                style={{
                  position: "absolute",
                  right: 10,
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  cursor: loading ? "not-allowed" : "pointer",
                  fontSize: 18,
                  color: "#6b7280",
                  padding: 4
                }}
                title={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "👁️" : "👁️‍🗨️"}
              </button>
            </div>
          </div>

          {/* Buttons */}
          <div style={{ display: "flex", justifyContent: "flex-end", gap: 12, marginTop: 8 }}>
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              style={{
                padding: "10px 20px",
                borderRadius: 8,
                border: "1px solid #d1d5db",
                background: "#fff",
                color: "#374151",
                fontWeight: 500,
                fontSize: 14,
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.5 : 1,
                transition: "all 0.2s"
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !email || !password}
              style={{
                padding: "10px 24px",
                borderRadius: 8,
                border: "none",
                background: (loading || !email || !password) ? "#94a3b8" : "#2563eb",
                color: "#fff",
                fontWeight: 600,
                fontSize: 14,
                cursor: (loading || !email || !password) ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: 8,
                transition: "all 0.2s"
              }}
            >
              {loading ? (
                <>
                  <div style={{
                    width: 16,
                    height: 16,
                    border: "2px solid #fff",
                    borderTop: "2px solid transparent",
                    borderRadius: "50%",
                    animation: "spin 1s linear infinite"
                  }}></div>
                  <span>Logging in...</span>
                </>
              ) : (
                <span>Login to LMS</span>
              )}
            </button>
          </div>
        </form>

        {/* Spinner Animation */}
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
          </>
        )}

        {/* Show Courses List */}
        {showCourses && (
          <>
            {/* Header */}
            <div>
              <div style={{ fontWeight: 700, fontSize: 24, marginBottom: 8, color: "#111827" }}>
                📚 LMS Courses
              </div>
              <div style={{ fontSize: 14, color: "#6b7280" }}>
                Found {courses.length} course{courses.length !== 1 ? 's' : ''} in your LMS
              </div>
            </div>

            {/* Fetching Courses Loader */}
            {fetchingCourses && (
              <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                <div style={{
                  width: 48,
                  height: 48,
                  border: "4px solid #e5e7eb",
                  borderTop: "4px solid #2563eb",
                  borderRadius: "50%",
                  animation: "spin 1s linear infinite",
                  margin: '0 auto 16px auto'
                }}></div>
                <div style={{ fontSize: 15, fontWeight: 600, color: "#2563eb" }}>
                  Loading courses...
                </div>
              </div>
            )}
            {/* Courses List (cards with Name and ID only) */}
            {!fetchingCourses && courses.length > 0 && (
              <div style={{
                maxHeight: '420px',
                overflowY: 'auto',
                border: '1px solid #e5e7eb',
                borderRadius: 10,
                background: '#fafbfc',
                padding: 10
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 10 }}>
                  {courses.map((course, index) => (
                    <div
                      key={course.id || index}
                      onClick={() => {
                        console.log('Course selected in login modal:', course);
                        onLoginSuccess({ courses: [course] });
                      }}
                      style={{
                        background: '#fff',
                        borderRadius: 10,
                        padding: 14,
                        border: '1px solid #e5e7eb',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = '#2563eb';
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(37, 99, 235, 0.1)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = '#e5e7eb';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <div style={{ fontSize: 16, fontWeight: 700, color: '#2563eb' }}>
                          {course.name || `Course ${index + 1}`}
                        </div>
                        <div style={{ fontSize: 13, color: '#374151' }}>
                          ID: <span style={{ fontFamily: 'monospace' }}>{course.id || '-'}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No Courses Message */}
            {!fetchingCourses && courses.length === 0 && (
              <div style={{ 
                padding: '40px 20px',
                textAlign: 'center',
                color: '#6b7280',
                fontSize: 14
              }}>
                No courses found in your LMS.
              </div>
            )}

            {/* Close Button */}
            {!fetchingCourses && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
                <button
                  onClick={handleClose}
                  style={{
                    padding: "10px 20px",
                    borderRadius: 8,
                    border: "1px solid #d1d5db",
                    background: "#fff",
                    color: "#374151",
                    fontWeight: 600,
                    fontSize: 15,
                    cursor: "pointer",
                    transition: "all 0.2s"
                  }}
                  onMouseEnter={(e) => e.target.style.background = "#f9fafb"}
                  onMouseLeave={(e) => e.target.style.background = "#fff"}
                >
                  Close
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </Modal>
  );
}

