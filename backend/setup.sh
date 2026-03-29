#!/usr/bin/env bash
# IBMI Backend - Cria venv, instala dependências e (se executado com source) ativa o ambiente.
# Uso recomendado: source setup.sh   (para criar/atualizar e já ativar o venv)
# Uso alternativo:  ./setup.sh        (só cria e instala; depois execute: source .venv/bin/activate)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="${VENV_DIR:-.venv}"
PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" &>/dev/null; then
  echo "Erro: $PYTHON não encontrado. Instale Python 3.11+ ou defina PYTHON=..." >&2
  exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Criando ambiente virtual em $VENV_DIR..."
  "$PYTHON" -m venv "$VENV_DIR"
else
  echo "Ambiente virtual já existe em $VENV_DIR."
fi

echo "Instalando dependências..."
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r requirements.txt -q
echo "Dependências instaladas."

# Se o script foi executado com source setup.sh, ativa o venv no shell atual
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  echo ""
  echo "Para ativar o ambiente virtual, execute:"
  echo "  source $VENV_DIR/bin/activate"
  echo "ou, a partir da pasta backend:"
  echo "  source setup.sh"
else
  echo "Ativando ambiente virtual..."
  # shellcheck source=/dev/null
  source "$VENV_DIR/bin/activate"
  echo "Ambiente ativado. Use 'deactivate' para sair."
fi
