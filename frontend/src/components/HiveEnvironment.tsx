import React from 'react';
import { Hive, HiveMindAccessLevel } from '../types';
import { Icons } from '../constants';

interface HiveEnvironmentProps {
  hive: Hive;
  onUpdateHive: (hiveId: string, updates: any) => Promise<Hive>;
  allHives: Hive[];
}

export const HiveEnvironment: React.FC<HiveEnvironmentProps> = ({ 
  hive, 
  onUpdateHive,
  allHives 
}) => {
  const handleUpdate = (field: string, value: any) => {
    onUpdateHive(hive.id, { [field]: value });
  };

  const handleHiveMindConfig = (accessLevel: HiveMindAccessLevel, sharedHiveIds?: string[]) => {
    onUpdateHive(hive.id, {
      hiveMindConfig: {
        accessLevel,
        sharedHiveIds: sharedHiveIds || hive.hiveMindConfig.sharedHiveIds
      }
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 md:space-y-12 pb-20 animate-in slide-in-from-bottom-4 duration-500">
      <div className="space-y-2">
        <h2 className="text-3xl md:text-5xl font-black tracking-tighter">Hive Environment</h2>
        <p className="text-zinc-500 text-base md:text-lg">Centralized configuration for the <span className="text-emerald-500 font-bold">{hive.name}</span> mesh.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Hive Mind Configuration - Merged from Monohive */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden group col-span-full">
          <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Layers /></div>
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">Hive Mind Configuration</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <button 
              onClick={() => handleHiveMindConfig(HiveMindAccessLevel.ISOLATED)}
              className={`p-6 rounded-2xl border transition-all text-left space-y-2 ${hive.hiveMindConfig?.accessLevel === HiveMindAccessLevel.ISOLATED ? 'bg-emerald-500/10 border-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.1)]' : 'bg-zinc-950 border-zinc-800 hover:border-zinc-700'}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Isolated</span>
                {hive.hiveMindConfig?.accessLevel === HiveMindAccessLevel.ISOLATED && <div className="w-2 h-2 rounded-full bg-emerald-500"></div>}
              </div>
              <p className="text-xs font-bold text-zinc-200">Per-Hive Brain</p>
              <p className="text-[10px] text-zinc-500 leading-relaxed italic">Bots only reference files and history from this hive.</p>
            </button>

            <button 
              onClick={() => handleHiveMindConfig(HiveMindAccessLevel.SHARED)}
              className={`p-6 rounded-2xl border transition-all text-left space-y-2 ${hive.hiveMindConfig?.accessLevel === HiveMindAccessLevel.SHARED ? 'bg-blue-500/10 border-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.1)]' : 'bg-zinc-950 border-zinc-800 hover:border-zinc-700'}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Shared</span>
                {hive.hiveMindConfig?.accessLevel === HiveMindAccessLevel.SHARED && <div className="w-2 h-2 rounded-full bg-blue-500"></div>}
              </div>
              <p className="text-xs font-bold text-zinc-200">Cross-Hive Sharing</p>
              <p className="text-[10px] text-zinc-500 leading-relaxed italic">Select specific hives to share knowledge with this cluster.</p>
            </button>

            <button 
              onClick={() => handleHiveMindConfig(HiveMindAccessLevel.GLOBAL)}
              className={`p-6 rounded-2xl border transition-all text-left space-y-2 ${hive.hiveMindConfig?.accessLevel === HiveMindAccessLevel.GLOBAL ? 'bg-purple-500/10 border-purple-500 shadow-[0_0_20px_rgba(168,85,247,0.1)]' : 'bg-zinc-950 border-zinc-800 hover:border-zinc-700'}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-black uppercase tracking-widest text-zinc-400">Global</span>
                {hive.hiveMindConfig?.accessLevel === HiveMindAccessLevel.GLOBAL && <div className="w-2 h-2 rounded-full bg-purple-500"></div>}
              </div>
              <p className="text-xs font-bold text-zinc-200">Super-Brain Access</p>
              <p className="text-[10px] text-zinc-500 leading-relaxed italic">Full access to every file and conversation across all hives.</p>
            </button>
          </div>

          {hive.hiveMindConfig?.accessLevel === HiveMindAccessLevel.SHARED && (
            <div className="mt-6 p-6 bg-zinc-950 border border-zinc-800 rounded-2xl space-y-4 animate-in slide-in-from-top-2 duration-300">
              <h4 className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Select Hives to Link</h4>
              <div className="flex flex-wrap gap-3">
                {allHives.filter(p => p.id !== hive.id).map(p => (
                  <button
                    key={p.id}
                    onClick={() => {
                      const current = hive.hiveMindConfig.sharedHiveIds || [];
                      const next = current.includes(p.id) ? current.filter(id => id !== p.id) : [...current, p.id];
                      handleHiveMindConfig(HiveMindAccessLevel.SHARED, next);
                    }}
                    className={`px-4 py-2 rounded-xl text-[10px] font-bold transition-all border ${
                      (hive.hiveMindConfig.sharedHiveIds || []).includes(p.id) 
                      ? 'bg-blue-500/20 border-blue-500 text-blue-400' 
                      : 'bg-zinc-900 border-zinc-800 text-zinc-500 hover:border-zinc-700'
                    }`}
                  >
                    {p.name}
                  </button>
                ))}
                {allHives.length <= 1 && <p className="text-[10px] text-zinc-600 italic">No other hives available to link.</p>}
              </div>
            </div>
          )}
        </div>

        {/* Hive Identity - From Monohive */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden group col-span-full">
          <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Layers /></div>
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">Hive Identity</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2 tracking-widest">Hive Name</label>
              <input 
                type="text" 
                value={hive.name} 
                onChange={(e) => handleUpdate('name', e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 focus:outline-none transition-all shadow-inner" 
                placeholder="Operations Alpha" 
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2 tracking-widest">Description</label>
              <input 
                type="text" 
                value={hive.description} 
                onChange={(e) => handleUpdate('description', e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 focus:outline-none transition-all shadow-inner" 
                placeholder="Autonomous bot orchestration hive" 
              />
            </div>
          </div>
        </div>

        {/* Security Policy - From Monohive */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Shield /></div>
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">Default Security Policy</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2 tracking-widest">Default Bot UID</label>
              <input 
                type="text" 
                value={hive.globalUid} 
                onChange={(e) => handleUpdate('globalUid', e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 focus:outline-none transition-all shadow-inner" 
                placeholder="e.g. 1001" 
              />
              <p className="text-[10px] text-zinc-500 mt-2 italic">
                Newly spawned bots inherit this limited-privilege UID for container isolation.
              </p>
            </div>
          </div>
        </div>

        {/* Reasoning Credentials - From Monohive */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity"><Icons.Cpu /></div>
          <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">Reasoning Credentials</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2 tracking-widest">Master API Key (Orchestrator)</label>
              <input 
                type="password" 
                value={hive.globalApiKey} 
                onChange={(e) => handleUpdate('globalApiKey', e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 focus:outline-none transition-all shadow-inner" 
                placeholder="••••••••••••••••" 
              />
              <p className="text-[10px] text-zinc-500 mt-2 italic">Global fallback for bots without dedicated provider credentials.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-3xl p-8 flex items-center gap-8 shadow-xl">
        <div className="p-5 bg-emerald-600 text-white rounded-2xl shadow-lg shadow-emerald-900/20"><Icons.Server /></div>
        <div>
          <h4 className="font-bold text-xl tracking-tight">Hive Network Operational</h4>
          <p className="text-sm text-zinc-400 max-w-lg leading-relaxed mt-1">Environment integrity verified. Sandbox protocols are active. Each bot operates in a unique virtual space within the hive root.</p>
        </div>
      </div>
    </div>
  );
};
