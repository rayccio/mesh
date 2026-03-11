import React from 'react';
import { Agent, AgentStatus } from '../types';
import { Icons } from '../constants';

interface AgentGridProps {
  agents: Agent[];
  onSelect: (id: string) => void;
}

export const AgentGrid: React.FC<AgentGridProps> = ({ agents, onSelect }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 animate-in fade-in duration-500">
      {agents.map(agent => (
        <div 
          key={agent.id}
          onClick={() => onSelect(agent.id)}
          className="group cursor-pointer bg-zinc-900 border border-zinc-800 hover:border-emerald-500/50 rounded-2xl p-6 transition-all hover:shadow-[0_8px_30px_rgb(0,0,0,0.3)] relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-40 group-hover:text-emerald-500 transition-all transform group-hover:scale-110">
            <Icons.Box />
          </div>
          
          <div className="flex items-center gap-3 mb-6">
            <div className={`w-3 h-3 rounded-full shadow-[0_0_8px_rgba(0,0,0,0.5)] ${
              agent.status === AgentStatus.RUNNING ? 'bg-emerald-500 animate-pulse shadow-emerald-500/50' : 
              agent.status === AgentStatus.ERROR ? 'bg-red-500 shadow-red-500/50' : 'bg-zinc-700'
            }`} />
            <h3 className="font-black text-zinc-100 truncate tracking-tight uppercase text-sm">{agent.name}</h3>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between text-[11px]">
              <span className="text-zinc-500 font-bold uppercase tracking-widest">Role</span>
              <span className="text-zinc-300 font-medium">{agent.role}</span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-zinc-500 font-bold uppercase tracking-widest">Model</span>
              <span className="text-zinc-300 font-mono">
                {typeof agent.reasoning?.model === 'string' && agent.reasoning.model.includes('-') 
                  ? agent.reasoning.model.split('-')[1].toUpperCase() 
                  : (agent.reasoning?.model || 'CUSTOM').toString().toUpperCase()}
              </span>
            </div>
            <div className="flex justify-between text-[11px]">
              <span className="text-zinc-500 font-bold uppercase tracking-widest">UID</span>
              <span className="text-emerald-500 font-mono font-bold">{agent.userUid}</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-zinc-800 flex items-center justify-between text-[10px] font-mono text-zinc-500 uppercase">
            <span className="tracking-tighter">@{agent.containerId}</span>
            <span className="group-hover:text-emerald-400 transition-colors font-bold tracking-widest">Manage Bot →</span>
          </div>
        </div>
      ))}
    </div>
  );
};
