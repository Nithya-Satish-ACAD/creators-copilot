import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Courses from "./pages/Courses";
import ErrorBoundary from "./components/ErrorBoundary";
import NotFound from "./pages/NotFound";
import ForgotPassword from "./pages/ForgotPassword";
import AssetStudio from './pages/AssetStudio';

function App() {
  return (
    <ErrorBoundary>
        <Router>
          <Routes>
            <Route path="/" element={<Navigate to="/login" />} />
            <Route path="/courses" element={<Courses />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/studio/:feature" element={<AssetStudio />} />
            <Route path="/login" element={<Login />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Router>
    </ErrorBoundary>
  );
}

export default App;
