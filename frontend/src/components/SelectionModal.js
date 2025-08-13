import React from "react";
import Modal from "./Modal";

export default function SelectionModal({
  open,
  title,
  options,
  selectedOption,
  onSelect,
  onClose,
  onCreate
}) {
  return (
    <Modal open={open} onClose={onClose}>
      <div style={{ fontWeight: 700, fontSize: 22, marginBottom: 8 }}>{title}</div>
      <div style={{ fontWeight: 500, fontSize: 16, marginBottom: 18 }}>Select {title} option</div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 18 }}>
        {options.map((opt, i) => (
          <label key={opt.label} style={{
            border: selectedOption === i ? "2px solid #1976d2" : "1px solid #ddd",
            borderRadius: 8,
            padding: 10,
            minWidth: 150,
            flex: "1 1 38%",
            background: selectedOption === i ? "#f0f7ff" : "#fafbfc",
            cursor: "pointer",
            display: "flex",
            flexDirection: "column",
            gap: 10,
            boxShadow: selectedOption === i ? "0 2px 8px #1976d222" : "none"
          }}>
            <input
              type="radio"
              name="selection-option"
              checked={selectedOption === i}
              onChange={() => onSelect(i)}
              style={{ marginBottom: 6 }}
            />
            <span style={{ fontWeight: 600 }}>{opt.label}</span>
            <span style={{ color: "#444", fontSize: 13 }}>{opt.desc}</span>
          </label>
        ))}
      </div>
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 12 }}>
        <button onClick={onClose} style={{ padding: "8px 18px", border: "1px solid #bbb", background: "#fff", borderRadius: 6 }}>Cancel</button>
        <button
          onClick={() => onCreate(options[selectedOption])}
          style={{ padding: "8px 18px", background: "#222", color: "#fff", borderRadius: 6, border: "none" }}
        >
          Create
        </button>
      </div>
    </Modal>
  );
}
