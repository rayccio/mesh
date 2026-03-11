import React, { useMemo } from 'react';
import { Hive, HiveMindAccessLevel } from '../types';
import { Icons } from '../constants';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface HiveMindDashboardProps {
  hives: Hive[];
}

export const HiveMindDashboard: React.FC<HiveMindDashboardProps> = ({ hives }) => {
  const stats = useMemo(() => {
    const totalFiles = hives.reduce((acc, h) => acc + h.globalFiles.length, 0);
    const totalAgents = hives.reduce((acc, h) => acc + h.agents.length, 0);
    const totalVectors = totalFiles * 42; // Simulated vector count
    
    const accessDistribution = hives.reduce((acc, h) => {
      const level = h.hiveMindConfig?.accessLevel || HiveMindAccessLevel.ISOLATED;
      acc[level] = (acc[level] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const pieData = [
      { name: 'Isolated', value: accessDistribution[HiveMindAccessLevel.ISOLATED] || 0, color: '#71717a' },
      { name: 'Shared', value: accessDistribution[HiveMindAccessLevel.SHARED] || 0, color: '#10b981' },
      { name: 'Global', value: accessDistribution[HiveMindAccessLevel.GLOBAL] || 0, color: '#3b82f6' },
    ].filter(d => d.value > 0);

    return {
      totalFiles,
      totalAgents,
      totalVectors,
      pieData
    };
  }, [hives]);

  return (
    <div className="space-y-8 animate-in fade-in duration-700 pb-20">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-4xl font-black tracking-tighter text-zinc-100 uppercase">
            Hive <span className="text-emerald-500">Mind</span>
          </h2>
          <p className="text-zinc-500 font-medium">Global RAG & Privacy-First Vector Store Status</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-xl flex items-center gap-3 shadow-inner">
            <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse"></div>
            <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Neural Sync: Active</span>
          </div>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Layers /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Knowledge Base</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.totalFiles} <span className="text-sm text-zinc-500">Indexed Files</span></h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Across {hives.length} Hives</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Cpu /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Neural Nodes</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.totalAgents} <span className="text-sm text-zinc-500">Active Brains</span></h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Connected to Hive Mind</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Shield /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Vector Density</p>
          <h3 className="text-3xl font-black text-zinc-100 tracking-tighter">{stats.totalVectors.toLocaleString()} <span className="text-sm text-zinc-500">Embeddings</span></h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Privacy-First Local Store</p>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 rounded-3xl p-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Terminal /></div>
          <p className="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-1">Inference Speed</p>
          <h3 className="text-3xl font-black text-blue-500 tracking-tighter">14ms</h3>
          <p className="text-[10px] text-zinc-500 mt-2 font-mono">Local RAG Latency</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Access Distribution */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 shadow-2xl space-y-6 flex flex-col items-center">
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500 w-full">Privacy Segmentation</h3>
          <div className="h-[250px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {stats.pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '12px' }}
                  itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex gap-4 text-[10px] font-black uppercase tracking-widest">
            {stats.pieData.map(d => (
              <div key={d.name} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }}></div>
                <span className="text-zinc-400">{d.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Hive Knowledge Base */}
        <div className="lg:col-span-2 bg-zinc-900 border border-zinc-800 rounded-3xl p-8 shadow-2xl space-y-6">
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-zinc-500">Hive Knowledge Density</h3>
          <div className="space-y-4">
            {hives.map(h => (
              <div key={h.id} className="p-4 bg-zinc-950 border border-zinc-800 rounded-2xl flex items-center justify-between group hover:border-emerald-500/30 transition-all">
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    h.hiveMindConfig?.accessLevel === HiveMindAccessLevel.GLOBAL ? 'bg-blue-500/10 text-blue-500' :
                    h.hiveMindConfig?.accessLevel === HiveMindAccessLevel.SHARED ? 'bg-emerald-500/10 text-emerald-500' :
                    'bg-zinc-800 text-zinc-500'
                  }`}>
                    <Icons.Layers />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-zinc-200">{h.name}</h4>
                    <p className="text-[10px] text-zinc-500 uppercase tracking-widest font-black">
                      {h.hiveMindConfig?.accessLevel || HiveMindAccessLevel.ISOLATED} ACCESS
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-xs font-mono text-zinc-400">{h.globalFiles.length} Files</span>
                  <div className="flex gap-1 mt-1">
                    {Array.from({ length: Math.min(5, h.globalFiles.length) }).map((_, i) => (
                      <div key={i} className="w-1 h-1 rounded-full bg-emerald-500/50"></div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
