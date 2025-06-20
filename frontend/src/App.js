import React, { useState } from "react";
import CourseForm from "./components/Course/CourseForm";
import CourseOverview from "./components/Course/CourseOverview";
import CourseChat from "./components/Course/CourseChat";
import LeftPanel from "./components/shared/LeftPanel";
import ResourcePanel from "./components/ResourcePanel";

const globalStyles = document.createElement('style');
globalStyles.innerHTML = `
  html, body {
    margin: 0;
    padding: 0;
    height: 100%;
    overflow: hidden;
  }
`;
document.head.appendChild(globalStyles);

function App() {
  const [hasStarted, setHasStarted] = useState(false);
  const [showFormModal, setShowFormModal] = useState(false);
  const [courseContext, setCourseContext] = useState(null);
  const [activeBlock, setActiveBlock] = useState(null);
  const [courseData, setCourseData] = useState(null);

  const renderCenterPanel = () => {
    if (activeBlock === "generate_course") {
      if (!courseData && courseContext) {
        fetch("/generate_course", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(courseContext)
        })
          .then(res => res.json())
          .then(data => setCourseData(data.result))
          .catch(console.error);
      }

      if (!courseData) {
        return <p style={{ textAlign: "center", marginTop: "2rem", color: "#aaa" }}>Generating...</p>;
      }

      return <CourseOverview courseData={courseData} />;
    }

    return (
      <p style={{ textAlign: "center", marginTop: "2rem", color: "#888", fontStyle: "italic" }}>
        Select a block to begin or use free chat
      </p>
    );
  };

  if (!hasStarted) {
    return (
      <div style={{
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        fontFamily: "Segoe UI, sans-serif"
      }}>
        <h1>🎓 Welcome to the AI Course Builder</h1>
        <button
          onClick={() => setShowFormModal(true)}
          style={{
            padding: "12px 24px",
            fontSize: "1rem",
            background: "#6c63ff",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            cursor: "pointer",
            boxShadow: "0 4px 12px rgba(0,0,0,0.1)"
          }}
        >
          🚀 Create Course
        </button>

        {showFormModal && (
          <div style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            backgroundColor: "rgba(0, 0, 0, 0.4)",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            zIndex: 999
          }}>
            <div style={{
              background: "#fff",
              borderRadius: "12px",
              padding: "1.5rem 2rem",
              width: "420px",
              boxShadow: "0 8px 24px rgba(0,0,0,0.2)",
              display: "flex",
              flexDirection: "column",
              justifyContent: "center"
            }}>
              <h3 style={{ marginBottom: "1rem", textAlign: "center" }}>📘 Create New Course</h3>
              <CourseForm
                onGenerate={(formData) => {
                  setCourseContext(formData);
                  setShowFormModal(false);
                  setHasStarted(true);
                }}
                showSubmitOnly={true}
              />
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={{
      display: "flex",
      height: "100vh",
      width: "100vw",
      fontFamily: "Segoe UI, sans-serif",
      overflow: "hidden"
    }}>
      <div style={{
        flex: "0 0 240px",
        background: "#f8f9fa",
        borderRight: "1px solid #eee",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
      }}>
        <LeftPanel onSelectBlock={setActiveBlock} />
      </div>

      <div style={{
        flex: "1",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden"
      }}>
        <div style={{
          flex: 1,
          overflowY: "auto",
          padding: "1.5rem",
          boxSizing: "border-box"
        }}>
          {renderCenterPanel()}
        </div>

        <div style={{
          borderTop: "1px solid #eee",
          padding: "1rem",
          background: "#fff",
          boxSizing: "border-box"
        }}>
          <CourseChat courseData={courseData} onUpdate={setCourseData} />
        </div>
      </div>

      <div style={{
        flex: "0 0 300px",
        borderLeft: "1px solid #eee",
        background: "#fdfdfd",
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column"
      }}>
        <ResourcePanel />
      </div>
    </div>
  );
}

export default App;
