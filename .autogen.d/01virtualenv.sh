#!/bin/bash
# See: https://stackoverflow.com/questions/59895/how-to-get-the-source-directory-of-a-bash-script-from-within-the-script-itself
# Note: you can't refactor this out: its at the top of every script so the scripts can find their includes.
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

# Source common includes
source include.sh

if ! command -v poetry 1>/dev/null 2>&1 ; then
  log "poetry is not installed. Trying to install it."
  poetry_url="https://install.python-poetry.org"
  if command -v curl 1>/dev/null 2>&1 ; then
    if ! curl -sSL "${poetry_url}" | python3 - ; then
      fatal 1 "Failed to install poetry"
    fi
  elif command -v wget 1>/dev/null 2>&1 ; then
    if ! wget -O - "${poetry_url}" | python3 - ; then
      fatal 1 "Failed to install poetry"
    fi
  else
    fatal 1 "Could not find wget or curl to install poetry with"
  fi
fi

if ! command -v poetry 1>/dev/null 2>&1 ; then
  log "poetry is not installed."
fi

log "Checking for correct Python version"
if command -v pyenv ; then
  python=$(pyenv which python)
else
  python_version=$(cut -d"." -f1,2 < .python-version)
  if ! command -v "python${python_version}" >/dev/null; then
    fatal 1 "Failed to find python${python_version}. Consider installing pyenv to set it up."
  fi
  python=$(command -v python${python_version})
  log "Set python version without pyenv - minor version may not match"
fi

if ! poetry env use "${python}"; then
  fatal 1 "Could not set poetry python interpreter to $python"
fi

if ! poetry install --no-root ; then
  fatal 1 "Could not install dependencies with poetry"
fi

exit 0
