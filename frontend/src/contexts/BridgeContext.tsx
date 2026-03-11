import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { orchestratorService } from '../services/orchestratorService';

export interface BridgeInfo {
  type: string;
  enabled: boolean;
  status: string; // "running", "exited", "not_found", "starting", "stopping", "restarting"
  container: string;
}

interface BridgeContextType {
  bridges: BridgeInfo[];
  loading: boolean;
  toggleBridge: (bridgeType: string, enable: boolean) => Promise<void>;
  restartBridge: (bridgeType: string) => Promise<void>;
  refreshBridges: () => Promise<void>;
  enabledBridgeTypes: string[]; // convenience array of enabled types
}

const BridgeContext = createContext<BridgeContextType | undefined>(undefined);

export const useBridges = () => {
  const context = useContext(BridgeContext);
  if (!context) throw new Error('useBridges must be used within BridgeProvider');
  return context;
};

export const BridgeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [bridges, setBridges] = useState<BridgeInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const refreshBridges = useCallback(async () => {
    setLoading(true);
    try {
      const data = await orchestratorService.listBridges();
      setBridges(data);
    } catch (err) {
      console.error('Failed to load bridges', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshBridges();
  }, []);

  const toggleBridge = useCallback(async (bridgeType: string, enable: boolean) => {
    // Optimistic update
    setBridges(prev => prev.map(b => 
      b.type === bridgeType 
        ? { ...b, enabled: enable, status: enable ? 'starting' : 'stopping' } 
        : b
    ));
    try {
      if (enable) {
        await orchestratorService.enableBridge(bridgeType);
      } else {
        await orchestratorService.disableBridge(bridgeType);
      }
      // After a short delay, refresh to get actual status
      setTimeout(() => refreshBridges(), 2000);
    } catch (err) {
      console.error(`Failed to toggle bridge ${bridgeType}`, err);
      // Revert optimistic update
      refreshBridges();
    }
  }, [refreshBridges]);

  const restartBridge = useCallback(async (bridgeType: string) => {
    setBridges(prev => prev.map(b => 
      b.type === bridgeType ? { ...b, status: 'restarting' } : b
    ));
    try {
      await orchestratorService.restartBridge(bridgeType);
      setTimeout(() => refreshBridges(), 2000);
    } catch (err) {
      console.error(`Failed to restart bridge ${bridgeType}`, err);
      refreshBridges();
    }
  }, [refreshBridges]);

  const enabledBridgeTypes = bridges.filter(b => b.enabled).map(b => b.type);

  return (
    <BridgeContext.Provider value={{ 
      bridges, 
      loading, 
      toggleBridge, 
      restartBridge, 
      refreshBridges,
      enabledBridgeTypes
    }}>
      {children}
    </BridgeContext.Provider>
  );
};
