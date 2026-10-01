const DATA_VERSION_KEY = 'intelli_ci_data_version';
const PROJECTS_KEY = 'intelli_ci_projects';
const COMMITS_KEY = 'intelli_ci_commits';
const USER_KEY = 'intelli_ci_user';
const TOKEN_KEY = 'intelli_ci_token';
const CURRENT_DATA_VERSION = 'real-project-zero-v1';

function resetOldDemoData() {
  if (localStorage.getItem(DATA_VERSION_KEY) !== CURRENT_DATA_VERSION) {
    localStorage.setItem(DATA_VERSION_KEY, CURRENT_DATA_VERSION);
    localStorage.removeItem(PROJECTS_KEY);
    localStorage.removeItem(COMMITS_KEY);
  }
}

function readJson(key, fallback) {
  resetOldDemoData();

  try {
    const value = localStorage.getItem(key);
    return value ? JSON.parse(value) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson(key, value) {
  resetOldDemoData();
  localStorage.setItem(key, JSON.stringify(value));
}

function normalizeRepo(input) {
  return input.trim().replace(/^https:\/\/github\.com\//, '').replace(/\.git$/, '').replace(/\/$/, '');
}

function getCommitKey(commit) {
  const sha = String(commit.sha || '').slice(0, 7).toLowerCase();
  return sha;
}

function dedupeCommits(commits) {
  const seen = new Set();

  return commits.filter((commit) => {
    const key = getCommitKey(commit);
    if (!commit.sha || seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

function getProjectCommits(commits, project) {
  return commits.filter((commit) => (
    commit.repo?.toLowerCase() === project.repo.toLowerCase()
    || commit.project?.toLowerCase() === project.name.toLowerCase()
  ));
}

export function hasCommit(repo, sha) {
  const key = String(sha || '').slice(0, 7).toLowerCase();
  const repoName = normalizeRepo(repo).toLowerCase();

  return getCommits().some((commit) => (
    String(commit.sha || '').slice(0, 7).toLowerCase() === key
    && normalizeRepo(commit.repo || '').toLowerCase() === repoName
  ));
}

export function getProjects() {
  return readJson(PROJECTS_KEY, []);
}

export function addProject(repoInput) {
  const repo = normalizeRepo(repoInput);
  if (!repo || !repo.includes('/')) {
    throw new Error('Enter a GitHub repo as owner/repository.');
  }

  const existing = getProjects().find((project) => project.repo.toLowerCase() === repo.toLowerCase());
  if (existing) {
    throw new Error('This repository is already added.');
  }

  const name = repo.split('/').pop();
  const project = {
    id: `project-${Date.now()}`,
    name,
    repo,
    description: 'GitHub repository connected to Intelli-CI demo pipeline.',
    commits: 0,
    filesChanged: 0,
    skipRate: '0%',
    timeSaved: 0,
    status: 'Connected',
    lastRun: 'Waiting for first commit',
  };
  const projects = [project, ...getProjects()];

  writeJson(PROJECTS_KEY, projects);
  return project;
}

export function deleteProject(projectId) {
  const project = getProjects().find((item) => item.id === projectId);
  const projects = getProjects().filter((item) => item.id !== projectId);
  const commits = getCommits().filter((commit) => commit.repo !== project?.repo);

  writeJson(PROJECTS_KEY, projects);
  writeJson(COMMITS_KEY, commits);
  return projects;
}

export function clearAllProjects() {
  writeJson(PROJECTS_KEY, []);
  writeJson(COMMITS_KEY, []);
}

export function syncPipelinesFromApi(pipelines = [], repositories = []) {
  if (!Array.isArray(pipelines) || pipelines.length === 0) {
    return getCommits();
  }

  const repoLookup = new Map(
    repositories.map((repo) => [
      String(repo.id),
      {
        name: repo.name,
        repo: repo.url?.replace(/^https:\/\/github\.com\//, '').replace(/\.git$/, '') ?? repo.name,
      },
    ])
  );
  const localProjects = getProjects();
  const syncedCommits = dedupeCommits(pipelines.map((pipeline) => {
    const repoInfo = repoLookup.get(String(pipeline.repo_id));
    const matchingProject = localProjects.find((project) => project.repo === repoInfo?.repo || project.name === repoInfo?.name);
    const projectName = matchingProject?.name ?? repoInfo?.name ?? 'GitHub Project';
    const repo = matchingProject?.repo ?? repoInfo?.repo ?? String(pipeline.repo_id);
    const durationMinutes = pipeline.time_saved_minutes ?? Math.max(0, Math.round((pipeline.duration_seconds ?? 0) / 60));

    return {
      sha: pipeline.commit_sha?.slice(0, 7) ?? String(pipeline.id).slice(0, 7),
      project: projectName,
      repo,
      files: pipeline.files_changed ?? pipeline.files ?? 0,
      linesAdded: pipeline.lines_added ?? 0,
      linesDeleted: pipeline.lines_deleted ?? 0,
      churn: pipeline.code_churn ?? pipeline.churn ?? 0,
      prob: pipeline.failure_probability ?? 0,
      decision: pipeline.decision ?? (pipeline.status === 'FAILED' ? 'RUN_TESTS' : 'SKIP_TESTS'),
      time: pipeline.created_at ? new Date(pipeline.created_at).toLocaleString() : 'Just now',
      timeSaved: durationMinutes,
    };
  }));
  const existingCommits = dedupeCommits(readJson(COMMITS_KEY, []));
  const merged = dedupeCommits([
    ...syncedCommits,
    ...existingCommits,
  ]);

  writeJson(COMMITS_KEY, merged);

  if (repositories.length > 0) {
    const projects = repositories.map((repo) => {
      const repoName = repo.url?.replace(/^https:\/\/github\.com\//, '').replace(/\.git$/, '') ?? repo.name;
      const projectCommits = getProjectCommits(merged, { repo: repoName, name: repo.name });
      const optimized = projectCommits.filter((commit) => commit.decision !== 'RUN_TESTS').length;
      const totalSaved = projectCommits.reduce((sum, commit) => sum + commit.timeSaved, 0);

      return {
        id: `repo-${repo.id}`,
        name: repo.name,
        repo: repoName,
        description: 'GitHub repository connected to Intelli-CI pipeline.',
        commits: projectCommits.length,
        filesChanged: projectCommits[0]?.files ?? 0,
        skipRate: `${Math.round((optimized / Math.max(projectCommits.length, 1)) * 100)}%`,
        timeSaved: totalSaved,
        status: projectCommits.length ? 'Synced' : 'Connected',
        lastRun: projectCommits[0] ? `Commit ${projectCommits[0].sha} synced` : 'Waiting for first commit',
      };
    });

    writeJson(PROJECTS_KEY, projects);
  }

  return merged;
}

export function syncGithubCommitsFromApi(syncResults = []) {
  const results = Array.isArray(syncResults) ? syncResults : [syncResults];
  const incomingCommits = dedupeCommits(results.flatMap((result) => {
    const data = result?.data ?? result;
    const repo = data?.repo;
    const project = data?.project ?? repo?.split('/').pop();

    return (data?.commits ?? []).map((commit) => ({
      sha: commit.sha?.slice(0, 7) ?? '',
      project: commit.project ?? project ?? 'GitHub Project',
      repo: commit.repo ?? repo,
      files: commit.files_changed ?? commit.files ?? 0,
      linesAdded: commit.lines_added ?? commit.linesAdded ?? 0,
      linesDeleted: commit.lines_deleted ?? commit.linesDeleted ?? 0,
      churn: commit.churn ?? 0,
      prob: commit.failure_probability ?? commit.prob ?? 0,
      decision: commit.decision ?? 'SKIP_TESTS',
      time: commit.time ? new Date(commit.time).toLocaleString() : 'Just now',
      timeSaved: commit.time_saved_minutes ?? commit.timeSaved ?? 0,
    }));
  }).filter((commit) => commit.sha));

  if (incomingCommits.length === 0) {
    return getCommits();
  }

  const existingCommits = dedupeCommits(readJson(COMMITS_KEY, []));
  const merged = dedupeCommits([
    ...incomingCommits,
    ...existingCommits,
  ]);
  const projects = getProjects().map((project) => {
    const projectCommits = getProjectCommits(merged, project);
    const optimized = projectCommits.filter((commit) => commit.decision !== 'RUN_TESTS').length;

    return {
      ...project,
      commits: projectCommits.length,
      filesChanged: projectCommits[0]?.files ?? 0,
      skipRate: `${Math.round((optimized / Math.max(projectCommits.length, 1)) * 100)}%`,
      timeSaved: projectCommits.reduce((sum, commit) => sum + commit.timeSaved, 0),
      status: projectCommits.length ? 'Synced' : project.status,
      lastRun: projectCommits[0] ? `Commit ${projectCommits[0].sha} synced from GitHub` : project.lastRun,
    };
  });

  writeJson(COMMITS_KEY, merged);
  writeJson(PROJECTS_KEY, projects);
  return merged;
}

export function getCommits(projectName) {
  const commits = dedupeCommits(readJson(COMMITS_KEY, []));
  return projectName ? commits.filter((commit) => commit.project === projectName) : commits;
}

export function getProjectAnalytics(projectName) {
  const commits = getCommits(projectName);
  const total = commits.length || 1;
  const skipped = commits.filter((commit) => commit.decision === 'SKIP_TESTS').length;
  const partial = commits.filter((commit) => commit.decision === 'PARTIAL_TESTS').length;
  const run = commits.filter((commit) => commit.decision === 'RUN_TESTS').length;
  const avgRisk = commits.length
    ? Math.round(commits.reduce((sum, commit) => sum + commit.prob, 0) / commits.length)
    : 0;

  return {
    avgRisk,
    filesChanged: commits[0]?.files ?? 0,
    skipRate: Math.round(((skipped + partial) / total) * 100),
    timeSaved: commits.reduce((sum, commit) => sum + commit.timeSaved, 0),
    decisionData: [
      { name: 'Run tests', value: run, color: '#f85149' },
      { name: 'Partial', value: partial, color: '#d29922' },
      { name: 'Skipped', value: skipped, color: '#2ea043' },
    ],
  };
}

export function getDashboardStats() {
  const projects = getProjects();
  const commits = getCommits();
  const optimized = commits.filter((commit) => commit.decision !== 'RUN_TESTS').length;
  const highRisk = commits.filter((commit) => commit.prob > 55).length;

  return {
    projects,
    commits,
    skipped: optimized,
    highRisk,
    filesChanged: commits[0]?.files ?? 0,
    latestCommit: commits[0] ?? null,
    timeSaved: commits.reduce((sum, commit) => sum + commit.timeSaved, 0),
    skipRate: Math.round((optimized / Math.max(commits.length, 1)) * 100),
  };
}

export function saveUser(user, token = 'local-demo-token') {
  localStorage.setItem(TOKEN_KEY, token);
  writeJson(USER_KEY, user);
}

export function getStoredUser() {
  return readJson(USER_KEY, null);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
