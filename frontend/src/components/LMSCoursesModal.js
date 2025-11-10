import React, { useState, useEffect } from "react";
import Modal from "./Modal";

export default function LMSCoursesModal({
  open,
  onClose,
  onCourseSelected
}) {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isGridView, setIsGridView] = useState(true);
  
  console.log('LMSCoursesModal render - isGridView:', isGridView, 'courses:', courses.length);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCourseId, setSelectedCourseId] = useState(null);

  useEffect(() => {
    if (open) {
      fetchLMSCourses();
      setSelectedCourseId(null);
    }
  }, [open]);

  const fetchLMSCourses = async () => {
    try {
      setLoading(true);
      setError("");
      
      // ========================================
      // LMS COURSES FETCH - COOKIE AUTHENTICATION
      // ========================================
      // 
      // ENDPOINT: POST /api/courses-lms
      // 
      // REQUEST HEADERS:
      // - Authorization: Bearer <user_auth_token>
      // - Content-Type: application/json
      // 
      // REQUEST BODY:
      // {
      //   "lms_cookies": "session=abc123; Path=/; HttpOnly"
      // }
      // 
      // EXPECTED SUCCESS RESPONSE (200):
      // {
      //   "message": "Successfully fetched courses from LMS",
      //   "data": [
      //     {
      //       "id": "course_id_123",
      //       "name": "Introduction to Machine Learning",
      //       "code": "CS101",
      //       "description": "Course description here...",
      //       "start_date": "2024-01-15",
      //       "end_date": "2024-05-20",
      //       "enrollment_count": 45,
      //       "status": "active",
      //       "instructor": "Dr. Jane Smith",
      //       "created_at": "2024-01-01T00:00:00Z",
      //       "updated_at": "2024-01-10T00:00:00Z"
      //     }
      //   ]
      // }
      // 
      // BACKEND IMPLEMENTATION:
      // 1. Validate LMS cookies from request body
      // 2. Call LMS platform API using Cookie header
      // 3. Transform LMS response to match expected format
      // 4. Return formatted courses list
      
      const token = localStorage.getItem("token");
      const lmsCookies = localStorage.getItem("lms_cookies");

      if (!lmsCookies) {
        throw new Error("LMS cookies not found. Please login to LMS first.");
      }

      const response = await fetch(
        `${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/api/courses-lms`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            lms_cookies: lmsCookies
          })
        }
      );

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("LMS session expired. Please login again.");
        }
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to fetch courses');
      }

      const data = await response.json();
      const normalized = Array.isArray(data) ? data : (data.data || data.courses || data.results || []);
      console.log('LMS Courses fetched:', normalized);
      setCourses(normalized);
      
    } catch (err) {
      console.error('Error fetching LMS courses:', err);
      setError(err.message || 'Failed to load courses from LMS');
    } finally {
      setLoading(false);
    }
  };

  const handleCourseSelect = (courseId) => {
    console.log('Course selected:', courseId);
    setSelectedCourseId(courseId);
  };

  const handleProceedWithExport = () => {
    if (!selectedCourseId) return;
    
    const selectedCourse = courses.find(c => c.id === selectedCourseId);
    onCourseSelected(selectedCourse);
  };

  const handleCreateNewCourse = () => {
    // Pass null to indicate creating a new course
    onCourseSelected(null);
  };

  // Filter courses based on search query
  const filteredCourses = courses.filter(course => 
    course.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (course.code || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
    (course.instructor || "").toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (!open) return null;

  return (
    <Modal open={open} onClose={onClose}>
      <div style={{ display: "flex", flexDirection: "column", gap: 16, position: "relative", minHeight: 400 }}>
        
        {/* Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ fontWeight: 700, fontSize: 22 }}>Select LMS Course</div>
          {!loading && !error && (
            <div style={{ display: "flex", gap: 8 }}>
              <button
                onClick={() => setIsGridView(true)}
                style={{
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: "1px solid #d1d5db",
                  background: isGridView ? "#2563eb" : "#fff",
                  color: isGridView ? "#fff" : "#222",
                  cursor: "pointer",
                  fontSize: 16
                }}
              >
                ▦
              </button>
              <button
                onClick={() => setIsGridView(false)}
                style={{
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: "1px solid #d1d5db",
                  background: !isGridView ? "#2563eb" : "#fff",
                  color: !isGridView ? "#fff" : "#222",
                  cursor: "pointer",
                  fontSize: 16
                }}
              >
                ≡
              </button>
            </div>
          )}
        </div>

        <p style={{ margin: 0, color: "#6b7280", fontSize: 14 }}>
          Choose an existing course or create a new one for your exported content
        </p>

        {/* Create New Course Button */}
        {!loading && !error && (
          <button
            onClick={handleCreateNewCourse}
            style={{
              width: '100%',
              padding: '14px 16px',
              borderRadius: 10,
              border: '2px dashed #2563eb',
              background: '#f5f8ff',
              color: '#2563eb',
              fontSize: 15,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 10,
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = '#eff6ff';
              e.target.style.borderColor = '#1d4ed8';
            }}
            onMouseLeave={(e) => {
              e.target.style.background = '#f5f8ff';
              e.target.style.borderColor = '#2563eb';
            }}
          >
            <span style={{ fontSize: 18 }}>➕</span>
            Create New Course in LMS
          </button>
        )}

        {/* Search Bar */}
        {!loading && !error && courses.length > 0 && (
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by course name, code, or instructor..."
            style={{
              width: '100%',
              padding: '10px 12px',
              borderRadius: 8,
              border: '1px solid #d1d5db',
              fontSize: 14,
              boxSizing: 'border-box'
            }}
          />
        )}

        {/* Loading State */}
        {loading && (
          <div style={{ 
            textAlign: 'center',
            padding: '60px 20px'
          }}>
            <div style={{
              width: 48,
              height: 48,
              border: "4px solid #e5e7eb",
              borderTop: "4px solid #2563eb",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
              margin: '0 auto 16px auto'
            }}></div>
            <div style={{
              fontSize: 15,
              fontWeight: 600,
              color: "#2563eb"
            }}>
              Loading courses from LMS...
            </div>
            <style>{`
              @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
              }
            `}</style>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div style={{ 
            padding: '16px',
            background: '#fee2e2',
            borderRadius: 8,
            border: '1px solid #fecaca',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: 16, fontWeight: 600, color: '#b91c1c', marginBottom: 8 }}>
              ❌ Error Loading Courses
            </div>
            <div style={{ fontSize: 14, color: '#991b1b', marginBottom: 12 }}>
              {error}
            </div>
            <button
              onClick={fetchLMSCourses}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "none",
                background: "#b91c1c",
                color: "#fff",
                fontWeight: 600,
                fontSize: 14,
                cursor: "pointer"
              }}
            >
              Try Again
            </button>
          </div>
        )}

        {/* Courses List */}
        {!loading && !error && (
          <div style={{
            maxHeight: '400px',
            overflowY: 'auto',
            border: '1px solid #e5e7eb',
            borderRadius: 10,
            background: '#fafbfc',
            padding: 8
          }}>
            {filteredCourses.length === 0 ? (
              <div style={{ 
                padding: '40px 20px',
                textAlign: 'center',
                color: '#6b7280',
                fontSize: 14
              }}>
                {searchQuery ? `No courses found matching "${searchQuery}"` : "No courses available"}
              </div>
            ) : isGridView ? (
              /* Grid View */
              <div style={{ display: 'grid', gap: 12 }}>
                {filteredCourses.map(course => (
                  <div
                    key={course.id}
                    onClick={() => handleCourseSelect(course.id)}
                    style={{
                      background: '#fff',
                      borderRadius: 10,
                      padding: 16,
                      border: selectedCourseId === course.id ? '3px solid #2563eb' : '1px solid #e5e7eb',
                      cursor: 'pointer',
                      position: 'relative',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      if (selectedCourseId !== course.id) {
                        e.currentTarget.style.borderColor = '#cbd5e1';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedCourseId !== course.id) {
                        e.currentTarget.style.borderColor = '#e5e7eb';
                      }
                    }}
                  >
                    {/* Selection indicator */}
                    {selectedCourseId === course.id && (
                      <div style={{
                        position: 'absolute',
                        top: 12,
                        right: 12,
                        width: 28,
                        height: 28,
                        borderRadius: '50%',
                        background: '#2563eb',
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: 16,
                        fontWeight: 'bold'
                      }}>
                        ✓
                      </div>
                    )}

                    {/* Course Header */}
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 8 }}>
                      <div style={{ flex: 1 }}>
                        <h3 style={{ 
                          fontSize: 16, 
                          fontWeight: 700, 
                          color: '#2563eb',
                          margin: '0 0 4px 0'
                        }}>
                          {course.name}
                        </h3>
                        {course.code && (
                          <div style={{ fontSize: 12, color: '#6b7280', fontWeight: 600 }}>
                            {course.code}
                          </div>
                        )}
                      </div>
                      {course.status && (
                        <span style={{
                          padding: '4px 10px',
                          borderRadius: 10,
                          fontSize: 11,
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          background: course.status === 'active' ? '#dcfce7' : '#f3f4f6',
                          color: course.status === 'active' ? '#16a34a' : '#6b7280'
                        }}>
                          {course.status}
                        </span>
                      )}
                    </div>

                    {/* Course Info */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13, color: '#374151' }}>
                      {course.instructor && (
                        <div>👤 {course.instructor}</div>
                      )}
                      {course.enrollment_count !== undefined && (
                        <div>👥 {course.enrollment_count} students</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              /* List View */
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ background: '#f5f8ff', borderBottom: '1px solid #e5e7eb' }}>
                    <th style={{ padding: '10px 12px', textAlign: 'center', fontSize: 13, fontWeight: 700, color: '#2563eb', width: 50 }}>
                      Select
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'left', fontSize: 13, fontWeight: 700, color: '#2563eb' }}>
                      Course
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'left', fontSize: 13, fontWeight: 700, color: '#2563eb' }}>
                      Code
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', fontSize: 13, fontWeight: 700, color: '#2563eb' }}>
                      Students
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', fontSize: 13, fontWeight: 700, color: '#2563eb' }}>
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCourses.map((course, index) => (
                    <tr 
                      key={course.id}
                      onClick={() => handleCourseSelect(course.id)}
                      style={{ 
                        borderBottom: index < filteredCourses.length - 1 ? '1px solid #f3f4f6' : 'none',
                        cursor: 'pointer',
                        background: selectedCourseId === course.id ? '#eff6ff' : 'transparent'
                      }}
                    >
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <input
                          type="radio"
                          checked={selectedCourseId === course.id}
                          onChange={() => handleCourseSelect(course.id)}
                          style={{ width: 18, height: 18, cursor: 'pointer' }}
                        />
                      </td>
                      <td style={{ padding: '12px', fontSize: 14, fontWeight: 600, color: '#2563eb' }}>
                        {course.name}
                      </td>
                      <td style={{ padding: '12px', fontSize: 13, color: '#6b7280' }}>
                        {course.code || '-'}
                      </td>
                      <td style={{ padding: '12px', fontSize: 13, color: '#374151', textAlign: 'center' }}>
                        {course.enrollment_count !== undefined ? course.enrollment_count : '-'}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <span style={{
                          padding: '4px 10px',
                          borderRadius: 10,
                          fontSize: 11,
                          fontWeight: 600,
                          textTransform: 'uppercase',
                          background: course.status === 'active' ? '#dcfce7' : '#f3f4f6',
                          color: course.status === 'active' ? '#16a34a' : '#6b7280'
                        }}>
                          {course.status || 'active'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Action Buttons */}
        {!loading && !error && (
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 8 }}>
            <button
              onClick={onClose}
              style={{
                padding: "10px 20px",
                borderRadius: 8,
                border: "1px solid #d1d5db",
                background: "#fff",
                color: "#374151",
                fontWeight: 600,
                fontSize: 15,
                cursor: "pointer"
              }}
            >
              Cancel
            </button>
            <button
              onClick={handleProceedWithExport}
              disabled={!selectedCourseId}
              style={{
                padding: "10px 24px",
                borderRadius: 8,
                border: "none",
                background: selectedCourseId ? "#2563eb" : "#94a3b8",
                color: "#fff",
                fontWeight: 600,
                fontSize: 15,
                cursor: selectedCourseId ? "pointer" : "not-allowed",
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}
            >
              Continue to Export
              <span style={{ fontSize: 16 }}>→</span>
            </button>
          </div>
        )}
      </div>
    </Modal>
  );
}

