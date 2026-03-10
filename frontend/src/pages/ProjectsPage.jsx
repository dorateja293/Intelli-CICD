import { useEffect, useState } from 'react'
import { FolderGit2, Plus, Trash2, GitBranch, AlertCircle } from 'lucide-react'
import { repositoryService, getErrorMessage } from '../services/api'
import Button from '../components/Button'

export default function ProjectsPage() {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Connect form state
  const [showForm, setShowForm] = useState(false)
  const [fullName, setFullName] = useState('')
  const [branch, setBranch] = useState('main')
  const [description, setDescription] = useState('')
  const [connecting, setConnecting] = useState(false)
  const [connectError, setConnectError] = useState('')

  const fetchRepos = () => {
    setLoading(true)
    repositoryService
      .list()
      .then(({ data }) => setRepos(data.repositories ?? []))
      .catch((err) => setError(getErrorMessage(err, 'Failed to load projects')))
      .finally(() => setLoading(false))
  }

  useEffect(fetchRepos, [])

  const handleConnect = async (e) => {
    e.preventDefault()
    if (!fullName.trim() || !fullName.includes('/')) {
      setConnectError('Enter a valid repository name in owner/repo format')
      return
    }
    setConnecting(true)
    setConnectError('')
    try {
      await repositoryService.connect({
        full_name: fullName.trim(),
        default_branch: branch.trim() || 'main',
        description: description.trim(),
      })
      setFullName('')
      setBranch('main')
      setDescription('')
      setShowForm(false)
      fetchRepos()
    } catch (err) {
      setConnectError(getErrorMessage(err, 'Failed to connect repository'))
    } finally {
      setConnecting(false)
    }
  }

  const handleDelete = async (repoId, repoName) => {
    if (!window.confirm(`Remove ${repoName}? This will also delete all associated commits and predictions.`)) return
    try {
      await repositoryService.delete(repoId)
      setRepos((prev) => prev.filter((r) => r.id !== repoId))
    } catch (err) {
      alert(getErrorMessage(err, 'Failed to remove project'))
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5 sm:space-y-6 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Projects</h1>
          <p className="page-sub">Connect GitHub repositories to optimize CI pipeline decisions</p>
        </div>
        <Button icon={Plus} onClick={() => { setShowForm((v) => !v); setConnectError('') }}>
          Connect repo
        </Button>
      </div>

      {/* Connect form */}
      {showForm && (
        <div className="panel">
          <div className="panel-header">
            <h2 className="section-title">Connect a new repository</h2>
          </div>
          <form onSubmit={handleConnect} className="p-6 space-y-5">
            {connectError && (
              <div
                className="flex items-center gap-2 px-4 py-3 rounded-md text-sm bg-[#f8514926] text-[#f85149] border border-[#f8514940]"
              >
                <AlertCircle size={16} strokeWidth={2} />
                {connectError}
              </div>
            )}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wider text-[var(--color-text-secondary)]">
                  Repository <span className="text-[#f85149]">*</span>
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="owner/repository"
                  required
                  className="w-full px-4 py-2.5 rounded-lg text-sm border bg-[#0d1117] outline-none transition-all duration-200 text-[var(--color-text-primary)] border-[#30363d] focus:border-[#2ea043] focus:ring-1 focus:ring-[#2ea043] hover:border-[#8b949e]"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wider text-[var(--color-text-secondary)]">
                  Default branch
                </label>
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  placeholder="main"
                  className="w-full px-4 py-2.5 rounded-lg text-sm border bg-[#0d1117] outline-none transition-all duration-200 text-[var(--color-text-primary)] border-[#30363d] focus:border-[#2ea043] focus:ring-1 focus:ring-[#2ea043] hover:border-[#8b949e]"
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wider text-[var(--color-text-secondary)]">
                Description <span className="font-normal normal-case">(optional)</span>
              </label>
              <input
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Short description of the repository"
                className="w-full px-4 py-2.5 rounded-lg text-sm border bg-[#0d1117] outline-none transition-all duration-200 text-[var(--color-text-primary)] border-[#30363d] focus:border-[#2ea043] focus:ring-1 focus:ring-[#2ea043] hover:border-[#8b949e]"
              />
            </div>
            <div className="flex items-center gap-3 pt-1">
              <Button type="submit" variant="primary" loading={connecting}>
                {connecting ? 'Connecting…' : 'Connect repository'}
              </Button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2.5 rounded-lg text-sm transition-colors font-medium text-[var(--color-text-secondary)] hover:bg-[#21262d] hover:text-white"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Repository list */}
      <div className="panel">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <FolderGit2 size={16} className="text-[var(--color-text-secondary)]" />
            <h2 className="section-title">Connected repositories</h2>
          </div>
          <span className="text-xs font-medium text-[var(--color-text-secondary)]">
            {repos.length} repo{repos.length !== 1 ? 's' : ''}
          </span>
        </div>

        {loading ? (
          <div className="p-5 space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="skeleton h-16 w-full rounded-lg" />
            ))}
          </div>
        ) : error ? (
          <div className="p-8 text-center text-sm text-[#f85149]">
            {error}
          </div>
        ) : repos.length === 0 ? (
          <div className="p-12 text-center flex flex-col items-center">
            <FolderGit2 size={40} className="mb-4 text-[#30363d]" strokeWidth={1.5} />
            <p className="text-sm font-medium text-[var(--color-text-primary)]">No repositories connected</p>
            <p className="text-sm mt-1.5 text-[var(--color-text-secondary)] max-w-sm mx-auto">
              Click "Connect repo" to link a GitHub repository and start optimizing your CI pipeline.
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-[#30363d] bg-transparent">
            {repos.map((repo) => (
              <li
                key={repo.id}
                className="flex items-center gap-4 px-6 py-5 transition-colors hover:bg-[#21262d]"
              >
                <FolderGit2 size={18} className="text-[#2f81f7] flex-shrink-0" strokeWidth={2} />
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm truncate text-[var(--color-text-primary)]">
                    {repo.full_name}
                  </p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="flex items-center gap-1.5 text-xs font-medium text-[var(--color-text-secondary)]">
                      <GitBranch size={12} strokeWidth={2} className="text-[var(--color-text-secondary)]" />
                      {repo.default_branch}
                    </span>
                    {repo.description && (
                      <span className="text-xs truncate text-[var(--color-text-secondary)]">
                        {repo.description}
                      </span>
                    )}
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => handleDelete(repo.id, repo.full_name)}
                  className="ml-auto p-2 rounded-lg transition-colors text-[var(--color-text-secondary)] hover:text-[#f85149] hover:bg-[#f8514926]"
                  title="Remove repository"
                >
                  <Trash2 size={16} strokeWidth={2} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

