import React, { useState } from "react";
import { formContainerStyle, textareaStyle, inputStyle, labelStyle } from "../styles";

function CourseForm({ onGenerate, showSubmitOnly = false }) {
  const [form, setForm] = useState({
    course_name: "",
    description: "",
    duration_days: "",
    total_hours: "",
  });
  const [loading] = useState(false);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (onGenerate) onGenerate(form);
  };

  return (
    <form onSubmit={handleSubmit} style={{ ...formContainerStyle, gap: "0.5rem" }}>
      <label style={labelStyle}>Course Name</label>
      <input name="course_name" value={form.course_name} onChange={handleChange} style={inputStyle} />

      <label style={labelStyle}>Description</label>
      <textarea
        name="description"
        rows={3}
        value={form.description}
        onChange={handleChange}
        style={textareaStyle}
      />

      <label style={labelStyle}>Duration (Days)</label>
      <input name="duration_days" type="number" value={form.duration_days} onChange={handleChange} style={inputStyle} />

      <label style={labelStyle}>Total Hours</label>
      <input name="total_hours" type="number" value={form.total_hours} onChange={handleChange} style={inputStyle} />

      <button
        type="submit"
        disabled={loading}
        style={{
          marginTop: "0.5rem",
          padding: "10px 16px",
          fontSize: "1rem",
          background: "#6c63ff",
          color: "#fff",
          border: "none",
          borderRadius: "6px",
          cursor: "pointer",
          alignSelf: "center"
        }}
      >
        {showSubmitOnly ? "Submit" : (loading ? "Generating..." : "Generate Overview")}
      </button>
    </form>
  );
}

export default CourseForm;
