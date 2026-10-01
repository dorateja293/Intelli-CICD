import React, { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { githubService } from '../services/api';
import { GitBranch, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function GitHubCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus]   = useState('processing');
  const [errorMsg, setErrorMsg] = useState('');

  // Guard against React StrictMode double-invocation in development.
  // A ref persists across the remount cycle so the code is only exchanged once.
  const exchangedRef = useRef(false);

  useEffect(() => {
    if (exchangedRef.current) return;   // already running / ran
    exchangedRef.current = true;

    const code  = searchParams.get('code');
    const state = searchParams.get('state');

    if (!code) {
      setStatus('error');
      setErrorMsg('No authorization code received from GitHub.');
      return;
    }

    const exchange = async () => {
      try {
        const redirectUri = window.location.origin + '/auth/github/callback';
        await githubService.handleCallback(code, state, redirectUri);
        setStatus('success');
        setTimeout(() => navigate('/projects?connected=true'), 1500);
      } catch (err) {
        setStatus('error');
        const detail = err.response?.data?.detail || err.message || 'OAuth exchange failed.';
        setErrorMsg(detail);
      }
    };

    exchange();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // run once on mount only — intentionally empty deps

  return (
    <div className="min-h-screen bg-githubBg flex items-center justify-center p-6 text-white">
      <div className="w-full max-w-md bg-githubCard border border-githubBorder rounded-2xl p-8 shadow-2xl text-center flex flex-col items-center">
        <div className="w-16 h-16 rounded-full bg-githubBg border border-githubBorder flex items-center justify-center mb-6 text-githubPrimary">
          <GitBranch size={32} />
        </div>

        {status === 'processing' && (
          <>
            <h2 className="text-xl font-bold mb-2">Connecting GitHub…</h2>
            <p className="text-sm text-githubTextSecondary mb-6">
              Exchanging authorization code and fetching your profile.
            </p>
            <Loader2 size={32} className="animate-spin text-githubPrimary" />
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3">
              <CheckCircle size={28} />
            </div>
            <h2 className="text-xl font-bold mb-2">GitHub Connected!</h2>
            <p className="text-sm text-githubTextSecondary mb-4">
              Redirecting to your repository manager…
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-12 h-12 rounded-full bg-rose-500/10 text-rose-400 flex items-center justify-center mb-3">
              <AlertCircle size={28} />
            </div>
            <h2 className="text-xl font-bold mb-2">Connection Failed</h2>
            <p className="text-sm text-rose-400 mb-6 break-words">{errorMsg}</p>
            <button
              onClick={() => navigate('/projects')}
              className="px-6 py-2.5 bg-githubPrimary hover:bg-emerald-600 text-white font-medium text-sm rounded-lg transition-colors"
            >
              Back to Projects
            </button>
          </>
        )}
      </div>
    </div>
  );
}
