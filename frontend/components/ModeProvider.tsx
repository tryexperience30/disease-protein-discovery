"use client";

import { createContext, useContext, useMemo, useState } from "react";

type Mode = "explorer" | "research";

const ModeContext = createContext<{
  mode: Mode;
  setMode: (m: Mode) => void;
}>({ mode: "explorer", setMode: () => undefined });

export function ModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setMode] = useState<Mode>("explorer");
  const value = useMemo(() => ({ mode, setMode }), [mode]);
  return <ModeContext.Provider value={value}>{children}</ModeContext.Provider>;
}

export function useMode() {
  return useContext(ModeContext);
}
