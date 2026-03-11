import React, { useState, useEffect } from 'react';
import { Icons } from '../constants';
import { orchestratorService } from '../services/orchestratorService';
import { useProviders } from '../contexts/ProviderContext';

interface ProviderModel {
  id: string;
  name: string;
  enabled: boolean;
  is_primary: boolean;
  is_utility: boolean;
}

interface Provider {
  name: string;
  display_name: string;
  enabled: boolean;
  api_key_present: boolean;
  models: Record<string, ProviderModel>;
}

interface KnownProvider {
  name: string;
  display_name: string;
  models: Array<{ id: string; name: string; default_primary?: boolean; default_utility?: boolean }>;
}

export const AIProviderConfig: React.FC = () => {
  const { providers, refreshProviders } = useProviders();
  const [knownProviders, setKnownProviders] = useState<KnownProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [apiKeyInputs, setApiKeyInputs] = useState<Record<string, string>>({});
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({});
  const [showAddProvider, setShowAddProvider] = useState(false);
  const [selectedKnownProvider, setSelectedKnownProvider] = useState<string>('');
  const [isCustomProvider, setIsCustomProvider] = useState(false);
  const [newProviderKey, setNewProviderKey] = useState('');
  const [newProviderDisplay, setNewProviderDisplay] = useState('');
  const [newProviderModels, setNewProviderModels] = useState<Array<{id: string, name: string, default_primary?: boolean, default_utility?: boolean}>>([]);
  const [newModelId, setNewModelId] = useState('');
  const [newModelName, setNewModelName] = useState('');

  useEffect(() => {
    loadKnownProviders().finally(() => setLoading(false));
  }, []);

  const loadKnownProviders = async () => {
    try {
      const data = await orchestratorService.getKnownProviders();
      setKnownProviders(data);
    } catch (err) {
      console.error('Failed to load known providers', err);
    }
  };

  const handleToggleProvider = async (providerKey: string, enabled: boolean) => {
    await updateProvider(providerKey, { enabled });
  };

  const handleApiKeyChange = (providerKey: string, value: string) => {
    setApiKeyInputs(prev => ({ ...prev, [providerKey]: value }));
  };

  const handleSaveApiKey = async (providerKey: string) => {
    const key = apiKeyInputs[providerKey];
    if (key === undefined) return;
    await updateProvider(providerKey, { api_key: key });
    setApiKeyInputs(prev => ({ ...prev, [providerKey]: '' }));
    setShowApiKey(prev => ({ ...prev, [providerKey]: false }));
  };

  const handleToggleModel = async (providerKey: string, modelId: string, enabled: boolean) => {
    const provider = providers[providerKey];
    if (!provider) return;
    const model = provider.models[modelId];
    // Prevent disabling if this is the primary and no other primary exists (back-end will handle, but UI can warn)
    if (!enabled && model?.is_primary) {
      alert('Cannot disable the primary model. Please set another model as primary first.');
      return;
    }
    if (!enabled && model?.is_utility) {
      alert('Cannot disable the utility model. Please set another model as utility first.');
      return;
    }
    const updatedModels = { ...provider.models };
    if (!updatedModels[modelId]) {
      const known = knownProviders.find(kp => kp.name === providerKey);
      const modelInfo = known?.models.find(m => m.id === modelId);
      updatedModels[modelId] = {
        id: modelId,
        name: modelInfo?.name || modelId,
        enabled,
        is_primary: false,
        is_utility: false,
      };
    } else {
      updatedModels[modelId] = { ...updatedModels[modelId], enabled };
    }
    await updateProvider(providerKey, { models: updatedModels });
  };

  const handleSetPrimary = async (providerKey: string, modelId: string) => {
    const provider = providers[providerKey];
    if (!provider) return;
    const model = provider.models[modelId];
    if (!model) return;
    if (!model.enabled) {
      alert('Cannot set a disabled model as primary. Enable the model first.');
      return;
    }
    await updateProvider(providerKey, {
      models: { [modelId]: { ...model, is_primary: true, is_utility: model.is_utility } }
    });
  };

  const handleSetUtility = async (providerKey: string, modelId: string) => {
    const provider = providers[providerKey];
    if (!provider) return;
    const model = provider.models[modelId];
    if (!model) return;
    if (!model.enabled) {
      alert('Cannot set a disabled model as utility. Enable the model first.');
      return;
    }
    await updateProvider(providerKey, {
      models: { [modelId]: { ...model, is_utility: true, is_primary: model.is_primary } }
    });
  };

  const handleDeleteProvider = async (providerKey: string) => {
    if (!confirm(`Delete provider "${providerKey}"?`)) return;
    setSaving(true);
    try {
      await orchestratorService.deleteProvider(providerKey);
      await refreshProviders();
    } catch (err) {
      console.error('Failed to delete provider', err);
    } finally {
      setSaving(false);
    }
  };

  const updateProvider = async (providerKey: string, updates: any) => {
    setSaving(true);
    try {
      await orchestratorService.updateProviderConfig(providerKey, updates);
      await refreshProviders();
    } catch (err) {
      console.error('Failed to update provider', err);
    } finally {
      setSaving(false);
    }
  };

  const handleAddProvider = async () => {
    if (isCustomProvider) {
      if (!newProviderKey || !newProviderDisplay) return;
      const models: Record<string, ProviderModel> = {};
      newProviderModels.forEach(m => {
        models[m.id] = {
          id: m.id,
          name: m.name,
          enabled: true,
          is_primary: m.default_primary || false,
          is_utility: m.default_utility || false,
        };
      });
      await updateProvider(newProviderKey, {
        display_name: newProviderDisplay,
        models
      });
    } else {
      if (!selectedKnownProvider) return;
      const known = knownProviders.find(kp => kp.name === selectedKnownProvider);
      if (!known) return;
      const models: Record<string, ProviderModel> = {};
      known.models.forEach(m => {
        models[m.id] = {
          id: m.id,
          name: m.name,
          enabled: true,
          is_primary: m.default_primary || false,
          is_utility: m.default_utility || false,
        };
      });
      await updateProvider(known.name, {
        display_name: known.display_name,
        models
      });
    }
    setShowAddProvider(false);
    resetAddForm();
  };

  const resetAddForm = () => {
    setSelectedKnownProvider('');
    setIsCustomProvider(false);
    setNewProviderKey('');
    setNewProviderDisplay('');
    setNewProviderModels([]);
    setNewModelId('');
    setNewModelName('');
  };

  const addModelToNewProvider = () => {
    if (!newModelId || !newModelName) return;
    setNewProviderModels([...newProviderModels, { id: newModelId, name: newModelName }]);
    setNewModelId('');
    setNewModelName('');
  };

  const removeModelFromNewProvider = (modelId: string) => {
    setNewProviderModels(newProviderModels.filter(m => m.id !== modelId));
  };

  if (loading) {
    return <div className="text-center py-8 text-zinc-500">Loading provider configuration...</div>;
  }

  const providerKeys = Object.keys(providers);

  return (
    <div className="space-y-6">
      <div className="flex justify-end mb-4">
        <button
          onClick={() => setShowAddProvider(true)}
          className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-emerald-500 transition-colors flex items-center gap-2"
        >
          <Icons.Plus />
          Add Provider
        </button>
      </div>

      {providerKeys.length === 0 ? (
        <div className="text-center py-8 text-zinc-500 italic">No providers configured. Click "Add Provider" to get started.</div>
      ) : (
        providerKeys.map((providerKey) => {
          const provider = providers[providerKey];
          const known = knownProviders.find(kp => kp.name === providerKey);

          return (
            <div key={providerKey} className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-xl relative">
              {!known && (
                <button
                  onClick={() => handleDeleteProvider(providerKey)}
                  className="absolute top-4 right-4 p-2 text-zinc-500 hover:text-red-500 transition-colors"
                  title="Delete Provider"
                >
                  <Icons.Trash className="w-4 h-4" />
                </button>
              )}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <h3 className="text-lg font-bold text-emerald-400">{provider.display_name}</h3>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    provider.enabled 
                      ? 'bg-emerald-500/20 text-emerald-400' 
                      : 'bg-zinc-800 text-zinc-500'
                  }`}>
                    {provider.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
                <label className="flex items-center gap-2 cursor-pointer">
                  <span className="text-xs text-zinc-400">Enable</span>
                  <input
                    type="checkbox"
                    checked={provider.enabled}
                    onChange={(e) => handleToggleProvider(providerKey, e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-10 h-5 bg-zinc-800 rounded-full peer-checked:bg-emerald-600 transition-all relative">
                    <div className="absolute top-1 left-1 w-3 h-3 bg-white rounded-full transition-all peer-checked:left-6"></div>
                  </div>
                </label>
              </div>

              {/* API Key Section */}
              <div className="mb-4 p-4 bg-zinc-950 rounded-xl border border-zinc-800">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-zinc-300">API Key</span>
                  {provider.api_key_present ? (
                    <span className="text-xs text-emerald-500 flex items-center gap-1">
                      <span className="w-2 h-2 bg-emerald-500 rounded-full"></span>
                      Key stored
                    </span>
                  ) : (
                    <span className="text-xs text-red-400 flex items-center gap-1">
                      <span className="w-2 h-2 bg-red-400 rounded-full"></span>
                      Missing Key
                    </span>
                  )}
                </div>
                <div className="mt-2 flex gap-2">
                  <div className="relative flex-1">
                    <input
                      type={showApiKey[providerKey] ? 'text' : 'password'}
                      value={apiKeyInputs[providerKey] || ''}
                      onChange={(e) => handleApiKeyChange(providerKey, e.target.value)}
                      placeholder="Enter new API key"
                      className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2 text-sm text-zinc-200 focus:outline-none focus:border-emerald-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiKey(prev => ({ ...prev, [providerKey]: !prev[providerKey] }))}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 text-xs"
                    >
                      {showApiKey[providerKey] ? 'Hide' : 'Show'}
                    </button>
                  </div>
                  <button
                    onClick={() => handleSaveApiKey(providerKey)}
                    disabled={!apiKeyInputs[providerKey] || saving}
                    className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm hover:bg-emerald-500 disabled:opacity-50"
                  >
                    Save
                  </button>
                </div>
              </div>

              {/* Models List */}
              {provider.enabled && (
                <div className="space-y-3">
                  <h4 className="text-xs font-bold uppercase tracking-widest text-zinc-500">Models</h4>
                  {Object.values(provider.models).map((model) => (
                    <div key={model.id} className="flex items-center justify-between p-3 bg-zinc-950 rounded-lg border border-zinc-800">
                      <div className="flex items-center gap-4">
                        <span className={`text-sm ${model.enabled ? 'text-zinc-300' : 'text-zinc-600'}`}>{model.name}</span>
                        <label className="flex items-center gap-1 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={model.enabled}
                            onChange={(e) => handleToggleModel(providerKey, model.id, e.target.checked)}
                            className="sr-only peer"
                          />
                          <div className="w-8 h-4 bg-zinc-800 rounded-full peer-checked:bg-emerald-600 transition-all relative">
                            <div className="absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-all peer-checked:left-4"></div>
                          </div>
                          <span className="text-xs text-zinc-400">Enable</span>
                        </label>
                      </div>
                      <div className="flex items-center gap-3">
                        {/* Primary radio */}
                        <label className={`flex items-center gap-1 cursor-pointer ${!model.enabled ? 'opacity-50' : ''}`}>
                          <input
                            type="radio"
                            name={`primary-${providerKey}`}
                            checked={model.is_primary}
                            onChange={() => handleSetPrimary(providerKey, model.id)}
                            disabled={!model.enabled}
                            className="sr-only peer"
                          />
                          <div className={`w-4 h-4 rounded-full border-2 border-zinc-600 peer-checked:border-emerald-500 peer-checked:bg-emerald-500 ${!model.enabled ? 'border-zinc-700' : ''}`}></div>
                          <span className={`text-xs ${model.enabled ? 'text-zinc-400' : 'text-zinc-600'}`}>Primary</span>
                        </label>
                        {/* Utility radio */}
                        <label className={`flex items-center gap-1 cursor-pointer ${!model.enabled ? 'opacity-50' : ''}`}>
                          <input
                            type="radio"
                            name={`utility-${providerKey}`}
                            checked={model.is_utility}
                            onChange={() => handleSetUtility(providerKey, model.id)}
                            disabled={!model.enabled}
                            className="sr-only peer"
                          />
                          <div className={`w-4 h-4 rounded-full border-2 border-zinc-600 peer-checked:border-purple-500 peer-checked:bg-purple-500 ${!model.enabled ? 'border-zinc-700' : ''}`}></div>
                          <span className={`text-xs ${model.enabled ? 'text-zinc-400' : 'text-zinc-600'}`}>Utility</span>
                        </label>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })
      )}

      {/* Add Provider Modal */}
      {showAddProvider && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-zinc-900 rounded-2xl border border-zinc-800 p-6 max-w-md w-full shadow-2xl">
            <h3 className="text-lg font-bold text-emerald-400 mb-4">Add AI Provider</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    checked={!isCustomProvider}
                    onChange={() => setIsCustomProvider(false)}
                    className="text-emerald-500"
                  />
                  <span className="text-sm text-zinc-300">Select from known providers</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="radio"
                    checked={isCustomProvider}
                    onChange={() => setIsCustomProvider(true)}
                    className="text-emerald-500"
                  />
                  <span className="text-sm text-zinc-300">Custom provider</span>
                </label>
              </div>

              {!isCustomProvider ? (
                <div>
                  <label className="block text-xs font-bold text-zinc-500 uppercase mb-1">Provider</label>
                  <select
                    value={selectedKnownProvider}
                    onChange={(e) => setSelectedKnownProvider(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm text-zinc-200"
                  >
                    <option value="">Select a provider</option>
                    {knownProviders
                      .filter(kp => !providers[kp.name]) // only show those not already added
                      .map(kp => (
                        <option key={kp.name} value={kp.name}>{kp.display_name}</option>
                      ))}
                  </select>
                </div>
              ) : (
                <>
                  <div>
                    <label className="block text-xs font-bold text-zinc-500 uppercase mb-1">Provider Key</label>
                    <input
                      type="text"
                      value={newProviderKey}
                      onChange={(e) => setNewProviderKey(e.target.value)}
                      placeholder="e.g., cohere"
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm text-zinc-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-zinc-500 uppercase mb-1">Display Name</label>
                    <input
                      type="text"
                      value={newProviderDisplay}
                      onChange={(e) => setNewProviderDisplay(e.target.value)}
                      placeholder="e.g., Cohere"
                      className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2 text-sm text-zinc-200"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-bold text-zinc-500 uppercase mb-2">Models</label>
                    {newProviderModels.map(model => (
                      <div key={model.id} className="flex items-center justify-between p-2 bg-zinc-950 rounded-lg border border-zinc-800 mb-2">
                        <span className="text-sm text-zinc-300">{model.name} ({model.id})</span>
                        <button
                          onClick={() => removeModelFromNewProvider(model.id)}
                          className="text-red-500 hover:text-red-400"
                        >
                          <Icons.Trash className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                    <div className="flex gap-2 mt-2">
                      <input
                        type="text"
                        value={newModelId}
                        onChange={(e) => setNewModelId(e.target.value)}
                        placeholder="Model ID (e.g., command-r)"
                        className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1 text-xs text-zinc-200"
                      />
                      <input
                        type="text"
                        value={newModelName}
                        onChange={(e) => setNewModelName(e.target.value)}
                        placeholder="Display Name"
                        className="flex-1 bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-1 text-xs text-zinc-200"
                      />
                      <button
                        onClick={addModelToNewProvider}
                        className="px-3 py-1 bg-emerald-600 text-white rounded-lg text-xs hover:bg-emerald-500"
                      >
                        Add
                      </button>
                    </div>
                  </div>
                </>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleAddProvider}
                  disabled={(!isCustomProvider && !selectedKnownProvider) || (isCustomProvider && (!newProviderKey || !newProviderDisplay))}
                  className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-bold hover:bg-emerald-500 disabled:opacity-50"
                >
                  Add Provider
                </button>
                <button
                  onClick={() => {
                    setShowAddProvider(false);
                    resetAddForm();
                  }}
                  className="flex-1 px-4 py-2 bg-zinc-800 text-zinc-300 rounded-lg text-sm font-bold hover:bg-zinc-700"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {saving && (
        <div className="fixed bottom-4 right-4 bg-emerald-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          Saving...
        </div>
      )}
    </div>
  );
};
