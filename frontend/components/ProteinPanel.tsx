"use client";

import { createContext, useContext, useState } from "react";

type Panel = {
  id: string;
  type: string;
  score: number | null;
  degree: number;
} | null;

const PanelContext = createContext<{
  selected: Panel;
  setSelected: (p: Panel) => void;
}>({ selected: null, setSelected: () => undefined });

export function useProteinPanel() {
  return useContext(PanelContext);
}

export function ProteinPanelProvider({ children }: { children: React.ReactNode }) {
  const [selected, setSelected] = useState<Panel>(null);
  return (
    <PanelContext.Provider value={{ selected, setSelected }}>{children}</PanelContext.Provider>
  );
}
