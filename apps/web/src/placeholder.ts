export const ENVIRONMENTS = ["dev", "staging"] as const;
export type PlaceholderEnvironment = (typeof ENVIRONMENTS)[number];

export function isEnvironment(value: string): value is PlaceholderEnvironment {
  return (ENVIRONMENTS as readonly string[]).includes(value);
}

// The commit goes into the page as text, so only a plain hex SHA is accepted.
export function isCommit(value: string): boolean {
  return /^[0-9a-f]{7,40}$/.test(value);
}

export function renderPlaceholder(
  environment: PlaceholderEnvironment,
  commit: string,
): string {
  if (!isEnvironment(environment)) {
    throw new Error(`Unknown environment: ${String(environment)}`);
  }
  if (!isCommit(commit)) {
    throw new Error("The commit must be 7 to 40 lowercase hex characters");
  }
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>GaugePrep (${environment})</title>
<style>body{font-family:system-ui,sans-serif;margin:3rem auto;max-width:32rem;padding:0 1rem;line-height:1.5}</style>
</head>
<body>
<main>
<h1>GaugePrep</h1>
<p>Environment: <strong id="environment">${environment}</strong></p>
<p>Commit: <code id="commit">${commit}</code></p>
</main>
</body>
</html>
`;
}
