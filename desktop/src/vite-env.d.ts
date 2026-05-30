/// <reference types="vite/client" />

interface Window {
  desktop: {
    getAppVersion: () => Promise<string>;
    openExternal: (url: string) => Promise<void>;
  };
}
