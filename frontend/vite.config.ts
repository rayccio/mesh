import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '');
    return {
        server: {
            port: 3000,
            host: '0.0.0.0',
        },
        plugins: [react()],
        define: {
            // No API keys here – they are never exposed to the frontend
            'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL || 'http://localhost:8000'),
        },
        resolve: {
            alias: {
                '@': path.resolve(__dirname, './src'),
            },
        },
        build: {
            rollupOptions: {
                // No need to externalize react-router-dom – we want it bundled
            }
        }
    };
});
