import React from "react";

export default function NotFound() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", justifyContent: "center", alignItems: "center", background: "#f7f7f7" }}>
      <div style={{ background: "#fff", padding: 40, borderRadius: 16, boxShadow: "0 4px 24px #0002", textAlign: "center" }}>
        <h1 style={{ fontSize: 48, fontWeight: 700, color: "#2563eb", margin: "0 0 16px 0" }}>404</h1>
        <p style={{ fontSize: 18, color: "#6b7280", margin: "0 0 24px 0" }}>Page not found</p>
        <a href="/" style={{ color: "#2563eb", textDecoration: "none", fontWeight: 500 }}>Go back home</a>
      </div>
    </div>
  );
} 