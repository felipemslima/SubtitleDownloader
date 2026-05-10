import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

const envDir = path.resolve(__dirname, '..');

function numberFromEnv(value: string | undefined, fallback: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, envDir, '');

  return {
    envDir,
    plugins: [react()],
    server: {
      host: env.VITE_DEV_HOST || '127.0.0.1',
      port: numberFromEnv(env.VITE_DEV_PORT, 5173),
    },
    preview: {
      host: env.VITE_PREVIEW_HOST || env.VITE_DEV_HOST || '127.0.0.1',
      port: numberFromEnv(env.VITE_PREVIEW_PORT, 4173),
    },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
  };
});
