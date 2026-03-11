import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Icons } from '../constants';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { LoadingSpinner } from './LoadingSpinner';

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const navigate = useNavigate();
  const location = useLocation();
  const { login, gatewayEnabled, loading: authLoading } = useAuth();

  const from = (location.state as any)?.from?.pathname || '/';

  // If gateway is disabled, redirect to home
  useEffect(() => {
    if (!authLoading && !gatewayEnabled) {
      navigate('/', { replace: true });
    }
  }, [gatewayEnabled, authLoading, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await login(username, password);
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-zinc-950">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-zinc-950 relative overflow-hidden font-sans">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/10 blur-[120px] rounded-full" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-emerald-500/5 blur-[120px] rounded-full" />
        <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(#10b981 0.5px, transparent 0.5px)', backgroundSize: '30px 30px' }} />
      </div>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full max-w-md p-8 relative z-10"
      >
        <div className="text-center mb-12">
          <div className="inline-flex p-4 bg-emerald-500/10 text-emerald-500 rounded-2xl mb-6 shadow-inner border border-emerald-500/20">
            <Icons.Shield />
          </div>
          <h1 className="text-4xl font-black tracking-tighter text-white uppercase mb-2">
            Hive<span className="text-emerald-500">Bot</span>
          </h1>
          <p className="text-zinc-500 text-sm font-bold uppercase tracking-[0.2em]">Security Gateway v4.2</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest ml-1">Operator ID</label>
            <div className="relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600">
                <Icons.User />
              </div>
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-zinc-900/50 border border-zinc-800 rounded-2xl pl-12 pr-4 py-4 text-zinc-100 focus:border-emerald-500 focus:outline-none transition-all shadow-inner"
                placeholder="Enter UID..."
                required
                autoComplete="username"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest ml-1">Access Key</label>
            <div className="relative">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600">
                <Icons.Shield />
              </div>
              <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-zinc-900/50 border border-zinc-800 rounded-2xl pl-12 pr-4 py-4 text-zinc-100 focus:border-emerald-500 focus:outline-none transition-all shadow-inner"
                placeholder="••••••••"
                required
                autoComplete="current-password"
              />
            </div>
          </div>

          {error && (
            <motion.div 
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-[10px] font-black uppercase tracking-widest text-center"
            >
              {error}
            </motion.div>
          )}

          <button 
            type="submit" 
            disabled={isLoading}
            className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-800 text-white font-black uppercase tracking-widest py-4 rounded-2xl transition-all shadow-lg shadow-emerald-900/20 flex items-center justify-center gap-3 group"
          >
            {isLoading ? (
              <>
                <LoadingSpinner size="sm" />
                <span>Authenticating...</span>
              </>
            ) : (
              <>
                Authorize Session
                <span className="group-hover:translate-x-1 transition-transform">→</span>
              </>
            )}
          </button>
        </form>

        <div className="mt-12 pt-8 border-t border-zinc-900 flex flex-col items-center gap-4">
          <p className="text-[10px] text-zinc-600 font-bold uppercase tracking-widest">Authorized Access Only</p>
          <div className="flex gap-6">
            <div className="flex items-center gap-2 text-[9px] text-zinc-700 font-mono">
              <div className="w-1 h-1 rounded-full bg-emerald-500/50" />
              ENCRYPTED
            </div>
            <div className="flex items-center gap-2 text-[9px] text-zinc-700 font-mono">
              <div className="w-1 h-1 rounded-full bg-emerald-500/50" />
              ISOLATED
            </div>
            <div className="flex items-center gap-2 text-[9px] text-zinc-700 font-mono">
              <div className="w-1 h-1 rounded-full bg-emerald-500/50" />
              AUDITED
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};
