#!/usr/bin/env bash
# Create a cambc workspace at $WS (default ~/ws) with the oracle bots linked in.
# The cambc binary downloads its toolchains with its own TLS stack; behind a
# TLS-intercepting proxy those downloads fail, so we pre-fetch them with curl.
set -euo pipefail
WS=${WS:-$HOME/ws}
REPO=$(cd "$(dirname "$0")/.." && pwd)
pip install --quiet cambc==3.0.5
CACHE=$HOME/.cache/cambc
mkdir -p "$CACHE" "$WS"
if [ ! -d "$CACHE/wasi-sdk-33" ]; then
  curl -sSL https://github.com/WebAssembly/wasi-sdk/releases/download/wasi-sdk-33/wasi-sdk-33.0-x86_64-linux.tar.gz | tar xz -C "$CACHE"
  mv "$CACHE/wasi-sdk-33.0-x86_64-linux" "$CACHE/wasi-sdk-33"
fi
if [ ! -d "$CACHE/cmake-3.31.8-linux-x86_64" ]; then
  curl -sSL https://github.com/Kitware/CMake/releases/download/v3.31.8/cmake-3.31.8-linux-x86_64.tar.gz | tar xz -C "$CACHE"
fi
if [ ! -x "$CACHE/ninja-1.12.1-linux-x86_64/ninja" ]; then
  mkdir -p "$CACHE/ninja-1.12.1-linux-x86_64"
  curl -sSL -o /tmp/ninja.zip https://github.com/ninja-build/ninja/releases/download/v1.12.1/ninja-linux.zip
  python3 -c "import zipfile;zipfile.ZipFile('/tmp/ninja.zip').extractall('$CACHE/ninja-1.12.1-linux-x86_64')"
  chmod +x "$CACHE/ninja-1.12.1-linux-x86_64/ninja"
fi
export SSL_CERT_FILE=${SSL_CERT_FILE:-/root/.ccr/ca-bundle.crt}
(cd "$WS" && cambc init --yes .)
for b in "$REPO"/oracle/bots/*/; do ln -sfn "${b%/}" "$WS/bots/$(basename "$b")"; done
echo "workspace ready: $WS"
