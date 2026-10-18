import { spawnSync } from "node:child_process";

// Explicit target; never silently substitute a local server for a hosted check.
let target;
try {
  target = new URL(process.argv[2]);
  if (target.protocol !== "https:" || target.username || target.password ||
      target.pathname !== "/" || target.search || target.hash) throw new Error();
} catch {
  console.error("Usage: npm run test:deployed -- https://your-deployment.vercel.app/");
  process.exit(2);
}
console.log(`Checking hosted release: ${target.origin}`);
const check = spawnSync(process.execPath,
  ["node_modules/@playwright/test/cli.js", "test", ...process.argv.slice(3)], {
    stdio: "inherit",
    env: { ...process.env, CAREER_RADAR_BASE_URL: target.origin },
  });
if (check.error) console.error(check.error.message);
process.exit(check.status ?? 1);
