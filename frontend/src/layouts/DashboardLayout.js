import React from "react";
import curriculumOptions from "../data/curriculumOptions";
import assessmentsOptions from "../data/assessmentsOptions";
import DashboardHeader from "../components/header/DashboardHeader";
import SectionCard from "../components/SectionCard";
import Sidebar from "../components/Sidebar";
import SettingsModal from "../components/SettingsModal";
import Modal from "../components/Modal";
import KnowledgeBase from "../components/KnowledgBase";
import ExportAssetsModal from "../components/ExportAssetsModal";
import LMSLoginModal from "../components/LMSLoginModal";
import { useNavigate } from "react-router-dom";

export default function DashboardLayout({ state }) {
  const navigate = useNavigate();
  const [showLMSLoginModal, setShowLMSLoginModal] = React.useState(false);
  const [showExportModal, setShowExportModal] = React.useState(false);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#fafbfc" }}>
      <DashboardHeader
        isGridView={state.isGridView}
        onGridView={() => state.setIsGridView(true)}
        onListView={() => state.setIsGridView(false)}
        onSettings={() => state.setShowSettingsModal(true)}
        onExport={() => setShowLMSLoginModal(true)}
        onLogout={() => {
          localStorage.removeItem("user");
          navigate("/login");
        }}
      />

      {/* Main Body */}
      <div style={{ display: "flex", flex: 1, padding: "20px 5vw", gap: 24 }}>
        <div style={{ flex: 2, display: "flex", flexDirection: "column", gap: 24 }}>
          <SectionCard title="Curriculum" buttonLabel="Create" onButtonClick={state.handleCurriculumCreate} />
          <SectionCard title="Assessments" buttonLabel="Create" onButtonClick={state.handleAssessmentsCreate} />
          <SectionCard title="Evaluation" buttonLabel="Start Evaluation" />
          <KnowledgeBase 
            onFileChange={() => {}} 
            courseId={localStorage.getItem('currentCourseId')}
          />
        </div>
        <div style={{ flex: 1 }}>
          <Sidebar ref={state.sidebarRef} onAddContentClick={() => state.setShowAddResourceModal(true)} />
        </div>
      </div>

      {/* Curriculum Modal */}
      <Modal open={state.showCurriculumModal} onClose={() => state.setShowCurriculumModal(false)}>
        <div style={{ fontWeight: 700, fontSize: 22, marginBottom: 8 }}>✨ Curriculum</div>
        <div style={{ fontSize: 15, marginBottom: 16 }}>Select Curriculum Component</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 24 }}>
          {curriculumOptions.map((opt, i) => (
            <label key={opt.label} style={{
              border: state.selectedOption === i ? "2px solid #1976d2" : "1px solid #ccc",
              background: state.selectedOption === i ? "#e8f1ff" : "#fff",
              borderRadius: 10,
              padding: 12,
              cursor: "pointer",
              flex: "1 1 40%"
            }}>
              <input
                type="radio"
                name="curriculum"
                checked={state.selectedOption === i}
                onChange={() => {
                  state.setSelectedOption(i);
                  state.setSelectedComponent(opt.url);
                }}
                style={{ marginRight: 8 }}
              />
              <strong>{opt.label}</strong>
              <div style={{ fontSize: 13, color: "#555", marginTop: 4 }}>{opt.desc}</div>
            </label>
          ))}
        </div>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
          <button onClick={() => state.setShowCurriculumModal(false)} style={{ padding: "8px 16px", borderRadius: 6, border: "1px solid #ccc" }}>Cancel</button>
          <button
            onClick={() => {
              state.setShowCurriculumModal(false);
              navigate(`/studio/${curriculumOptions[state.selectedOption].url}`);
            }}
            style={{ padding: "8px 16px", borderRadius: 6, background: "#222", color: "#fff", fontWeight: 500 }}
          >
            Create
          </button>
        </div>
      </Modal>

      {/* Assessments Modal */}
      <Modal open={state.showAssessmentsModal} onClose={() => state.setShowAssessmentsModal(false)}>
        <div style={{ fontWeight: 700, fontSize: 22, marginBottom: 8 }}>🧪 Assessments</div>
        <div style={{ fontSize: 15, marginBottom: 16 }}>Select Assessment Component</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginBottom: 24 }}>
          {assessmentsOptions.map((opt, i) => (
            <label key={opt.label} style={{
              border: state.selectedOption === i ? "2px solid #1976d2" : "1px solid #ccc",
              background: state.selectedOption === i ? "#e8f1ff" : "#fff",
              borderRadius: 10,
              padding: 12,
              cursor: "pointer",
              flex: "1 1 40%"
            }}>
              <input
                type="radio"
                name="assessments"
                checked={state.selectedOption === i}
                onChange={() => {
                  state.setSelectedOption(i);
                  state.setSelectedComponent(opt.url);
                }}
                style={{ marginRight: 8 }}
              />
              <strong>{opt.label}</strong>
              <div style={{ fontSize: 13, color: "#555", marginTop: 4 }}>{opt.desc}</div>
            </label>
          ))}
        </div>
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
          <button onClick={() => state.setShowAssessmentsModal(false)} style={{ padding: "8px 16px", borderRadius: 6, border: "1px solid #ccc" }}>Cancel</button>
          <button
            onClick={() => {
              state.setShowAssessmentsModal(false);
              navigate(`/studio/${assessmentsOptions[state.selectedOption].url}`);
            }}
            style={{ padding: "8px 16px", borderRadius: 6, background: "#222", color: "#fff", fontWeight: 500 }}
          >
            Create
          </button>
        </div>
      </Modal>

      <SettingsModal open={state.showSettingsModal} onClose={() => state.setShowSettingsModal(false)} onSave={() => state.setShowSettingsModal(false)} />
      
      {/* ========================================
          LMS Login Modal - Shows first when Export to LMS is clicked
          BACKEND INTEGRATION: This modal calls /api/login-lms endpoint
          ======================================== */}
      <LMSLoginModal
        open={showLMSLoginModal}
        onClose={() => setShowLMSLoginModal(false)}
        onLoginSuccess={(data) => {
          console.log("✅ LMS login successful:", data);
          
          // Log course information
          if (data.courses && data.courses.length > 0) {
            console.log(`📚 Loaded ${data.courses.length} courses from LMS:`, data.courses);
          } else if (data.coursesError) {
            console.warn("⚠️ Courses couldn't be loaded:", data.coursesError);
          }
          
          // Close login modal
          setShowLMSLoginModal(false);
          // Proceed to export modal
          setShowExportModal(true);
        }}
      />
      
      {/* ========================================
          Export Assets Modal - Shows after successful LMS login
          BACKEND INTEGRATION: This modal calls /api/courses/{id}/export-lms (current)
          FUTURE: Will call /api/courses/{id}/push-to-lms when implemented
          ======================================== */}
      <ExportAssetsModal
        open={showExportModal}
        onClose={() => setShowExportModal(false)}
        assets={[]}
        onExportSelected={(selected) => {
          // BACKEND: Selected assets are sent to backend for processing
          // Current: Downloads JSON file
          // Future: Pushes directly to LMS platform
          console.log("Selected for export:", selected);
        }}
      />
    </div>
  );
}
