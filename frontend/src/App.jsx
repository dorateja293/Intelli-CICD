import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ProjectProvider } from './context/ProjectContext';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import GitHubCallback from './pages/GitHubCallback';
import DashboardLayout from './layout/DashboardLayout';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import Commits from './pages/Commits';
import Analytics from './pages/Analytics';
import Predict from './pages/Predict';
import Logs from './pages/Logs';
import Profile from './pages/Profile';

export default function App() {
  return (
    <Router>
      <ProjectProvider>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/auth/github/callback" element={<GitHubCallback />} />
          
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/commits" element={<Commits />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/predict" element={<Predict />} />
            <Route path="/logs" element={<Logs />} />
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Routes>
      </ProjectProvider>
    </Router>
  );
}