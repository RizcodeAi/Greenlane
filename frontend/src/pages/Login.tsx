import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../store/auth';
import { login, getMe } from '../services/api';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await login({ email, password });
      const userRes = await getMe();
      authLogin(userRes.data.user, userRes.data.organization);
      navigate('/dashboard');
    } catch {
      setError('Invalid credentials. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="bg-navy-900 border border-navy-800 rounded-lg p-8 w-full max-w-md shadow-lg">
        <h1 className="text-2xl font-bold mb-6 text-center text-navy-50">GreenLane Maritime</h1>
        <h2 className="text-lg text-slate-400 mb-6 text-center">Sign in to your account</h2>
        {error && <p className="text-red-400 text-sm mb-4 text-center">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500" required />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500" required />
          </div>
          <button type="submit" disabled={loading}
            className="w-full bg-green-600 hover:bg-green-500 disabled:bg-navy-700 text-white font-semibold py-2 rounded transition-colors">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
}
