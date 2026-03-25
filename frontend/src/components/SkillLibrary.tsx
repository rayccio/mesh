import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Icons } from '../constants';
import { orchestratorService } from '../services/orchestratorService';
import { Skill, SkillType, SkillVisibility, Layer } from '../types';
import { LoadingSpinner } from './LoadingSpinner';
import { toast } from 'react-hot-toast';

interface SkillLibraryProps {
  onInstall?: (skill: Skill) => void;
  showInstall?: boolean;
}

export const SkillLibrary: React.FC<SkillLibraryProps> = ({ onInstall, showInstall = true }) => {
  const [filter, setFilter] = useState('');
  const [selectedType, setSelectedType] = useState<SkillType | ''>('');
  const [selectedLayer, setSelectedLayer] = useState<string>('');
  const [skillLayerMap, setSkillLayerMap] = useState<Record<string, string>>({});
  const [layers, setLayers] = useState<Layer[]>([]);

  // Fetch all skills
  const { data: skills = [], isLoading: skillsLoading, error: skillsError } = useQuery({
    queryKey: ['skills', 'all'],
    queryFn: () => orchestratorService.listSkills(),
    staleTime: 1000 * 60 * 5,
  });

  // Fetch layers
  const { data: layersData = [], isLoading: layersLoading } = useQuery({
    queryKey: ['layers'],
    queryFn: () => orchestratorService.listLayers(),
    staleTime: 1000 * 60 * 5,
  });

  useEffect(() => {
    if (skillsError) {
      toast.error('Failed to load skills');
    }
  }, [skillsError]);

  useEffect(() => {
    if (layersData) {
      setLayers(layersData);
    }
  }, [layersData]);

  // Build skill -> layer map
  useEffect(() => {
    const buildMap = async () => {
      if (layers.length === 0) return;
      const map: Record<string, string> = {};
      for (const layer of layers) {
        try {
          const layerSkills = await orchestratorService.listLayerSkills(layer.id);
          for (const ls of layerSkills) {
            map[ls.skill_id] = layer.name;
          }
        } catch (err) {
          console.error(`Failed to fetch skills for layer ${layer.id}`, err);
        }
      }
      setSkillLayerMap(map);
    };
    buildMap();
  }, [layers]);

  const filteredSkills = skills.filter(skill => {
    if (filter && !skill.name.toLowerCase().includes(filter.toLowerCase()) && !skill.description.toLowerCase().includes(filter.toLowerCase())) return false;
    if (selectedType && skill.type !== selectedType) return false;
    if (selectedLayer && skillLayerMap[skill.id] !== selectedLayer) return false;
    return true;
  });

  const isLoading = skillsLoading || layersLoading;

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-4">
        <input
          type="text"
          placeholder="Search skills..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="flex-1 min-w-[200px] bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-2 text-sm text-zinc-200 focus:border-emerald-500 outline-none"
        />
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value as SkillType | '')}
          className="bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-2 text-sm text-zinc-200 focus:border-emerald-500 outline-none"
        >
          <option value="">All types</option>
          {Object.values(SkillType).map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <select
          value={selectedLayer}
          onChange={(e) => setSelectedLayer(e.target.value)}
          className="bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-2 text-sm text-zinc-200 focus:border-emerald-500 outline-none"
        >
          <option value="">All layers</option>
          {layers.map(l => (
            <option key={l.id} value={l.name}>{l.name}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredSkills.map(skill => (
          <div key={skill.id} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 hover:border-emerald-500/30 transition-all">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-bold text-emerald-400">{skill.name}</h3>
                <p className="text-xs text-zinc-500 mt-1">{skill.type}</p>
              </div>
              {showInstall && onInstall && (
                <button
                  onClick={() => onInstall(skill)}
                  className="px-3 py-1 bg-emerald-600 text-white rounded-lg text-xs font-black uppercase tracking-widest hover:bg-emerald-500"
                >
                  Install
                </button>
              )}
            </div>
            <p className="text-sm text-zinc-400 mt-3 line-clamp-3">{skill.description}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {skill.tags.map(tag => (
                <span key={tag} className="px-2 py-1 bg-zinc-800 text-zinc-400 rounded text-[10px] font-mono">#{tag}</span>
              ))}
            </div>
            <div className="mt-4 text-[10px] text-zinc-600 flex justify-between">
              <span>v{skill.metadata?.version || '1.0'} • by {skill.authorId || 'community'}</span>
              {skillLayerMap[skill.id] && (
                <span className="text-emerald-400">Layer: {skillLayerMap[skill.id]}</span>
              )}
            </div>
          </div>
        ))}
        {filteredSkills.length === 0 && (
          <div className="col-span-full text-center py-12 text-zinc-500 italic">
            No skills found.
          </div>
        )}
      </div>
    </div>
  );
};
