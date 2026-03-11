import React, { useState, useEffect } from 'react';
import { orchestratorService } from '../services/orchestratorService';
import { Icons } from '../constants';

export const PublicUrlConfig: React.FC = () => {
  const [enabled, setEnabled] = useState(false);
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [detecting, setDetecting] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const storedUrl = await orchestratorService.getPublicUrl();
        if (storedUrl) {
          setUrl(storedUrl);
          setEnabled(true);
        }
      } catch (err) {
        console.error('Failed to load public URL', err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const handleToggle = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newEnabled = e.target.checked;
    setEnabled(newEnabled);
    if (!newEnabled) {
      // If turning off, clear the URL
      setUrl('');
      saveUrl(null);
    }
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
  };

  const saveUrl = async (urlToSave: string | null) => {
    setSaving(true);
    try {
      await orchestratorService.setPublicUrl(urlToSave);
    } catch (err) {
      console.error('Failed to save public URL', err);
    } finally {
      setSaving(false);
    }
  };

  const handleSave = () => {
    if (!enabled) return;
    if (!url.trim()) {
      alert('Please enter a valid URL or disable webhook mode.');
      return;
    }
    saveUrl(url.trim());
  };

  const handleDetect = async () => {
    setDetecting(true);
    try {
      const ip = await orchestratorService.detectPublicIp();
      if (ip) {
        const suggestedUrl = `http://${ip}:8000`; // or use https if detected?
        setUrl(suggestedUrl);
      } else {
        alert('Could not detect public IP automatically. Please enter your domain or IP manually.');
      }
    } catch (err) {
      alert('Failed to detect public IP.');
    } finally {
      setDetecting(false);
    }
  };

  if (loading) {
    return <div className="text-zinc-500">Loading configuration...</div>;
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-3xl p-8 space-y-6 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 right-0 p-8 opacity-5"><Icons.Globe /></div>
      <h3 className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">External Communication</h3>

      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-zinc-300">Enable Webhook Mode</p>
          <p className="text-xs text-zinc-500 mt-1">
            When enabled, the system will use webhooks for channel bridges (requires a public URL).<br />
            When disabled, bridges will use long‑polling (works behind NAT).
          </p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            className="sr-only peer"
            checked={enabled}
            onChange={handleToggle}
          />
          <div className="w-11 h-6 bg-zinc-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600"></div>
        </label>
      </div>

      {enabled && (
        <div className="space-y-4">
          <div>
            <label className="block text-[10px] font-bold text-zinc-600 uppercase mb-2 tracking-widest">
              Public URL / Domain
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={url}
                onChange={handleUrlChange}
                placeholder="https://your-domain.com or http://123.45.67.89"
                className="flex-1 bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-emerald-500 focus:outline-none transition-all shadow-inner"
              />
              <button
                onClick={handleDetect}
                disabled={detecting}
                className="px-4 py-2 bg-zinc-800 text-zinc-300 rounded-xl text-xs font-black uppercase tracking-widest hover:bg-zinc-700 transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                {detecting ? (
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : (
                  'Detect IP'
                )}
              </button>
            </div>
            <p className="text-xs text-zinc-500 mt-2">
              Enter the public address where your server can be reached. Webhook endpoints will be<br />
              <code className="text-emerald-400 bg-zinc-950 px-2 py-1 rounded">{url || 'https://your-domain.com'}/webhook/&#123;platform&#125;</code>
            </p>
          </div>
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={saving || !url.trim()}
              className="px-6 py-2 bg-emerald-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-emerald-500 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {saving ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Saving...
                </>
              ) : (
                'Save'
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
