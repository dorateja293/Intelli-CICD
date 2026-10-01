import { commitService, projectService } from './api';
import { getCommits, getProjects, hasCommit, syncGithubCommitsFromApi, syncPipelinesFromApi } from './localData';

function normalizeRepo(repo) {
  return repo.trim().replace(/^https:\/\/github\.com\//, '').replace(/\.git$/, '').replace(/\/$/, '');
}

function estimateCommitDecision(filesChanged, churn) {
  const probability = Math.min(95, Math.round((filesChanged * 9) + (churn / 18)));

  if (probability > 55) {
    return { probability, decision: 'RUN_TESTS', timeSaved: 0 };
  }
  if (probability > 30) {
    return { probability, decision: 'PARTIAL_TESTS', timeSaved: 9 };
  }
  return { probability, decision: 'SKIP_TESTS', timeSaved: 18 };
}

async function fetchGitHubCommitsDirect(repo, limit = 100) {
  const repoPath = normalizeRepo(repo);
  const listResponse = await fetch(`https://api.github.com/repos/${repoPath}/commits?per_page=${limit}`, {
    headers: {
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
    },
  });

  if (!listResponse.ok) {
    throw new Error('GitHub repo not found, private, or rate limited.');
  }

  const commits = await listResponse.json();
  const detailedCommits = await Promise.all(
    commits.map(async (item) => {
      if (hasCommit(repoPath, item.sha)) {
        const shortSha = item.sha.slice(0, 7);
        const existing = getCommits().find((commit) => commit.sha === shortSha && commit.repo === repoPath);
        return existing ?? {
          sha: item.sha,
          project: repoPath.split('/').pop(),
          repo: repoPath,
          files_changed: 0,
          lines_added: 0,
          lines_deleted: 0,
          churn: 0,
          failure_probability: 0,
          decision: 'SKIP_TESTS',
          time: item.commit?.author?.date,
          time_saved_minutes: 0,
        };
      }

      let filesChanged = 0;
      let linesAdded = 0;
      let linesDeleted = 0;

      try {
        const detailsResponse = await fetch(`https://api.github.com/repos/${repoPath}/commits/${item.sha}`, {
          headers: {
            Accept: 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28',
          },
        });

        if (detailsResponse.ok) {
          const details = await detailsResponse.json();
          filesChanged = details.files?.length ?? 0;
          linesAdded = details.stats?.additions ?? 0;
          linesDeleted = details.stats?.deletions ?? 0;
        }
      } catch {
        // Keep the commit visible even if GitHub blocks per-commit stats.
      }

      const churn = linesAdded + linesDeleted;
      const { probability, decision, timeSaved } = estimateCommitDecision(filesChanged, churn);

      return {
        sha: item.sha,
        project: repoPath.split('/').pop(),
        repo: repoPath,
        files_changed: filesChanged,
        lines_added: linesAdded,
        lines_deleted: linesDeleted,
        churn,
        failure_probability: probability,
        decision,
        time: item.commit?.author?.date,
        time_saved_minutes: timeSaved,
      };
    })
  );

  return {
    data: {
      repo: repoPath,
      project: repoPath.split('/').pop(),
      commits: detailedCommits,
    },
  };
}

async function syncProjectFromGitHub(project) {
  try {
    return await fetchGitHubCommitsDirect(project.repo, 100);
  } catch {
    const response = await projectService.syncGitHubCommits({ repo: project.repo, limit: 100 });
    return response.data;
  }
}

export async function syncRealGitHubCommits() {
  const projects = getProjects();

  if (projects.length === 0) {
    return { commits: [], error: null };
  }

  try {
    const githubResults = await Promise.all(projects.map(syncProjectFromGitHub));
    const commits = syncGithubCommitsFromApi(githubResults);

    try {
      const [commitResponse, projectResponse] = await Promise.all([
        commitService.getCommits().catch(() => ({ data: { data: [] } })),
        projectService.getProjects().catch(() => ({ data: { data: [] } })),
      ]);
      syncPipelinesFromApi(commitResponse.data?.data ?? [], projectResponse.data?.data ?? []);
    } catch {
      // Public GitHub sync already populated the local dashboard state.
    }

    return { commits, error: null };
  } catch (error) {
    return {
      commits: [],
      error: error.message || 'Could not sync commits from GitHub.',
    };
  }
}
