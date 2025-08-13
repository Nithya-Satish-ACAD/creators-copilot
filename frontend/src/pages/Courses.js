// src/pages/Courses.js
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import CoursesLayout from "../layouts/CoursesLayout";
import CourseModal from "../components/CourseModal";
import { useCourses } from "../hooks/useCourses";
import { fetchCourses, createCourse,  deleteCourse } from "../services/course";
import { useRef } from "react";

export default function Courses() {
  const {
    showModal, setShowModal,
    courseName, setCourseName,
    courseDesc, setCourseDesc,
    handleLogout,
    loading, error
  } = useCourses();

  const [savedCourses, setSavedCourses] = useState([]);
  const navigate = useNavigate();
  const [menuOpenIndex, setMenuOpenIndex] = useState(null);
  const menuRef = useRef();

  useEffect(() => {
    async function loadCourses() {
      try {
        const coursesFromAPI = await fetchCourses();
        setSavedCourses(coursesFromAPI);
      } catch (err) {
        console.error("Failed to fetch courses:", err);
        if (err.message === 'User not authenticated') {
          // Redirect to login if user is not authenticated
          navigate("/login");
        }
      }
    }
  
    loadCourses();
  }, [showModal, navigate]);

  // Close menu on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpenIndex(null);
      }
    }
    if (menuOpenIndex !== null) {
      document.addEventListener("mousedown", handleClickOutside);
    } else {
      document.removeEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [menuOpenIndex]);

  const handleDelete = async (courseId) => {
    const confirmed = window.confirm("Are you sure you want to delete this course? This action cannot be undone.");
    if (!confirmed) return;
    try {
      await deleteCourse(courseId);
      setSavedCourses((prev) => prev.filter((c) => c.id !== courseId));
      setMenuOpenIndex(null);
    } catch (err) {
      alert("Failed to delete course.");
    }
  };

  const renderCourseCard = (course, index) => (
    <div
      key={index}
      style={{
        background: "#fff",
        border: "1.5px solid #f3f4f6",
        borderRadius: 16,
        boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
        minWidth: 220,
        maxWidth: 260,
        minHeight: 90,
        padding: "24px 20px",
        cursor: "pointer",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 17,
        fontWeight: 600,
        color: "#222",
        position: 'relative',
        transition: "transform 0.18s, box-shadow 0.18s, border 0.18s"
      }}
      onClick={e => {
        // Only navigate if not clicking the menu
        if (e.target.getAttribute('data-menu')) return;
        localStorage.setItem("currentCourseTitle", course.name);
        localStorage.setItem("currentCourseId", course.id || `course-${index}`);
        navigate("/dashboard");
      }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = "translateY(-4px) scale(1.03)";
        e.currentTarget.style.boxShadow = "0 6px 24px rgba(37,99,235,0.08)";
        e.currentTarget.style.border = "1.5px solid #2563eb";
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = "none";
        e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.04)";
        e.currentTarget.style.border = "1.5px solid #f3f4f6";
      }}
    >
      <span style={{ fontWeight: 700, fontSize: 18, marginBottom: 6, textAlign: 'center', width: '100%', textTransform: 'capitalize', letterSpacing: 0.2 }}>{course.name}</span>
      {/* Three-dot menu */}
      <button
        data-menu
        style={{
          position: 'absolute',
          top: 12,
          right: 14,
          background: 'none',
          border: 'none',
          fontSize: 22,
          color: '#b0b3b8',
          cursor: 'pointer',
          padding: 0,
          zIndex: 2
        }}
        onClick={e => {
          e.stopPropagation();
          setMenuOpenIndex(index === menuOpenIndex ? null : index);
        }}
        aria-label="Open menu"
      >
        &#8942;
      </button>
      {/* Dropdown menu */}
      {menuOpenIndex === index && (
        <div
          ref={menuRef}
          style={{
            position: 'absolute',
            top: 38,
            right: 14,
            background: '#fff',
            border: '1px solid #eee',
            borderRadius: 8,
            boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            zIndex: 10,
            minWidth: 90,
            padding: '6px 0',
          }}
        >
          <div
            style={{
              padding: '8px 18px',
              color: '#e11d48',
              fontWeight: 500,
              fontSize: 15,
              cursor: 'pointer',
              border: 'none',
              background: 'none',
              textAlign: 'left',
              width: '100%'
            }}
            onClick={e => {
              e.stopPropagation();
              handleDelete(course.id);
            }}
          >
            Delete
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div style={{ minHeight: "100vh", background: "#fff", display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden" }}>
      <CoursesLayout
        onAddCourse={() => setShowModal(true)}
        onLogout={handleLogout}
      >
        {/* ✅ Course Cards go here */}
        <div style={{ padding: "24px 5vw", display: "flex", flexWrap: "wrap", gap: "32px" }}>
          {savedCourses.length > 0 ? (
            savedCourses.map(renderCourseCard)
          ) : (
            <div style={{ color: "#888", fontSize: 16 }}>No courses created yet.</div>
          )}
        </div>
      </CoursesLayout>

      {/* ✅ Create Course Modal */}
      <CourseModal
        open={showModal}
        onClose={() => setShowModal(false)}
        courseName={courseName}
        setCourseName={setCourseName}
        courseDesc={courseDesc}
        setCourseDesc={setCourseDesc}
        onSubmit={async () => {
          try {
            const newCourse = await createCourse({
              name: courseName,
              description: courseDesc
            });
            setShowModal(false);
            localStorage.setItem("currentCourseTitle", newCourse.name);
            localStorage.setItem("currentCourseId", newCourse.id);
            navigate("/dashboard");
          } catch (err) {
            console.error("Error creating course:", err);
          }
        }}
        loading={loading}
        error={error}
      />
    </div>
  );
}
