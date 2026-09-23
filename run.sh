#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# completion
completion() {
  cat <<'EOF'
_wwsai_run()
{
  local cur prev cword
  cword=${COMP_CWORD:-0}
  cur=${COMP_WORDS[$cword]:-}
  prev=${COMP_WORDS[$((cword - 1))]:-}
  compopt +o default 2>/dev/null || true
  compopt +o bashdefault 2>/dev/null || true
  local cmds="up down status history api-key dashboard help completion"
  local api_cmds="gen list rename delete"
  local history_opts="--key --provider --contains --since --limit"
  local provider_opts="openai anthropic"
  if [[ ${COMP_WORDS[1]:-} == api-key ]]; then
    if [[ $cword -eq 2 ]]; then
      COMPREPLY=( $(compgen -W "$api_cmds" -- "$cur") )
    fi
    return
  fi
  if [[ ${COMP_WORDS[1]:-} == history ]]; then
    if [[ $prev == --provider ]]; then
      COMPREPLY=( $(compgen -W "$provider_opts" -- "$cur") )
    else
      COMPREPLY=( $(compgen -W "$history_opts" -- "$cur") )
    fi
    return
  fi
  if [[ $cword -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "$cmds" -- "$cur") )
  fi
}
complete -F _wwsai_run ./run.sh run.sh
EOF
}

register_completion() {
  eval "$(completion)"
}

# env
ensure_env() {
  mkdir -p .runtime/uv-cache
  export UV_CACHE_DIR="$PWD/.runtime/uv-cache"
  if command -v uv >/dev/null 2>&1; then
    if [[ ! -d .venv ]]; then
      uv venv >/dev/null 2>&1
    fi
    PY=(uv run python)
  else
    PY=(python3)
  fi
}

# dispatch
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  register_completion
  return 0
fi

case "${1:-serve}" in
  completion)
    completion
    ;;
  help|-h|--help)
    ensure_env
    "${PY[@]}" -m src.cli help
    ;;
  serve|up|down|status|history|dashboard|api-key)
    ensure_env
    if [[ $# -eq 0 ]]; then
      set -- serve
    fi
    "${PY[@]}" -m src.cli "$@"
    ;;
  *)
    echo "Unknown command: $1" >&2
    echo "Run ./run.sh help" >&2
    exit 2
    ;;
esac
