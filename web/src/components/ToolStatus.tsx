/** A stable live region: announces work without shifting the tool controls. */
export default function ToolStatus({ busy, children }: { busy: boolean; children: string }) {
  return <div className="tool-status" role="status" aria-live="polite" aria-atomic="true">
    {busy && <><span className="work-indicator" aria-hidden="true" /><span>{children}</span></>}
  </div>;
}
