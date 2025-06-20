import React, { useState } from "react";
import { chatReviseCourse } from "./CourseAPI";

function CourseChat({ courseData, onUpdate }) {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSend = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setError("");

    try {
      const response = await chatReviseCourse(courseData, input);
      const updated = JSON.parse(response);
      onUpdate(updated);
    } catch (err) {
      console.error("Parsing failed:", err);
      setError("⚠️ Failed to process your instruction. Try again.");
    } finally {
      setInput("");
      setLoading(false);
    }
  };

  return (
    <div style={{
        display: "flex",
        padding: "12px 16px",
        borderTop: "1px solid #eee",
        background: "#fff",
        alignItems: "flex-end",
        boxShadow: "0 -2px 8px rgba(0,0,0,0.03)",
        gap: "10px"
      }}>
      
      <textarea
        placeholder="Type your instruction..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        rows={2}
        style={{
          flex: 1,
          borderRadius: "10px",
          border: "1px solid #ddd",
          padding: "12px",
          fontSize: "1rem",
          resize: "none",
          minHeight: "48px",
          maxHeight: "120px",
          overflowY: "auto",
          fontFamily: "inherit"
        }}
      />
      <button
        onClick={handleSend}
        style={{
          padding: "10px 18px",
          background: "#6c63ff",
          color: "white",
          border: "none",
          borderRadius: "10px",
          fontWeight: "bold",
          cursor: "pointer",
          height: "48px"
        }}
      >
        {loading ? "Sending..." : "Send"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}

export default CourseChat;
