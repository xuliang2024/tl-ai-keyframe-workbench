import { create } from "zustand";

type WorkbenchState = {
  selectedFrameId: string;
  setSelectedFrameId: (frameId: string) => void;
};

export const useWorkbenchStore = create<WorkbenchState>((set) => ({
  selectedFrameId: "frame-1",
  setSelectedFrameId: (frameId) => set({ selectedFrameId: frameId }),
}));
