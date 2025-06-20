export const containerStyle = {
  display: "flex",
  flexDirection: "row",
  height: "100vh",
  fontFamily: "Segoe UI, sans-serif",
};

export const leftPanelStyle = {
  width: "40%",
  height: "100%",
  padding: "2rem",
  borderRight: "1px solid #ddd",
  overflowY: "auto",
  display: "flex",
  flexDirection: "column",
};

export const rightPanelStyle = {
  width: "60%",
  height: "100%",
  padding: "2rem",
  overflowY: "auto",
  backgroundColor: "#fff",
  boxShadow: "inset 0 0 10px rgba(0, 0, 0, 0.05)",
};

export const centeredStyle = {
  height: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontFamily: "Segoe UI, sans-serif",
};

export const buttonStyle = {
  padding: "10px 16px",
  backgroundColor: "#6c63ff",
  color: "white",
  border: "none",
  borderRadius: "6px",
  cursor: "pointer",
};


export const formContainerStyle = {
  width: "100%",
  maxWidth: "400px",
  margin: "0 auto",
  padding: "2rem",
  background: "#fff",
  borderRadius: "12px",
  boxShadow: "0 4px 10px rgba(0,0,0,0.05)",
  display: "flex",
  flexDirection: "column",
};

export const labelStyle = {
  fontWeight: "600",
  marginBottom: "6px",
  marginTop: "1rem",
};

export const inputStyle = {
  padding: "10px",
  fontSize: "1rem",
  border: "1px solid #ccc",
  borderRadius: "6px",
  marginBottom: "1rem",
};

export const textareaStyle = {
  ...inputStyle,
  minHeight: "100px",
  resize: "vertical",
};

export const panelStyle = {
  width: "280px",
  padding: "1.5rem",
  borderLeft: "1px solid #eee",
  background: "#f9f9fc",
  height: "100vh",
  overflowY: "auto",
  position: "fixed",
  right: 0,
  top: 0,
  fontFamily: "Segoe UI, sans-serif",
};