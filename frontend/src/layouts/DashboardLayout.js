import React from "react";
import curriculumOptions from "../data/curriculumOptions";
import assessmentsOptions from "../data/assessmentsOptions";
import AppHeader from "../components/header/AppHeader";
import SectionCard from "../components/SectionCard";
import Sidebar from "../components/Sidebar";
import SettingsModal from "../components/SettingsModal";
import Modal from "../components/Modal";
import KnowledgeBase from "../components/KnowledgBase";
import { useNavigate } from "react-router-dom";

export default function DashboardLayout({ state }) {
  const navigate = useNavigate();

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "#fafbfc" }}>
      <AppHeader
        isGridView={state.isGridView}
        onGridView={() => state.setIsGridView(true)}
        onListView={() => state.setIsGridView(false)}
        onSettings={() => state.setShowSettingsModal(true)}
        onExport={() => alert("Export to LMS is coming soon!")}
        onLogout={() => {
          localStorage.removeItem("user");
          navigate("/login");
        }}
        type="dashboard"
      />

      {/* Main Body */}
      <div style={{ display: "flex", flex: 1, padding: "20px 5vw", gap: 24 }}>
        <div style={{ flex: 2, display: "flex", flexDirection: "column", gap: 24 }}>
          <SectionCard title="Curriculum" buttonLabel="Create" onButtonClick={state.handleCurriculumCreate} />
          <SectionCard title="Assessments" buttonLabel="Create" onButtonClick={state.handleAssessmentsCreate} />
          <SectionCard title="Evaluation" buttonLabel="Start Evaluation" />
          <KnowledgeBase onFileChange={() => {}} />
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
    </div>
  );
}
