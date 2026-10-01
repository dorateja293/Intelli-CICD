import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { projectService, githubService } from '../services/api';

const ProjectContext = createContext(null);

export function ProjectProvider({ children }) {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [githubStatus, setGithubStatus] = useState({
    connected: false,
    username: '',
    avatar_url: '',
    email: '',
    oauth_configured: true,
    mode: 'DISCONNECTED',
  });
  const [loading, setLoading] = useState(true);
  const [lastEvent, setLastEvent] = useState(null);

  // Fetch GitHub connection status for logged-in user
  const fetchGithubStatus = useCallback(async () => {
    try {
      const res = await githubService.getStatus();
      if (res.data?.data) {
        setGithubStatus(res.data.data);
      } else {
        setGithubStatus({
          connected: false,
          username: '',
          avatar_url: '',
          email: '',
          oauth_configured: true,
          mode: 'DISCONNECTED',
        });
      }
    } catch {
      setGithubStatus({
        connected: false,
        username: '',
        avatar_url: '',
        email: '',
        oauth_configured: false,
        mode: 'DISCONNECTED',
      });
    }
  }, []);

  // Fetch registered projects/repositories for logged-in user
  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      const res = await projectService.getProjects();
      const list = res.data?.data || [];
      setProjects(list);

      if (list.length > 0) {
        setSelectedProject((prev) => {
          if (!prev) return list[0];
          const found = list.find((p) => p.id === prev.id);
          return found || list[0];
        });
      } else {
        setSelectedProject(null);
      }
    } catch {
      setProjects([]);
      setSelectedProject(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      await fetchGithubStatus();
      await fetchProjects();
    };
    init();
  }, [fetchGithubStatus, fetchProjects]);

  // Connect to SSE Live Event Stream
  useEffect(() => {
    let eventSource = null;
    try {
      const sseUrl = import.meta.env.VITE_API_URL 
        ? `${import.meta.env.VITE_API_URL}/events/stream`
        : '/api/v1/events/stream';

      eventSource = new EventSource(sseUrl);

      eventSource.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          setLastEvent(parsed);
          if (parsed.event === 'pipeline_update' || parsed.event === 'sync_completed' || parsed.event === 'repository_registered') {
            fetchProjects();
          }
        } catch {
          // Ignore parse errors
        }
      };

      eventSource.onerror = () => {
        // SSE disconnected, will retry automatically
      };
    } catch {
      // EventSource not supported or unavailable
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [fetchProjects]);

  // Simulate Webhook Push
  const simulateWebhook = async (params = {}) => {
    try {
      const res = await githubService.simulateWebhook({
        repository_id: selectedProject?.id,
        event_type: params.event_type || 'workflow_run',
        conclusion: params.conclusion || 'success',
        commit_message: params.commit_message || `feat: automated commit simulated at ${new Date().toLocaleTimeString()}`,
        branch: params.branch || selectedProject?.default_branch || 'main',
      });
      await fetchProjects();
      return res.data?.data;
    } catch (err) {
      console.error('Webhook simulation failed:', err);
      throw err;
    }
  };

  return (
    <ProjectContext.Provider
      value={{
        projects,
        selectedProject,
        setSelectedProject,
        githubStatus,
        fetchGithubStatus,
        fetchProjects,
        loading,
        lastEvent,
        simulateWebhook,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}
