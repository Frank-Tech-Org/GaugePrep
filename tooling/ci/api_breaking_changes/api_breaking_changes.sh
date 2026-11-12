#!/usr/bin/env bash
# Builds oasdiff with a pinned hash and fails on a breaking change under /api/v1.
# Usage: api_breaking_changes.sh   (env: OASDIFF_VERSION OASDIFF_GO_VERSION OASDIFF_SHA256)
set -e

bin="$RUNNER_TEMP/oasdiff-bin/oasdiff"
if ! { [ -f "$bin" ] && echo "${OASDIFF_SHA256}  $bin" | sha256sum --check --quiet -; }; then
  rm -rf "$RUNNER_TEMP/oasdiff-bin"
  GOTOOLCHAIN="go${OASDIFF_GO_VERSION}" CGO_ENABLED=0 GOFLAGS="" GOWORK=off GOPATH="$RUNNER_TEMP/gopath" GOBIN="$RUNNER_TEMP/oasdiff-bin" \
    go install -trimpath "github.com/oasdiff/oasdiff@v${OASDIFF_VERSION}"
  echo "${OASDIFF_SHA256}  $bin" | sha256sum --check -
fi
# SECURITY: empty config and our own severity file, so a checkout .oasdiff.* is never read.
: >"$RUNNER_TEMP/oasdiff.config.yaml"
echo 'response-optional-property-removed err' >"$RUNNER_TEMP/oasdiff.severity"
cd "$RUNNER_TEMP"
if ! "$bin" breaking openapi.base.json openapi.head.json --config oasdiff.config.yaml --severity-levels oasdiff.severity --allow-external-refs=false --match-path '^/api/v1/' --fail-on ERR; then
  echo "::error title=Breaking API change::oasdiff found a breaking change under /api/v1 (listed above). Installed copies of the web app still call the old contract: make the change additive, or keep the old field or operation until a new API version."
  exit 1
fi
