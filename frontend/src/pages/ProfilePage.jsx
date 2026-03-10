import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { profileService } from '../services/api'
import Avatar from '../components/Avatar'
import FormInput from '../components/FormInput'
import Button from '../components/Button'

export default function ProfilePage() {
  const { user, updateUser } = useAuth()

  // Profile form state
  const [name, setName] = useState(user?.name ?? '')
  const email = user?.email ?? ''
  const [profileMsg, setProfileMsg] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)

  // Password form state
  const [currentPw, setCurrentPw] = useState('')
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [pwError, setPwError] = useState(null)
  const [pwMsg, setPwMsg] = useState(null)
  const [pwLoading, setPwLoading] = useState(false)

  async function handleProfileSave(e) {
    e.preventDefault()
    if (!name.trim()) return
    setProfileLoading(true)
    try {
      const { data } = await profileService.update(name.trim())
      updateUser({ ...user, name: data.name })
      setProfileMsg('Profile updated successfully.')
      setTimeout(() => setProfileMsg(null), 3000)
    } catch (err) {
      setProfileMsg(err.response?.data?.detail || 'Update failed.')
    } finally {
      setProfileLoading(false)
    }
  }

  async function handlePasswordChange(e) {
    e.preventDefault()
    setPwError(null)
    if (newPw.length < 8) { setPwError('New password must be at least 8 characters.'); return }
    if (newPw !== confirmPw) { setPwError('Passwords do not match.'); return }
    setPwLoading(true)
    try {
      await profileService.changePassword(currentPw, newPw)
      setPwMsg('Password changed successfully.')
      setCurrentPw(''); setNewPw(''); setConfirmPw('')
      setTimeout(() => setPwMsg(null), 3000)
    } catch (err) {
      setPwError(err.response?.data?.detail || 'Password change failed.')
    } finally {
      setPwLoading(false)
    }
  }

  const joinedDate = user?.created_at
    ? new Date(user.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
    : 'Demo Account'

  return (
    <div className="max-w-3xl mx-auto space-y-7 sm:space-y-8 fade-in">
      {/* Header */}
      <div>
        <h1 className="page-title">Profile</h1>
        <p className="page-sub">Manage your account settings and preferences</p>
      </div>

      {/* Identity card */}
      <div
        className="rounded-xl border p-6 flex items-center gap-5 card-hover"
        style={{ background: '#161B22', borderColor: '#30363D' }}
      >
        <Avatar name={user?.name ?? 'Demo User'} size="lg" />
        <div>
          <p className="text-lg font-semibold" style={{ color: '#E6EDF3' }}>{user?.name ?? 'Demo User'}</p>
          <p className="text-sm" style={{ color: '#8B949E' }}>{user?.email ?? 'demo@intelli-ci.dev'}</p>
          <p className="text-xs mt-1" style={{ color: '#8B949E' }}>Joined {joinedDate}</p>
        </div>
      </div>

      {/* Edit profile */}
      <div className="panel">
        <div className="panel-header">
          <h2 className="section-title">Edit Profile</h2>
        </div>
        <form onSubmit={handleProfileSave} className="p-6 space-y-5">
          <FormInput label="Full Name" type="text" value={name} onChange={(e) => setName(e.target.value)} required />
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium" style={{ color: '#E6EDF3' }}>Email Address</label>
            <input
              type="email"
              value={email}
              disabled
              className="w-full px-4 py-2.5 rounded-lg border text-sm cursor-not-allowed opacity-50 min-h-[46px]"
              style={{ background: '#0D1117', borderColor: '#30363D', color: '#8B949E' }}
            />
            <p className="text-xs" style={{ color: '#8B949E' }}>Email address cannot be changed.</p>
          </div>
          {profileMsg && (
            <p className="text-sm" style={{ color: '#3fb950' }}>{profileMsg}</p>
          )}
          <div className="flex justify-end">
            <Button type="submit" variant="primary" loading={profileLoading}>Save Changes</Button>
          </div>
        </form>
      </div>

      {/* Change password */}
      <div className="panel">
        <div className="panel-header">
          <h2 className="section-title">Change Password</h2>
        </div>
        <form onSubmit={handlePasswordChange} className="p-6 space-y-5">
          <FormInput label="Current Password" type="password" value={currentPw} onChange={(e) => setCurrentPw(e.target.value)} required />
          <FormInput label="New Password" type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} required />
          <FormInput
            label="Confirm New Password"
            type="password"
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            error={pwError}
            required
          />
          {pwMsg && <p className="text-sm" style={{ color: '#3fb950' }}>{pwMsg}</p>}
          <div className="flex justify-end">
            <Button type="submit" variant="primary" loading={pwLoading}>Update Password</Button>
          </div>
        </form>
      </div>
    </div>
  )
}
