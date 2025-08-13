import React from "react";

const spinnerStyle = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  minHeight: "40vh",
};

const circleStyle = {
  width: 48,
  height: 48,
  border: "6px solid #e0e0e0",
  borderTop: "6px solid #222",
  borderRadius: "50%",
  animation: "spin 1s linear infinite"
};

const keyframes = `@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`;

export default function LoadingSpinner() {
  return (
    <div style={spinnerStyle}>
      <style>{keyframes}</style>
      <div style={circleStyle} aria-label="Loading" />
    </div>
  );
} 