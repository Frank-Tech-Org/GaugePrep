// Static export (ADR-004). The export goes to out/; the placeholder deploy keeps dist/.
/** @type {import('next').NextConfig} */
const config = {
  output: "export",
  images: { unoptimized: true },
  trailingSlash: true,
  reactStrictMode: true,
};

export default config;
