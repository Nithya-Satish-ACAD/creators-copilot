import React from "react";

const safeList = (data) => {
  if (Array.isArray(data)) return data;
  if (typeof data === "string") return data.split(/[,•\n]/).map(s => s.trim()).filter(Boolean);
  return [];
};

function CourseOverview({ courseData }) {
  return (
    <div style={{ background: "#fff", padding: "1.5rem", borderRadius: "10px", boxShadow: "0 0 8px rgba(0,0,0,0.05)" }}>
      <h2>📄 Course Overview</h2>

      <h3>📝 Description</h3>
      <p>{courseData.course_description}</p>

      <h3>📚 Methodology</h3>
      <p>{courseData.methodology}</p>

      <h3>🎯 Course Outcomes</h3>
      <ul>
        {safeList(courseData.course_outcomes).map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>

      <h3>💼 Job Roles Prepared For</h3>
      <ul>
        {safeList(courseData.job_roles_prepared_for).map((role, i) => (
          <li key={i}>{role}</li>
        ))}
      </ul>

      <h3>🛠️ Industry Skills Gained</h3>
      <ul>
        {safeList(courseData.industry_skills_gained).map((skill, i) => (
          <li key={i}>{skill}</li>
        ))}
      </ul>
    </div>
  );
}

export default CourseOverview;