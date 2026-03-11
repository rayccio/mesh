
import React from 'react';
import { Agent, AgentStatus } from '../types';

export const GlobalStats: React.FC<{ agents: Agent[] }> = ({ agents }) => {
  const activeCount = agents.filter(a => a.status === AgentStatus.RUNNING).length;
  const totalTokens = agents.reduce((acc, a) => acc + a.memory.tokenCount, 0);

  return (
    <div className="flex items-center gap-6">
      <div className="flex flex-col items-end">
        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-tighter">Active Containers</span>
        <span className="text-sm font-mono text-emerald-400">{activeCount} / {agents.length}</span>
      </div>
      <div className="w-px h-6 bg-zinc-800"></div>
      <div className="flex flex-col items-end">
        <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-tighter">Global Burn</span>
        <span className="text-sm font-mono text-zinc-200">{Math.floor(totalTokens)} <span className="text-xs opacity-50">tokens</span></span>
      </div>
    </div>
  );
};
