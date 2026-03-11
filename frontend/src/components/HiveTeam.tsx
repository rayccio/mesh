import React, { useState } from 'react';
import { Hive, UserAccount, UserRole } from '../types';
import { Icons } from '../constants';

interface HiveTeamProps {
  hive: Hive;
  allUsers: UserAccount[];
  onUpdateUsers: (users: UserAccount[]) => void;
  currentUser: UserAccount; // not used in this component but kept for consistency
}

export const HiveTeam: React.FC<HiveTeamProps> = ({ 
  hive, 
  allUsers, 
  onUpdateUsers,
  currentUser
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');

  // Filter users assigned to this hive
  const hiveUsers = allUsers.filter(u => (u.assignedHiveIds || []).includes(hive.id));
  const nonHiveUsers = allUsers.filter(u => !(u.assignedHiveIds || []).includes(hive.id));

  const handleAddExistingUser = (userId: string) => {
    const updatedUsers = allUsers.map(u => {
      if (u.id === userId) {
        return { ...u, assignedHiveIds: [...(u.assignedHiveIds || []), hive.id] };
      }
      return u;
    });
    onUpdateUsers(updatedUsers);
    setIsAdding(false);
  };

  const handleCreateUser = () => {
    if (!newUsername || !newPassword) return;
    const newUser: UserAccount = {
      id: Math.random().toString(36).substr(2, 9),
      username: newUsername,
      password: newPassword,
      role: UserRole.HIVE_USER,
      assignedHiveIds: [hive.id],
      createdAt: new Date().toISOString()
    };
    onUpdateUsers([...allUsers, newUser]);
    setNewUsername('');
    setNewPassword('');
    setIsAdding(false);
  };

  const handleRemoveUser = (userId: string) => {
    const updatedUsers = allUsers.map(u => {
      if (u.id === userId) {
        return { ...u, assignedHiveIds: (u.assignedHiveIds || []).filter(id => id !== hive.id) };
      }
      return u;
    });
    onUpdateUsers(updatedUsers);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <h2 className="text-3xl md:text-5xl font-black tracking-tighter uppercase">Hive <span className="text-emerald-500">Team</span></h2>
          <p className="text-zinc-500 text-base md:text-lg">Manage operators assigned to this hive.</p>
        </div>
        <button 
          onClick={() => setIsAdding(true)}
          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-emerald-900/20 flex items-center gap-2"
        >
          <Icons.Plus /> Add Member
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {hiveUsers.map(user => (
          <div key={user.id} className="bg-zinc-900 border border-zinc-800 rounded-3xl p-6 relative group hover:border-emerald-500/30 transition-all">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-zinc-800 rounded-2xl flex items-center justify-center text-zinc-400">
                <Icons.User />
              </div>
              <div>
                <h4 className="font-bold text-zinc-200">{user.username}</h4>
                <span className={`px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-widest ${
                  user.role === UserRole.GLOBAL_ADMIN ? 'bg-purple-500/10 text-purple-400' :
                  user.role === UserRole.HIVE_ADMIN ? 'bg-blue-500/10 text-blue-400' :
                  'bg-zinc-500/10 text-zinc-400'
                }`}>
                  {user.role.replace('_', ' ')}
                </span>
              </div>
            </div>
            
            <div className="flex justify-between text-[10px] pt-4 border-t border-zinc-800/50">
              <span className="text-zinc-500 uppercase font-bold">Joined Team</span>
              <span className="text-zinc-400 font-mono">{new Date(user.createdAt).toLocaleDateString()}</span>
            </div>

            <button 
              onClick={() => handleRemoveUser(user.id)}
              className="absolute top-4 right-4 p-2 text-zinc-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
              title="Remove from Hive"
            >
              <Icons.Trash />
            </button>
          </div>
        ))}
      </div>

      {isAdding && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 w-full max-w-md space-y-6 shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-black uppercase tracking-tighter">Add Team Member</h3>
              <button onClick={() => setIsAdding(false)} className="text-zinc-500 hover:text-white transition-colors"><Icons.X /></button>
            </div>

            <div className="space-y-6">
              {nonHiveUsers.length > 0 && (
                <div>
                  <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-3">Add Existing Operator</label>
                  <div className="space-y-2 max-h-40 overflow-y-auto p-2 bg-zinc-950 border border-zinc-800 rounded-xl">
                    {nonHiveUsers.map(u => (
                      <button
                        key={u.id}
                        onClick={() => handleAddExistingUser(u.id)}
                        className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200 transition-all"
                      >
                        <span>{u.username}</span>
                        <span className="text-[8px] opacity-50">{u.role}</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div className="relative">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-zinc-800"></div></div>
                <div className="relative flex justify-center text-[10px] uppercase font-black text-zinc-600"><span className="bg-zinc-900 px-2">Or Create New</span></div>
              </div>

              <div>
                <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">New Username</label>
                <input 
                  type="text" 
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all mb-4"
                  placeholder="Enter username"
                />
                
                <label className="block text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-2">Password</label>
                <input 
                  type="password" 
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 outline-none transition-all"
                  placeholder="Enter password"
                />
                <p className="mt-2 text-[9px] text-zinc-500 italic">New users created here are assigned the HIVE USER role by default.</p>
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <button 
                onClick={() => setIsAdding(false)}
                className="flex-1 px-4 py-3 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all"
              >
                Cancel
              </button>
              <button 
                onClick={handleCreateUser}
                disabled={!newUsername || !newPassword}
                className="flex-1 px-4 py-3 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-emerald-900/20"
              >
                Create & Add
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
