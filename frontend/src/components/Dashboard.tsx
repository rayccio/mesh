import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Hive, Agent, AgentStatus, Message } from '../types';
import { Icons } from '../constants';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { GoogleGenAI } from '@google/genai';

interface DashboardProps {
  hive: Hive;
  onNavigateToNodes: () => void;
  onRunAgent: (agentId: string) => void;
  agents: Agent[];
}

export const Dashboard: React.FC<DashboardProps> = ({ 
  hive, 
  onNavigateToNodes, 
  onRunAgent,
  agents 
}) => {
  const [setupPrompt, setSetupPrompt] = useState('');
  const [isSettingUp, setIsSettingUp] = useState(false);
  const [setupLogs, setSetupLogs] = useState<{ id: string; text: string; type: 'user' | 'ai' | 'system' }[]>([
    { id: '1', text: 'HiveBot Orchestrator initialized. Awaiting auto-setup instructions...', type: 'system' }
  ]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [setupLogs]);

  const handleAutoSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!setupPrompt.trim() || isSettingUp) return;

    const userMsg = setupPrompt;
    setSetupPrompt('');
    setSetupLogs(prev => [...prev, { id: Math.random().toString(36).substr(2, 9), text: userMsg, type: 'user' }]);
    setIsSettingUp(true);

    try {
      setSetupLogs(prev => [...prev, { id: 'loading', text: 'Analyzing hive requirements and generating bot configurations...', type: 'system' }]);
      
      const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || '' });
      const response = await ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `You are the HiveBot Orchestrator AI. The user is providing auto-setup instructions for a hive.
        HIVE_NAME: ${hive.name}
        HIVE_DESCRIPTION: ${hive.description}
        USER_INSTRUCTIONS: ${userMsg}
        
        Provide a professional, concise response (under 60 words) explaining how you will configure the hive based on these instructions. Use technical terminology like 'provisioning', 'hierarchical reporting', 'isolated sandboxes', etc.`,
      });
      
      const aiResponse = response.text || "Setup logic processed. Awaiting confirmation.";

      setSetupLogs(prev => prev.filter(l => l.id !== 'loading'));
      setSetupLogs(prev => [...prev, { id: Math.random().toString(36).substr(2, 9), text: aiResponse, type: 'ai' }]);
    } catch (err) {
      setSetupLogs(prev => prev.filter(l => l.id !== 'loading'));
      setSetupLogs(prev => [...prev, { id: Math.random().toString(36).substr(2, 9), text: 'Setup Error: Failed to reach reasoning engine. Check API configuration.', type: 'system' }]);
    } finally {
      setIsSettingUp(false);
    }
  };

  const stats = useMemo(() => {
    const totalTokens = agents.reduce((acc, a) => acc + a.memory.tokenCount, 0);
    const activeNodes = agents.filter(a => a.status === AgentStatus.RUNNING).length;
    const totalNodes = agents.length;
    
    const ramUsage = agents.reduce((acc, a) => acc + (a.status === AgentStatus.RUNNING ? 128 : 32), 0);
    const diskUsage = agents.reduce((acc, a) => acc + 45 + (a.localFiles.length * 2), 0);
    
    return {
      totalTokens,
      activeNodes,
      totalNodes,
      ramUsage,
      diskUsage,
      ramLimit: totalNodes * 256,
      diskLimit: totalNodes * 500
    };
  }, [agents]);

  const chartData = useMemo(() => {
    return agents.map(a => ({
      name: a.name.split(' ')[0],
      tokens: Math.floor(a.memory.tokenCount),
      files: a.localFiles.length
    }));
  }, [agents]);

  return (
    <div className="space-y-8 animate-in fade-in duration-700 pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-4xl font-black tracking-tighter text-zinc-100 uppercase">
            {hive.name} <span className="text-emerald-500">Dashboard</span>
          </h2>
          <p className="text-zinc-500 font-medium">{hive.description}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl flex items-center gap-3 shadow-inner">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Hive Health: Nominal</span>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Cpu /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Compute Load</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.activeNodes} <span className="text-sm text-zinc-500">/ {stats.totalNodes} Bots</span></h3>
          <div className="mt-4 h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
            <div className="h-full bg-emerald-500 transition-all duration-1000" style={{ width: `${(stats.activeNodes / stats.totalNodes) * 100}%` }}></div>
          </div>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Shield /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">RAM Utilization</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.ramUsage} <span className="text-sm text-zinc-500">MB</span></h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Limit: {stats.ramLimit} MB</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Server /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Disk Allocation</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.diskUsage} <span className="text-sm text-zinc-500">MB</span></h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Limit: {stats.diskLimit} MB</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Terminal /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Token Consumption</p>
          <h3 className="text-3xl font-black text-emerald-500 tracking-tighter">{Math.floor(stats.totalTokens).toLocaleString()}</h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Hive Lifetime Burn</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* AI Auto-Setup Chat - From Monohive */}
        <div className="lg:col-span-1 bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-2xl flex flex-col h-[500px] relative overflow-hidden">
          <div className="absolute top-0 right-0 p-6 opacity-5 pointer-events-none"><Icons.Cpu /></div>
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-emerald-500/10 text-emerald-500 rounded-lg flex items-center justify-center"><Icons.Terminal /></div>
            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Auto-Setup AI</h3>
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2 scrollbar-none">
            {setupLogs.map(log => (
              <div key={log.id} className={`flex ${log.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-3 rounded-2xl text-[11px] leading-relaxed ${
                  log.type === 'user' ? 'bg-emerald-600 text-white rounded-tr-none' : 
                  log.type === 'ai' ? 'bg-zinc-800 text-zinc-200 border border-zinc-700 rounded-tl-none' : 
                  'bg-zinc-950/50 text-zinc-500 italic text-center w-full border border-zinc-800/50'
                }`}>
                  {log.text}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>

          <form onSubmit={handleAutoSetup} className="relative">
            <input 
              type="text" 
              value={setupPrompt}
              onChange={(e) => setSetupPrompt(e.target.value)}
              disabled={isSettingUp}
              placeholder="Enter setup instructions..."
              className="w-full bg-zinc-950 border border-zinc-800 rounded-xl pl-4 pr-12 py-3 text-xs text-zinc-200 focus:border-emerald-500/50 outline-none transition-all"
            />
            <button 
              type="submit"
              disabled={isSettingUp || !setupPrompt.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-emerald-500 hover:text-emerald-400 disabled:opacity-30 transition-all"
            >
              {isSettingUp ? <div className="w-4 h-4 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" /> : <Icons.Shield />}
            </button>
          </form>
        </div>

        {/* Token Distribution Chart */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-3xl p-8 shadow-2xl space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Bot Token Distribution</h3>
            <button onClick={onNavigateToNodes} className="text-[10px] font-black text-emerald-500 uppercase tracking-widest hover:text-emerald-400 transition-colors">View All Bots →</button>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                <XAxis dataKey="name" stroke="#71717a" fontSize={10} tickLine={false} axisLine={false} />
                <YAxis stroke="#71717a" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '12px' }}
                  itemStyle={{ color: '#10b981', fontSize: '12px', fontWeight: 'bold' }}
                />
                <Bar dataKey="tokens" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Hive Map / Topology */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 shadow-2xl space-y-6 flex flex-col">
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Hive Topology</h3>
          <div className="flex-1 relative bg-zinc-950 rounded-2xl border border-zinc-800/50 overflow-hidden p-4">
            <div className="absolute inset-0 opacity-20 pointer-events-none" style={{ backgroundImage: 'radial-gradient(#10b981 0.5px, transparent 0.5px)', backgroundSize: '20px 20px' }}></div>
            <div className="relative h-full flex flex-col items-center justify-center gap-8">
              {/* Simple Visual Topology */}
              <div className="w-12 h-12 bg-emerald-500/20 border border-emerald-500 text-emerald-500 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(16,185,129,0.2)]">
                <Icons.Shield />
              </div>
              <div className="w-px h-8 bg-gradient-to-b from-emerald-500 to-transparent"></div>
              <div className="flex gap-4">
                {agents.slice(0, 3).map((a, i) => (
                  <div key={a.id} className="flex flex-col items-center gap-2">
                    <div className={`w-8 h-8 rounded-lg border flex items-center justify-center text-[10px] font-black ${a.status === AgentStatus.RUNNING ? 'bg-emerald-500/10 border-emerald-500 text-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : 'bg-zinc-800 border-zinc-700 text-zinc-500'}`}>
                      {i + 1}
                    </div>
                    <span className="text-[8px] font-bold text-zinc-600 uppercase tracking-tighter truncate w-12 text-center">{a.name.split(' ')[0]}</span>
                  </div>
                ))}
                {agents.length > 3 && (
                  <div className="w-8 h-8 rounded-lg border border-zinc-800 bg-zinc-900 flex items-center justify-center text-[10px] font-black text-zinc-600">
                    +{agents.length - 3}
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="pt-4 border-t border-zinc-800">
             <div className="flex items-center justify-between text-[10px]">
               <span className="text-zinc-500 font-bold uppercase tracking-widest">Hive Root</span>
               <span className="text-emerald-500 font-mono font-bold">ACTIVE</span>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};
