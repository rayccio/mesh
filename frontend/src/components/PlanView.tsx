import React, { useState } from 'react';
import { Icons } from '../constants';
import { orchestratorService } from '../services/orchestratorService';
import { useAuth } from '../contexts/AuthContext';

interface PlanViewProps {
  hiveId: string;
  agents: any[];
}

export const PlanView: React.FC<PlanViewProps> = ({ hiveId, agents }) => {
  const [goal, setGoal] = useState('');
  const [planning, setPlanning] = useState(false);
  const [tasks, setTasks] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [goalId, setGoalId] = useState<string | null>(null);
  const [assigning, setAssigning] = useState<{ [key: string]: boolean }>({});

  const handlePlan = async () => {
    if (!goal.trim()) return;
    setPlanning(true);
    try {
      const result = await orchestratorService.createPlan(hiveId, goal);
      setTasks(result.tasks);
      setEdges(result.edges);
      setGoalId(result.goal_id);
    } catch (err) {
      console.error('Planning failed', err);
      alert('Planning failed. Check console.');
    } finally {
      setPlanning(false);
    }
  };

  const handleAssign = async (taskId: string, agentId: string) => {
    setAssigning(prev => ({ ...prev, [taskId]: true }));
    try {
      await orchestratorService.assignTask(hiveId, taskId, agentId);
      // Update task status locally
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: 'assigned', assigned_agent_id: agentId } : t));
    } catch (err) {
      console.error('Assignment failed', err);
      alert('Assignment failed');
    } finally {
      setAssigning(prev => ({ ...prev, [taskId]: false }));
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="space-y-2">
        <h2 className="text-3xl font-black tracking-tighter">Hive Plan</h2>
        <p className="text-zinc-500">Decompose a goal into tasks and assign them to bots.</p>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-2xl">
        <div className="flex gap-4">
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Enter a goal, e.g., 'Research EV startups in Africa'"
            className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none"
          />
          <button
            onClick={handlePlan}
            disabled={planning || !goal.trim()}
            className="px-6 py-3 bg-emerald-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-emerald-500 disabled:opacity-50 flex items-center gap-2"
          >
            {planning ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Planning...
              </>
            ) : (
              'Plan'
            )}
          </button>
        </div>
      </div>

      {tasks.length > 0 && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 shadow-2xl">
          <h3 className="text-lg font-black text-emerald-500 mb-4">Task Graph</h3>
          <div className="space-y-4">
            {tasks.map(task => (
              <div key={task.id} className="flex items-center justify-between p-4 bg-zinc-950 rounded-xl border border-zinc-800">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <span className={`w-2 h-2 rounded-full ${
                      task.status === 'completed' ? 'bg-emerald-500' :
                      task.status === 'assigned' ? 'bg-blue-500' :
                      task.status === 'running' ? 'bg-yellow-500 animate-pulse' :
                      'bg-zinc-600'
                    }`} />
                    <span className="text-sm font-bold text-zinc-300">{task.description}</span>
                  </div>
                  <div className="text-xs text-zinc-500 mt-1">
                    ID: {task.id} | Status: {task.status}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {!task.assigned_agent_id && task.status === 'pending' && (
                    <select
                      onChange={(e) => handleAssign(task.id, e.target.value)}
                      disabled={assigning[task.id]}
                      value=""
                      className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1 text-xs text-zinc-200"
                    >
                      <option value="">Assign to...</option>
                      {agents.map(a => (
                        <option key={a.id} value={a.id}>{a.name}</option>
                      ))}
                    </select>
                  )}
                  {task.assigned_agent_id && (
                    <span className="text-xs text-emerald-400">Assigned to {agents.find(a => a.id === task.assigned_agent_id)?.name || task.assigned_agent_id}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
          {edges.length > 0 && (
            <div className="mt-6 pt-4 border-t border-zinc-800">
              <p className="text-xs text-zinc-500 font-mono">Dependencies: {edges.map(e => `${e.from} → ${e.to}`).join(', ')}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
