import { defineConfig } from 'vitest/config';
export default defineConfig({ test: { include: ['tests/web-unit/**/*_test.ts'], environment: 'node' } });
