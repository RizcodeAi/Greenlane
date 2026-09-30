import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../store/auth';
import { register, getMe } from '../services/api';

type Step = 1 | 2 | 3;

export default function Register() {
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();
  const [step, setStep] = useState<Step>(1);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [orgName, setOrgName] = useState('');
  const [industry, setIndustry] = useState('');
  const [inviteEmails, setInviteEmails] = useState('');
  const [inviteRole, setInviteRole] = useState('Compliance Officer');

  const handleNext = () => {
    if (step === 1 && (!email || !password || !fullName)) { setError('Please fill all fields'); return; }
    setError('');
    setStep((step + 1) as Step);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await register({
        email, password, full_name: fullName,
        org_name: orgName, industry,
        invite_emails: inviteEmails ? inviteEmails.split(',').map(e => e.trim()).filter(Boolean) : undefined,
      });
      const userRes = await getMe();
      authLogin(userRes.data.user, userRes.data.organization);
      navigate('/dashboard');
    } catch {
      setError('Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="bg-navy-900 border border-navy-800 rounded-lg p-8 w-full max-w-md shadow-lg">
        <h1 className="text-2xl font-bold mb-6 text-center text-navy-50">Create Account</h1>
        <div className="flex gap-2 mb-6">
          {[1, 2, 3].map((s) => (
            <div key={s} className={`flex-1 h-1 rounded-full ${step === s ? 'bg-green-500' : 'bg-navy-800'}`} />
          ))}
        </div>
        {error && <p className="text-red-400 text-sm mb-4 text-center">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          {step === 1 && (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Full Name</label>
                <input type="text" value={fullName} onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500" required />
              </div>
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
              <button type="button" onClick={handleNext} className="w-full bg-green-600 hover:bg-green-500 text-white font-semibold py-2 rounded">
                Next: Organization
              </button>
            </>
          )}
          {step === 2 && (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Organization Name</label>
                <input type="text" value={orgName} onChange={(e) => setOrgName(e.target.value)}
                  className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500" required />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Industry</label>
                <select value={industry} onChange={(e) => setIndustry(e.target.value)}
                  className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500" required>
                  <option value="">Select industry</option>
                  <option value="shipping">Shipping</option>
                  <option value="logistics">Logistics</option>
                  <option value="maritime">Maritime</option>
                  <option value="energy">Energy</option>
                  <option value="manufacturing">Manufacturing</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button type="button" onClick={() => setStep(1)} className="flex-1 bg-navy-700 hover:bg-navy-600 text-white py-2 rounded">Back</button>
                <button type="button" onClick={handleNext} className="flex-1 bg-green-600 hover:bg-green-500 text-white font-semibold py-2 rounded">Next: Invite</button>
              </div>
            </>
          )}
          {step === 3 && (
            <>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Invite Team Members (comma-separated emails)</label>
                <textarea value={inviteEmails} onChange={(e) => setInviteEmails(e.target.value)}
                  className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500" rows={3}
                  placeholder="colleague@example.com, manager@example.com" />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Role for Invited Members</label>
                <select value={inviteRole} onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full bg-navy-800 border border-navy-700 rounded px-3 py-2 text-white focus:outline-none focus:border-green-500">
                  <option value="Compliance Officer">Compliance Officer</option>
                  <option value="Fleet Manager">Fleet Manager</option>
                  <option value="Operator">Operator</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button type="button" onClick={() => setStep(2)} className="flex-1 bg-navy-700 hover:bg-navy-600 text-white py-2 rounded">Back</button>
                <button type="submit" disabled={loading} className="flex-1 bg-green-600 hover:bg-green-500 disabled:bg-navy-700 text-white font-semibold py-2 rounded">
                  {loading ? 'Creating...' : 'Create Account'}
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  );
}
