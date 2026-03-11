import React, { useState } from 'react';
import { Icons } from '../constants';
import { useAuth } from '../contexts/AuthContext';
import { LoadingSpinner } from './LoadingSpinner';

interface ChangePasswordModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const ChangePasswordModal: React.FC<ChangePasswordModalProps> = ({ onClose, onSuccess }) => {
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { user, changePassword } = useAuth();
  const isFirstTime = user && !user.password_changed;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }
    
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      // For first-time setup, oldPassword can be anything (it will be ignored)
      await changePassword(oldPassword, newPassword);
      onSuccess();
    } catch (err: any) {
      setError(err.message || 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 w-full max-w-md space-y-6 shadow-2xl animate-in zoom-in-95 duration-200">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-black uppercase tracking-tighter">
            {isFirstTime ? 'Set Admin Password' : 'Change Password'}
          </h3>
          <button onClick={onClose} className="text-zinc-500 hover:text-white transition-colors"><Icons.X /></button>
        </div>

        {isFirstTime ? (
          <p className="text-sm text-zinc-400">
            You are using the default admin account. Please set a password to secure your account and enable the login gateway.
          </p>
        ) : (
          <p className="text-sm text-zinc-400">
            Enter your current password and choose a new one.
          </p>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isFirstTime && (
            <div>
              <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">Current Password</label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all"
                required
                autoComplete="current-password"
              />
            </div>
          )}

          <div>
            <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all"
              required
              autoComplete="new-password"
            />
          </div>

          <div>
            <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all"
              required
              autoComplete="new-password"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-[10px] font-black uppercase tracking-widest text-center">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-emerald-900/20 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span>{isFirstTime ? 'Setting...' : 'Changing...'}</span>
                </>
              ) : (
                isFirstTime ? 'Set Password' : 'Change Password'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
