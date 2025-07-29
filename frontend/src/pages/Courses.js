// src/pages/Courses.js
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import CoursesLayout from "../layouts/CoursesLayout";
import CourseModal from "../components/CourseModal";
import { useCourses } from "../hooks/useCourses";

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

  useEffect(() => {
    // TODO: Replace localStorage with backend course fetch
    const stored = JSON.parse(localStorage.getItem("createdCourses") || "[]");
    setSavedCourses(stored);
  }, [showModal]);

  const renderCourseCard = (course, index) => (
    <div
      key={index}
      onClick={() => {
        // TODO: Replace localStorage with backend context/auth storage
        localStorage.setItem("currentCourseTitle", course.title);
        localStorage.setItem("currentCourseId", course.id || `course-${index}`);
        navigate("/dashboard");
      }}
      style={{
        background: "#f9f9ff",
        padding: "16px 20px",
        borderRadius: 10,
        boxShadow: "0 1px 6px rgba(0,0,0,0.08)",
        minWidth: 160,
        maxWidth: 200,
        cursor: "pointer",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        fontSize: 15,
        fontWeight: 600,
        color: "#111",
        transition: "transform 0.2s, box-shadow 0.2s"
      }}
      onMouseEnter={(e) => e.currentTarget.style.transform = "translateY(-2px)"}
      onMouseLeave={(e) => e.currentTarget.style.transform = "none"}
    >
      {course.title}
    </div>
  );

  return (
    <div style={{ minHeight: "100vh", background: "#fff", display: "flex", flexDirection: "column", height: "100vh", overflow: "hidden" }}>
      <CoursesLayout
        onAddCourse={() => setShowModal(true)}
        onLogout={handleLogout}
      >
        {/* ✅ Course Cards go here */}
        <div style={{ padding: "24px 5vw", display: "flex", flexWrap: "wrap", gap: "20px" }}>
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
        onSubmit={() => {
          const prev = JSON.parse(localStorage.getItem("createdCourses") || "[]");
          const newCourse = {
            id: Date.now().toString(),
            title: courseName,
            desc: courseDesc
          };
          const updated = [...prev, newCourse];
          localStorage.setItem("createdCourses", JSON.stringify(updated));

          localStorage.setItem("currentCourseTitle", newCourse.title);
          localStorage.setItem("currentCourseId", newCourse.id);

          setShowModal(false);
          navigate("/dashboard");
        }}
        loading={loading}
        error={error}
      />
    </div>
  );
}
