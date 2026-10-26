import { Suspense, useCallback, useEffect, useState, type ReactNode } from "react";
import { Radar } from "lucide-react";

function Ready({ onReady, children }: { onReady: () => void; children: ReactNode }) {
  useEffect(onReady, [onReady]);
  return children;
}

/** Prepares the tool behind a viewport-centred, minimum two-second introduction. */
export default function ToolEntrance({ name, motionEnabled, children }: { name: string; motionEnabled: boolean; children: ReactNode }) {
  const [minimumElapsed, setMinimumElapsed] = useState(false);
  const [ready, setReady] = useState(false);
  const [loaderGone, setLoaderGone] = useState(false);
  const onReady = useCallback(() => setReady(true), []);
  const revealed = minimumElapsed && ready;
  useEffect(() => {
    const timer = window.setTimeout(() => setMinimumElapsed(true), 2000);
    return () => window.clearTimeout(timer);
  }, []);
  useEffect(() => {
    if (!revealed) return;
    const timer = window.setTimeout(() => setLoaderGone(true), motionEnabled ? 200 : 0);
    return () => window.clearTimeout(timer);
  }, [revealed, motionEnabled]);
  return <div className="tool-entrance" data-state={revealed ? "ready" : "loading"}>
    {!loaderGone && <div className={`tool-loader${revealed ? " is-leaving" : ""}`} role="status" aria-label={`Opening ${name}`} aria-live="polite" aria-atomic="true" data-testid="tool-opening">
      <div className="tool-loader-centre">
        <div className="tool-loader-mark" aria-hidden="true"><span className="tool-loader-orbit" /><span className="tool-loader-inner" /><Radar size={38} strokeWidth={1.4} /></div>
        <p className="tool-loader-kicker">OPENING YOUR WORKSPACE</p>
        <strong>{name}</strong>
        <p>Bringing the analysis into focus.</p>
      </div>
    </div>}
    <Suspense fallback={null}>
      <div className="tool-entrance-content" inert={!revealed} aria-hidden={!revealed} aria-busy={!revealed}>
        <Ready onReady={onReady}>{children}</Ready>
      </div>
    </Suspense>
  </div>;
}
