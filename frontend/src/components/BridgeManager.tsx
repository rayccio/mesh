import React from 'react';
import { useBridges } from '../contexts/BridgeContext';
import { Icons } from '../constants';

export const BridgeManager: React.FC = () => {
  const { bridges, loading, toggleBridge, restartBridge } = useBridges();

  if (loading) {
    return <div className="text-center py-4 text-zinc-500">Loading bridges...</div>;
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 p-8 opacity-5"><Icons.Globe /></div>
      <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">Bridge Controllers</h3>
      <p className="text-sm text-zinc-400">
        Enable or disable channel bridges. Only enabled bridges will appear in agent channel configuration.
      </p>
      <div className="space-y-4">
        {bridges.map(bridge => (
          <div key={bridge.type} className="flex items-center justify-between p-4 bg-zinc-950 rounded-xl border border-zinc-800">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-zinc-300 capitalize">{bridge.type}</span>
              <span className={`text-xs px-2 py-1 rounded-full ${
                bridge.status === 'running' ? 'bg-emerald-500/20 text-emerald-400' :
                bridge.status === 'exited' || bridge.status === 'not_found' ? 'bg-red-500/20 text-red-400' :
                bridge.status === 'starting' || bridge.status === 'restarting' ? 'bg-yellow-500/20 text-yellow-400 animate-pulse' :
                'bg-zinc-800 text-zinc-500'
              }`}>
                {bridge.status}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => restartBridge(bridge.type)}
                disabled={!bridge.enabled || bridge.status === 'restarting' || bridge.status === 'starting'}
                className="p-2 text-zinc-500 hover:text-emerald-400 transition-colors disabled:opacity-50"
                title="Restart Bridge"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={bridge.enabled}
                  onChange={e => toggleBridge(bridge.type, e.target.checked)}
                  disabled={bridge.status === 'starting' || bridge.status === 'stopping' || bridge.status === 'restarting'}
                />
                <div className="w-10 h-5 bg-zinc-800 rounded-full peer-checked:bg-emerald-600 transition-all relative">
                  <div className="absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-all peer-checked:left-6"></div>
                </div>
              </label>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
