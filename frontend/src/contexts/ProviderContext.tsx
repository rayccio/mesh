import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { orchestratorService } from '../services/orchestratorService';

export interface ProviderModel {
  id: string;
  name: string;
  enabled: boolean;
  is_primary: boolean;
  is_utility: boolean;   // new
}

export interface Provider {
  name: string;
  display_name: string;
  enabled: boolean;
  api_key_present: boolean;
  models: Record<string, ProviderModel>;
}

interface ProviderContextType {
  providers: Record<string, Provider>;
  loading: boolean;
  refreshProviders: () => Promise<void>;
  getPrimaryModel: () => { provider: string; modelId: string } | null;
  getUtilityModel: () => { provider: string; modelId: string } | null;
  getEnabledModels: () => Array<{ provider: string; providerDisplay: string; modelId: string; modelName: string }>;
}

const ProviderContext = createContext<ProviderContextType | undefined>(undefined);

export const useProviders = () => {
  const context = useContext(ProviderContext);
  if (!context) {
    throw new Error('useProviders must be used within a ProviderProvider');
  }
  return context;
};

export const ProviderProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [providers, setProviders] = useState<Record<string, Provider>>({});
  const [loading, setLoading] = useState(true);

  const refreshProviders = useCallback(async () => {
    setLoading(true);
    try {
      const data = await orchestratorService.getProviderConfig();
      setProviders(data.providers);
    } catch (err) {
      console.error('Failed to load providers', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshProviders();
  }, []);

  const getPrimaryModel = useCallback(() => {
    for (const provider of Object.values(providers)) {
      if (provider.enabled && provider.api_key_present) {
        for (const model of Object.values(provider.models)) {
          if (model.enabled && model.is_primary) {
            return { provider: provider.name, modelId: model.id };
          }
        }
      }
    }
    return null;
  }, [providers]);

  const getUtilityModel = useCallback(() => {
    for (const provider of Object.values(providers)) {
      if (provider.enabled && provider.api_key_present) {
        for (const model of Object.values(provider.models)) {
          if (model.enabled && model.is_utility) {
            return { provider: provider.name, modelId: model.id };
          }
        }
      }
    }
    return null;
  }, [providers]);

  const getEnabledModels = useCallback(() => {
    const models: Array<{ provider: string; providerDisplay: string; modelId: string; modelName: string }> = [];
    Object.entries(providers).forEach(([providerKey, provider]) => {
      if (provider.enabled && provider.api_key_present) {
        Object.values(provider.models).forEach((model) => {
          if (model.enabled) {
            models.push({
              provider: providerKey,
              providerDisplay: provider.display_name,
              modelId: model.id,
              modelName: model.name,
            });
          }
        });
      }
    });
    return models;
  }, [providers]);

  return (
    <ProviderContext.Provider value={{
      providers,
      loading,
      refreshProviders,
      getPrimaryModel,
      getUtilityModel,
      getEnabledModels
    }}>
      {children}
    </ProviderContext.Provider>
  );
};
