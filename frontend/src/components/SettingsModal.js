import React, { useState, useEffect, useCallback } from "react";
import Modal from "./Modal";
import { FaWrench } from "react-icons/fa";
import { saveCourseSettings, getCourseSettings } from "../services/course";

// Dummy tag data (replace with backend data if needed)
const LEVELS = ["Year 1", "Year 2", "Year 3", "Year 4"];
const STUDY_AREAS = [
  "AI & Decentralised Technologies", "Life Sciences", "Energy Sciences", "eMobility",
  "Climate Change", "Connected Intelligence"
];
const PEDAGOGICAL_COMPONENTS = [
  "Theory", "Project", "Research", "Laboratory Experiments",
  "Unplugged Activities", "Programming Activities"
];

export default function SettingsModal({ open, onClose, onSave }) {
  const [selectedLevels, setSelectedLevels] = useState([]);
  const [selectedStudyAreas, setSelectedStudyAreas] = useState([]);
  const [selectedPedagogical, setSelectedPedagogical] = useState([]);
  const [askClarifyingQuestions, setAskClarifyingQuestions] = useState(false);
  const [, setLoading] = useState(false);

  // Get courseId from localStorage
  const courseId = localStorage.getItem("currentCourseId");

  const loadSavedSettings = useCallback(async () => {
    if (!courseId) return;
    
    setLoading(true);
    try {
      const savedSettings = await getCourseSettings(courseId);
      console.log("Loaded saved settings:", savedSettings);
      
      // Map backend field names to component state
      if (savedSettings) {
        setSelectedLevels(savedSettings.course_level || []);
        setSelectedStudyAreas(savedSettings.study_area || []);
        setSelectedPedagogical(savedSettings.pedagogical_components || []);
        setAskClarifyingQuestions(savedSettings.ask_clarifying_questions || false);
      }
    } catch (error) {
      console.error("Error loading saved settings:", error);
    } finally {
      setLoading(false);
    }
  }, [courseId]);

  // Load saved settings when modal opens
  useEffect(() => {
    if (open && courseId) {
      loadSavedSettings();
    }
  }, [open, courseId, loadSavedSettings]);

  // Toggle tag selection
  const toggleTag = (tag, selectedTags, setSelectedTags) => {
    setSelectedTags(prev =>
      prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]
    );
  };

  const handleSave = async () => {
    if (!courseId) {
      console.error("No courseId found in localStorage");
      return;
    }

    const payload = {
      course_level: selectedLevels,
      study_area: selectedStudyAreas,
      pedagogical_components: selectedPedagogical,
      ask_clarifying_questions: askClarifyingQuestions
    };
    console.log("Saving settings:", payload);
    try {
      await saveCourseSettings(courseId, payload);
      if (onSave) {
        // UNDERSTAND: Why? How? What is onSave in previous and next line?
        onSave(payload);
      }
      onClose(); // Close the modal after successful save
    } catch (error) {
      console.error("Error saving settings:", error);
      // You might want to show an error message to the user here
    }
  };

  return (
    <Modal open={open} onClose={onClose}>
      <div style={{ fontWeight: 700, fontSize: 22, marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
        <FaWrench /> Settings
      </div>

      <div style={{ marginBottom: 16 }}>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>Course level <span style={{ fontWeight: 400, fontSize: 13 }}>(select all that are applicable)</span></div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {LEVELS.map(level => (
            <button key={level}
              onClick={() => toggleTag(level, selectedLevels, setSelectedLevels)}
              style={{
                padding: "6px 12px",
                borderRadius: 16,
                border: selectedLevels.includes(level) ? "2px solid #2563eb" : "1px solid #ccc",
                background: selectedLevels.includes(level) ? "#e0edff" : "#fff",
                fontWeight: 500,
                cursor: "pointer"
              }}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>Study area</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {STUDY_AREAS.map(area => (
            <button key={area}
              onClick={() => toggleTag(area, selectedStudyAreas, setSelectedStudyAreas)}
              style={{
                padding: "6px 12px",
                borderRadius: 16,
                border: selectedStudyAreas.includes(area) ? "2px solid #2563eb" : "1px solid #ccc",
                background: selectedStudyAreas.includes(area) ? "#e0edff" : "#fff",
                fontWeight: 500,
                cursor: "pointer"
              }}
            >
              {area}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 16 }}>
        <div style={{ fontWeight: 600, marginBottom: 6 }}>Pedagogical Components <span style={{ fontWeight: 400, fontSize: 13 }}>(select all that are applicable)</span></div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
          {PEDAGOGICAL_COMPONENTS.map(comp => (
            <button key={comp}
              onClick={() => toggleTag(comp, selectedPedagogical, setSelectedPedagogical)}
              style={{
                padding: "6px 12px",
                borderRadius: 16,
                border: selectedPedagogical.includes(comp) ? "2px solid #2563eb" : "1px solid #ccc",
                background: selectedPedagogical.includes(comp) ? "#e0edff" : "#fff",
                fontWeight: 500,
                cursor: "pointer"
              }}
            >
              {comp}
            </button>
          ))}
        </div>
      </div>

      <div style={{ marginBottom: 24 }}>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={askClarifyingQuestions}
            onChange={() => setAskClarifyingQuestions(prev => !prev)}
          />
          Ask clarifying questions
        </label>
        <div style={{ color: "#666", fontSize: 13, marginLeft: 22 }}>
          Allows AI to ask targeted questions and gather necessary context before generating content.
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
        <button onClick={onClose} style={{ padding: "10px 24px", background: "#fff", border: "1px solid #bbb", borderRadius: 8, fontWeight: 500, cursor: "pointer" }}>Close</button>
        <button onClick={handleSave} style={{ padding: "10px 24px", background: "#222", color: "#fff", border: "none", borderRadius: 8, fontWeight: 600, cursor: "pointer" }}>Save Changes</button>
      </div>
    </Modal>
  );
}