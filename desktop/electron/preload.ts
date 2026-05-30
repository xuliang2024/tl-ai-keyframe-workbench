import { contextBridge, ipcRenderer } from "electron";

const desktopApi = {
  getAppVersion: () => ipcRenderer.invoke("app:get-version") as Promise<string>,
  openExternal: (url: string) => ipcRenderer.invoke("shell:open-external", url) as Promise<void>,
};

contextBridge.exposeInMainWorld("desktop", desktopApi);
