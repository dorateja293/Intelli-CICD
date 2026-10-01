import { Link, useNavigate } from 'react-router-dom';
import { authService } from '../services/api';
import { saveUser } from '../services/localData';
import { useState } from 'react';

export default function Login() {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  
  const handleLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const credentials = {
      email: formData.get('email'),
      password: formData.get('password'),
    };

    try {
      const response = await authService.login(credentials);
      const token = response.data?.data?.access_token || response.data?.access_token;
      if (!token) throw new Error('No token received');
      localStorage.setItem('intelli_ci_token', token);

      // Fetch user profile with the new token
      const meResponse = await authService.getMe();
      const user = meResponse.data?.data || meResponse.data;
      if (user) saveUser(user, token);

      navigate('/dashboard');
    } catch (err) {
      if (!credentials.email || !credentials.password) {
        setError('Enter email and password.');
        return;
      }
      setError(err.response?.data?.detail || err.message || 'Invalid email or password.');
    }
  };

  return (
    <div className="min-h-screen bg-githubBg flex items-center justify-center p-8">
      <div className="w-full max-w-md bg-githubCard border border-githubBorder rounded-xl p-10 shadow-xl flex flex-col gap-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white">Welcome Back</h2>
          <p className="text-githubTextSecondary text-sm mt-2">Sign in to your Intelli-CI account</p>
        </div>
        
        <form className="flex flex-col gap-5" onSubmit={handleLogin}>
          {error && <p className="rounded-lg border border-red-900/50 bg-red-900/20 px-4 py-3 text-sm text-red-300">{error}</p>}
          <div>
            <label className="block text-sm font-medium text-githubTextPrimary mb-2">Email</label>
            <input name="email" type="email" className="w-full bg-githubBg border border-githubBorder rounded-lg px-4 py-3 text-white focus:border-githubPrimary focus:outline-none transition-colors" placeholder="you@company.com" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-githubTextPrimary mb-2">Password</label>
            <input name="password" type="password" className="w-full bg-githubBg border border-githubBorder rounded-lg px-4 py-3 text-white focus:border-githubPrimary focus:outline-none transition-colors" placeholder="••••••••" required />
          </div>
          <button type="submit" className="w-full bg-githubPrimary text-white rounded-lg px-6 py-3 font-medium hover:bg-green-600 transition-colors mt-3">
            Login
          </button>
        </form>
        
        <p className="text-center text-sm text-githubTextSecondary">
          Don't have an account? <Link to="/signup" className="text-githubPrimary hover:underline">Sign up</Link>
        </p>
      </div>
    </div>
  );
}
