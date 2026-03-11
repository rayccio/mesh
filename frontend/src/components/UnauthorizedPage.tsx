import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Icons } from '../constants';

export const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950 p-4">
      <div className="text-center max-w-md">
        <div className="text-red-500 text-6xl mb-4">🔒</div>
        <h1 className="text-3xl font-black text-white mb-2">Access Denied</h1>
        <p className="text-zinc-400 mb-6">
          You don't have the required permissions to access this page.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => navigate(-1)}
            className="px-6 py-3 bg-zinc-800 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-zinc-700 transition-colors"
          >
            Go Back
          </button>
          <button
            onClick={() => navigate('/dashboard')}
            className="px-6 py-3 bg-emerald-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-emerald-500 transition-colors"
          >
            Go to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
};
