import { useState, useEffect } from 'react'
import { Github, Trash2, GitBranch, Plus, X } from 'lucide-react'
import { repositoryService, getErrorMessage } from '../services/api'

function ConnectModal({ onClose, onConnected }) {
  const [fullName, setFullName] = useState('')
  const [branch, setBranch] = useState('main')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!fullName.trim()) return
    setError(null)
    setLoading(true)
    try {
      const { data } = await repositoryService.connect({ full_name: fullName.trim(), default_branch: branch || 'main' })
      onConnected(data)
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to connect repository.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70" onClick={onClose}>
      <div className="bg-[#161b22] border border-[#30363d] rounded-xl p-8 w-full max-w-md shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-bold text-[#c9d1d9]">Connect Repository</h3>
          <button onClick={onClose} className="text-[#8b949e] hover:text-[#c9d1d9]"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#c9d1d9] mb-2">Repository (owner/repo)</label>
            <input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="e.g. octocat/hello-world"
              className="w-full bg-[#0d1117] border border-[#30363d] text-[#c9d1d9] rounded-md px-4 py-2.5 outline-none focus:border-[#2ea043] focus:ring-1 focus:ring-[#2ea043] transition-colors"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#c9d1d9] mb-2">Default Branch</label>
            <input
              value={branch}
              onChange={(e) => setBranch(e.target.value)}
              placeholder="main"
              className="w-full bg-[#0d1117] border border-[#30363d] text-[#c9d1d9] rounded-md px-4 py-2.5 outline-none focus:border-[#2ea043] focus:ring-1 focus:ring-[#2ea043] transition-colors"
            />
          </div>
          {error && <p className="text-sm text-[#f85149] bg-[#3d1a1a] border border-[#6e2020] rounded-lg px-4 py-3">{error}</p>}
          <button
            type="submit"
            disabled={loading || !fullName.trim()}
            className="w-full bg-[#2ea043] hover:bg-[#2c974b] disabled:opacity-50 text-white font-bold py-3 rounded-lg transition-colors flex justify-center items-center gap-2"
          >
            {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : 'Connect'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default function ProjectsPage() {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showModal, setShowModal] = useState(false)

  const fetchRepos = async () => {
    setError(null)
    try {
      const { data } = await repositoryService.list()
      setRepos(data.repositories ?? data ?? [])
    } catch (err) {
      setError(getErrorMessage(err, 'Failed to load repositories.'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchRepos() }, [])

  const handleDelete = async (id) => {
    try {
      await repositoryService.delete(id)
      setRepos((prev) => prev.filter((r) => r.id !== id))
    } catch (err) {
      alert(getErrorMessage(err, 'Failed to delete repository.'))
    }
  }

  const handleConnected = (repo) => {
    setRepos((prev) => [repo, ...prev])
    setShowModal(false)
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 fade-in">
      {showModal && <ConnectModal onClose={() => setShowModal(false)} onConnected={handleConnected} />}

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="page-title">Projects</h1>
          <p className="page-sub">Manage connected repositories and view high-level metrics</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-[#2ea043] hover:bg-[#2c974b] text-white font-medium rounded-lg shadow-sm transition-colors flex items-center gap-2"
        >
          <Plus size={18} />
          Connect Repository
        </button>
      </div>

      {error && (
        <p className="text-sm text-[#f85149] bg-[#3d1a1a] border border-[#6e2020] rounded-lg px-4 py-3">{error}</p>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-8 h-8 border-2 border-[#2ea043]/30 border-t-[#2ea043] rounded-full animate-spin" />
        </div>
      ) : repos.length === 0 ? (
        <div className="text-center py-20 text-[#8b949e] border-2 border-dashed border-[#30363d] rounded-xl bg-[#0d1117]/30">
          <Github size={48} className="mx-auto text-[#30363d] mb-4" />
          <p className="font-medium text-[#c9d1d9] mb-1">No repositories connected</p>
          <p className="text-sm">Click <strong>Connect Repository</strong> to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {repos.map((repo) => (
            <div key={repo.id} className="bg-[#161b22] border border-[#30363d] rounded-xl p-6 hover:border-[#8b949e] transition-colors shadow-sm flex flex-col">
              <div className="flex justify-between items-start mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-[#0d1117] border border-[#30363d] flex items-center justify-center shadow-inner">
                    <Github size={20} className="text-[#c9d1d9]" />
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-base font-bold text-[#c9d1d9] truncate">{repo.full_name?.split('/')[1] ?? repo.full_name}</h3>
                    <p className="text-[#8b949e] text-xs font-mono truncate">{repo.full_name}</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-xs text-[#8b949e] bg-[#0d1117] border border-[#30363d]/50 rounded-lg px-3 py-2 mb-6">
                <GitBranch size={12} className="shrink-0" />
                <span className="truncate">{repo.default_branch}</span>
              </div>

              {repo.description && (
                <p className="text-xs text-[#8b949e] mb-6 leading-relaxed line-clamp-2">{repo.description}</p>
              )}

              <div className="flex items-center justify-between border-t border-[#30363d] pt-4 mt-auto">
                <span className="text-xs text-[#8b949e]">{repo.created_at ? new Date(repo.created_at).toLocaleDateString() : ''}</span>
                <button
                  onClick={() => handleDelete(repo.id)}
                  className="p-2 text-[#8b949e] hover:text-[#f85149] transition-colors"
                  title="Disconnect"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
