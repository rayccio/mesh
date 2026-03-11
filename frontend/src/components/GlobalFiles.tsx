import React, { useState, useEffect, useRef } from 'react';
import { FileEntry } from '../types';
import { orchestratorService } from '../services/orchestratorService';
import { Icons } from '../constants';

interface GlobalFilesProps {
  onError?: (error: string) => void;
}

export const GlobalFiles: React.FC<GlobalFilesProps> = ({ onError }) => {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadFiles = async () => {
    try {
      const data = await orchestratorService.listGlobalFiles();
      setFiles(data);
    } catch (err) {
      console.error('Failed to load global files', err);
      onError?.('Failed to load global files');
    }
  };

  useEffect(() => {
    loadFiles();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    try {
      await orchestratorService.uploadGlobalFile(file);
      await loadFiles();
    } catch (err) {
      console.error('File upload failed', err);
      onError?.('File upload failed');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDeleteFile = async (filename: string) => {
    if (!confirm(`Delete ${filename}?`)) return;
    try {
      await orchestratorService.deleteGlobalFile(filename);
      await loadFiles();
    } catch (err) {
      console.error('File deletion failed', err);
      onError?.('File deletion failed');
    }
  };

  return (
    <div className="bg-zinc-900 rounded-3xl border border-zinc-800 p-6 shadow-2xl">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-black tracking-tight text-emerald-500">Global Files</h3>
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="px-4 py-2 bg-emerald-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-emerald-500 transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {isUploading ? (
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <Icons.Plus />
          )}
          Upload File
        </button>
        <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" />
      </div>

      <div className="space-y-2">
        {files.length === 0 && (
          <p className="text-zinc-500 italic text-center py-8">No global files uploaded.</p>
        )}
        {files.map(file => (
          <div key={file.id} className="flex items-center justify-between p-3 bg-zinc-950 rounded-xl border border-zinc-800">
            <div className="flex items-center gap-3">
              <Icons.File className="text-emerald-500" />
              <span className="text-sm font-medium text-zinc-300">{file.name}</span>
              <span className="text-[10px] text-zinc-500">({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
            <div className="flex items-center gap-2">
              <a
                href={orchestratorService.getGlobalFileDownloadUrl(file.name)}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 text-zinc-500 hover:text-emerald-400 transition-colors"
                title="Download"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </a>
              <button
                onClick={() => handleDeleteFile(file.name)}
                className="p-2 text-zinc-500 hover:text-red-500 transition-colors"
                title="Delete"
              >
                <Icons.Trash className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
