export type Bootstrap = {
  snapshot: any;
  taxonomy: any[];
  example_description: string;
  data_mode: string;
};
export async function api<T = any>(
  action: string,
  payload: Record<string, unknown> = {},
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(
    action === "bootstrap" ? "/api/index?action=bootstrap" : "/api/index",
    {
      method: action === "bootstrap" ? "GET" : "POST",
      headers:
        action === "bootstrap"
          ? undefined
          : { "Content-Type": "application/json" },
      body:
        action === "bootstrap"
          ? undefined
          : JSON.stringify({ action, ...payload }),
      signal,
    },
  );
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(
      "The analytical API is unavailable. Please retry once it is running.",
    );
  }
  if (!response.ok)
    throw new Error(data.error || "The request could not be completed.");
  return data as T;
}
export function downloadJSON(name: string, data: unknown) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export const DEMO_TEXT =
  "Synthetic demonstration — Junior Data Analyst\nDublin, Ireland. Permanent, hybrid.\nSQL is required; Python is preferred. Excel is essential.\nYou will create reports and communicate with stakeholders.\nSalary: competitive salary.";
export const format = (
  value: number | null | undefined,
  digits = 1,
  suffix = "",
) =>
  value == null
    ? "Not available"
    : value.toLocaleString("en-IE", { maximumFractionDigits: digits }) + suffix;
