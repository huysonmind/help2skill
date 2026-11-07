# `pipx [OPTIONS] COMMAND [ARGS]...`

Install and execute apps from Python packages.

Binaries can either be installed globally into isolated Virtual Environments
or run directly in a temporary Virtual Environment.

Virtual Environment location is ~/Library/Application Support/pipx/venvs.
Symlinks to apps are placed in ~/.local/bin.
Symlinks to manual pages are placed in ~/.local/share/man.

optional environment variables:
  PIPX_HOME              Overrides default pipx location. Virtual Environments
                        will be installed to $PIPX_HOME/venvs.
  PIPX_GLOBAL_HOME       Used instead of PIPX_HOME when the `--global` option
                        is given.
  PIPX_BIN_DIR           Overrides location of app installations. Apps are
                        symlinked or copied here.
  PIPX_GLOBAL_BIN_DIR    Used instead of PIPX_BIN_DIR when the `--global`
                        option is given.
  PIPX_MAN_DIR           Overrides location of manual pages installations.
                        Manual pages are symlinked or copied here.
  PIPX_GLOBAL_MAN_DIR    Used instead of PIPX_MAN_DIR when the `--global`
                        option is given.
  PIPX_COMPLETION_DIR    Overrides location of shell completion installations.
                        Completion scripts are symlinked or copied here.
  PIPX_GLOBAL_COMPLETION_DIR
                        Used instead of PIPX_COMPLETION_DIR when the
                        `--global` option is given.
  PIPX_DEFAULT_PYTHON    Overrides default python used for commands.
  PIPX_DEFAULT_BACKEND   Overrides which backend (`pip` or `uv`) is used for
                        new venvs.
  PIPX_COOLDOWN          Default `--cooldown` in days for the commands that
                        accept it.
  PIPX_DISABLE_SHARED_LIBS_AUTO_UPGRADE
                        Skips automatic shared library upgrades.
  PIPX_USE_EMOJI         Overrides emoji behavior. Default value varies based
                        on platform.

Options:
- `--version`: Print version and exit

Commands (all levels):
- `pipx install`: Install a package
- `pipx install-all`: Install all packages
- `pipx uninject`: Uninstall injected packages from an existing Virtual Environment
- `pipx inject`: Install packages into an existing Virtual Environment
- `pipx expose`: Relink hidden or missing resources of an environment
- `pipx unexpose`: Hide resources without removing an environment
- `pipx pin`: Pin the specified package to prevent it from being upgraded
- `pipx unpin`: Unpin the specified package
- `pipx upgrade`: Upgrade a package
- `pipx upgrade-all`: Upgrade all packages.
- `pipx upgrade-shared`: Upgrade shared libraries.
- `pipx uninstall`: Uninstall a package
- `pipx uninstall-all`: Uninstall all packages
- `pipx reset`: Return pipx to a fresh install
- `pipx reinstall`: Reinstall a package
- `pipx reinstall-all`: Reinstall all packages
- `pipx health`: Check installed package environments
- `pipx repair`: Repair broken package environments
- `pipx list`: List installed packages
- `pipx interpreter`: Interact with interpreters managed by pipx
- `pipx interpreter list`: List available interpreters
- `pipx interpreter prune`: Prune unused interpreters
- `pipx interpreter upgrade`: Upgrade installed interpreters to the latest available micro/patch version
- `pipx cache`: Manage cached run environments
- `pipx cache dir`: Show the cache directory
- `pipx cache purge`: Remove cached run environments
- `pipx manifest`: Manage tools declared in an explicit manifest
- `pipx manifest lock`: Resolve a tool manifest with nab
- `pipx manifest sync`: Apply a tool manifest
- `pipx run`: Download the latest version of a package to a temporary virtual environment, then run an app from it. Also compatible with local `__pypackages__` directory (experimental).
- `pipx exec`: Run an application from an existing pipx environment
- `pipx runpip`: Run pip, or `uv pip` under the uv backend, in an existing pipx-managed Virtual Environment
- `pipx ensurepath`: Ensure directories necessary for pipx operation are in your PATH environment variable.
- `pipx environment`: Print a list of environment variables and paths used by pipx.
- `pipx completions`: Print instructions on enabling shell completions for pipx
- `pipx help`: Show help for pipx or a command

Shared options (listed by name in the commands that accept them):
- `-q, --quiet` (repeat to increase, e.g. -qq): Give less output. May be used multiple times corresponding to the ERROR and CRITICAL logging levels. The count maxes out at 2.
- `-v, --verbose` (repeat to increase, e.g. -vv): Give more output. May be used multiple times corresponding to the INFO, DEBUG and NOTSET logging levels. The count maxes out at 3.
- `--skip-maintenance`: Do not upgrade shared libraries; use bundled pip when creating them.
- `--python TEXT`: Python to install with. Possible values can be the executable name (python3.11), the version of an available system Python or to pass to py launcher (3.11), or the full path to the executable. Requires Python 3.11 or above.
- `--fetch-python [always|missing|never]`: When to fetch a standalone Python build from python-build-standalone. 'always' uses a standalone build even when a system Python matches; 'missing' downloads only when the requested version is not found locally; 'never' never downloads. Defaults to PIPX_FETCH_PYTHON, or 'never'.
- `--fetch-missing-python`: Deprecated: alias for --fetch-python=missing.
- `--pip-args TEXT`: Arbitrary pip arguments to pass directly to pip install/upgrade commands. Under the uv backend, `pipx run` translates a subset (--index-url/-i, --extra-index-url, --find-links/-f, --trusted-host, --no-binary, --only-binary, --pre, --upgrade/-U, --no-cache-dir) and rejects other flags; other commands pass them to `uv pip install` unchanged.
- `--cooldown DAYS`: Ignore index artifacts uploaded fewer than DAYS days ago. Defaults to PIPX_COOLDOWN; pass 0 to opt out.
- `--backend [pip|uv]`: Backend used for creating venvs and managing packages. Defaults to PIPX_DEFAULT_BACKEND when set, else 'uv' when uv is available (via the `pipx[uv]` extra or on PATH), else 'pip'. Commands on an existing venv keep its recorded backend and warn when this flag differs; `pipx reinstall` and `pipx reinstall-all` rebuild venvs with it.
- `--output [human|json]` (default: human): Select the output format.
- `-f, --force`: Modify existing virtual environment and files in PIPX_BIN_DIR and PIPX_MAN_DIR

## `pipx install [OPTIONS] PACKAGE_SPEC...`

The install command is the preferred way to globally install apps
from Python packages and PEP 723 scripts. It creates an isolated virtual
environment for the source, then ensures its apps are
accessible on your $PATH. The package's manual pages installed in
share/man/man[1-9] can be viewed with man on an operating system where
it is available and the path in the environment variable `PIPX_MAN_DIR`
(default: ~/.local/share/man) is in the man search path
($MANPATH).

You get apps you can run from anywhere, in packages you can
cleanly upgrade or uninstall. Each package gets its own virtual
environment, so its dependencies cannot conflict with those of
other packages or interfere with your OS's python packages. You
do not need 'sudo' for this.

pipx install PACKAGE_SPEC ...
pipx install --python PYTHON PACKAGE_SPEC
pipx install VCS_URL
pipx install ./LOCAL_PATH
pipx install ./SCRIPT.py
pipx install ZIP_FILE
pipx install TAR_GZ_FILE

Package specs are passed to the selected backend. PEP 723 scripts are
installed with their declared dependencies.

Virtual Environments will be installed to `$PIPX_HOME/venvs`.
The default pipx home location is ~/Library/Application Support/pipx and can
be overridden by setting the environment variable `PIPX_HOME`.
If the `--global` option is used, the default pipx home location
instead is /opt/pipx and can be overridden
by setting the environment variable `PIPX_GLOBAL_HOME`.

The default app location is ~/.local/bin and can be
overridden by setting the environment variable `PIPX_BIN_DIR`.
If the `--global` option is used, the default app location instead
is /usr/local/bin and can be overridden by
setting the environment variable `PIPX_GLOBAL_BIN_DIR`.

The default manual pages location is ~/.local/share/man and
can be overridden by setting the environment variable `PIPX_MAN_DIR`.
If the `--global` option is used, the default manual pages location
instead is /usr/local/share/man and can be overridden
by setting the environment variable `PIPX_GLOBAL_MAN_DIR`.

The default python executable used to install a package is
/path/to/python and can be overridden
by setting the environment variable `PIPX_DEFAULT_PYTHON`.

Arguments:
- `PACKAGE_SPEC...` (text; required): package name(s), PEP 723 script(s), or installation spec(s)

Options:
- `--global`: Perform action globally for all users.
- `--include-deps`: Include apps and manual pages from all dependencies
- `--include-resources-from PACKAGE` (repeatable): Include apps and manual pages from this dependency. Repeat for multiple dependencies
- `-f, --force`: Modify existing virtual environment and files in PIPX_BIN_DIR and PIPX_MAN_DIR; --python does not change an existing environment's Python, use `pipx reinstall --python` for that
- `-U, --upgrade`: Upgrade or downgrade an existing package when its version does not satisfy the supplied spec, removing exposed apps, manual pages, and shell completions the new version no longer ships
- `--upgrade-strategy [only-if-needed|eager]`: How dependency upgrades are handled when --upgrade changes an existing package
- `--suffix TEXT`: Optional suffix for virtual environment and executable names. It goes at the end of each app name (pip3.14 becomes pip3.14_a), before the file extension on Windows (pip3.14_a.exe, hello_a.py).
- `--preinstall _PACKAGE_SPEC` (repeatable): Optional package to be installed into the Virtual Environment before installing the main package. Use this flag multiple times if you want to preinstall multiple packages.
- `--app TEXT` (repeatable): Require this application entry point after installation. Repeat to require multiple entry points.
- `--lock PATH`: Install the environment from an explicit pylock.toml file.
- `--system-site-packages`: Give the virtual environment access to the system site-packages dir.
- `-i, --index-url TEXT`: Base URL of Python Package Index
- `-e, --editable`: Install a project in editable mode
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--python`, `--fetch-python`, `--fetch-missing-python`, `--pip-args`, `--cooldown`, `--backend`, `--output`

Mutually exclusive: `--include-deps`, `--include-resources-from`

Mutually exclusive: `--fetch-python`, `--fetch-missing-python`

## `pipx install-all [OPTIONS] SPEC_METADATA_FILE`

Installs all the packages according to spec metadata file. Installs up to eight environments at once and prints the output of each in turn, in file order; --verbose installs them one at a time.

Arguments:
- `SPEC_METADATA_FILE` (text; required): Spec metadata file generated from pipx list --output json

Options:
- `--global`: Perform action globally for all users.
- `-f, --force`: Modify existing virtual environment and files in PIPX_BIN_DIR and PIPX_MAN_DIR; --python does not change an existing environment's Python, use `pipx reinstall --python` for that
- `--system-site-packages`: Give the virtual environment access to the system site-packages dir.
- `-i, --index-url TEXT`: Base URL of Python Package Index
- `-e, --editable`: Install a project in editable mode
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--python`, `--fetch-python`, `--fetch-missing-python`, `--pip-args`, `--cooldown`, `--backend`

Mutually exclusive: `--fetch-python`, `--fetch-missing-python`

## `pipx uninject [OPTIONS] ENVIRONMENT DEPENDENCIES...`

Uninstalls injected packages from an existing pipx-managed virtual environment.

Arguments:
- `ENVIRONMENT` (text; required): Name of the existing pipx-managed environment to uninject from
- `DEPENDENCIES...` (text; required): the package names to uninject from the environment

Options:
- `--global`: Perform action globally for all users.
- `--leave-deps`: Only uninstall the main injected package but leave its dependencies installed.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx inject [OPTIONS] ENVIRONMENT [DEPENDENCIES...]`

Installs packages to an existing pipx-managed virtual environment.

Arguments:
- `ENVIRONMENT` (text; required): Name of the existing pipx-managed environment to inject into
- `[DEPENDENCIES...]` (text): the packages to inject into the environment--either package name or pip package spec

Options:
- `--global`: Perform action globally for all users.
- `-r, --requirement file` (repeatable): file containing the packages to inject into the Virtual Environment--one package name or pip package spec per line. May be specified multiple times.
- `--include-apps`: Add apps from the injected packages onto your PATH and expose their manual pages
- `--include-deps`: Include apps and manual pages from all dependencies
- `--include-resources-from PACKAGE` (repeatable): Include apps and manual pages from this dependency. Repeat for multiple dependencies
- `--system-site-packages`: Give the virtual environment access to the system site-packages dir. Ignored, since the existing environment keeps the venv options it was installed with; accepted for compatibility.
- `-i, --index-url TEXT`: Base URL of Python Package Index
- `-e, --editable`: Install a project in editable mode
- `--with-suffix`: Add the suffix (if given) of the Virtual Environment to the packages to inject
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--pip-args`, `--cooldown`, `-f, --force`, `--backend`, `--output`

Mutually exclusive: `--include-deps`, `--include-resources-from`

## `pipx expose [OPTIONS] ENVIRONMENT`

Link each missing app, manual page, and shell completion without rebuilding the environment.

Arguments:
- `ENVIRONMENT` (text; required): Environment to expose

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx unexpose [OPTIONS] ENVIRONMENT`

Remove global links or copies while retaining the managed environment.

Arguments:
- `ENVIRONMENT` (text; required): Environment to hide

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx pin [OPTIONS] ENVIRONMENT`

Pin the specified package to prevent it from being upgraded

Arguments:
- `ENVIRONMENT` (text; required): Environment to pin

Options:
- `--global`: Perform action globally for all users.
- `--injected-only`: Pin injected packages in venv only, so that they will not be upgraded during upgrade operations. Note that this should not be passed if you wish to pin both main package and injected packages.
- `--skip TEXT [TEXT ...]`: Skip these packages. Implies `--injected-only`.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx unpin [OPTIONS] ENVIRONMENT`

Unpin the specified package and all injected packages in its venv to allow them to be upgraded

Arguments:
- `ENVIRONMENT` (text; required): Environment to unpin

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx upgrade [OPTIONS] PACKAGES...`

Upgrade package(s) in pipx-managed Virtual Environment(s) by running 'pip install --upgrade PACKAGE' ('uv pip install --upgrade PACKAGE' under the uv backend). Apps, manual pages, and shell completions the new version adds are exposed, and those it no longer ships are removed.

Arguments:
- `PACKAGES...` (text; required): names of the packages to upgrade

Options:
- `--global`: Perform action globally for all users.
- `--include-injected`: Also upgrade packages injected into the main app's environment
- `--system-site-packages`: Give the virtual environment access to the system site-packages dir. Only used with --install.
- `-i, --index-url TEXT`: Base URL of Python Package Index
- `-e, --editable`: Install a project in editable mode
- `--install`: Install package spec if missing
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `-f, --force`, `--pip-args`, `--cooldown`, `--python`, `--fetch-python`, `--fetch-missing-python`, `--backend`, `--output`

Mutually exclusive: `--fetch-python`, `--fetch-missing-python`

## `pipx upgrade-all [OPTIONS]`

Upgrades all packages within their virtual environments by running 'pip install --upgrade PACKAGE' ('uv pip install --upgrade PACKAGE' under the uv backend). Apps, manual pages, and shell completions a new version adds are exposed, and those it no longer ships are removed. Upgrades up to eight environments at once and prints the output of each in turn; --verbose upgrades them one at a time.

Options:
- `--global`: Perform action globally for all users.
- `--include-injected`: Also upgrade packages injected into the main app's environment
- `--skip TEXT [TEXT ...]`: skip these packages
- `--system-site-packages`: Give the virtual environment access to the system site-packages dir. Ignored, since the existing environment keeps the venv options it was installed with; accepted for compatibility.
- `-i, --index-url TEXT`: Base URL of Python Package Index
- `-e, --editable`: Install a project in editable mode
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `-f, --force`, `--pip-args`, `--cooldown`, `--backend`, `--output`

## `pipx upgrade-shared [OPTIONS]`

Upgrade shared libraries now. Other commands refresh them once they are over 30 days old.

Options:
- `--global`: Perform action globally for all users.
- `--pip-args TEXT`: Arbitrary pip arguments to pass directly to pip install/upgrade commands
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx uninstall [OPTIONS] ENVIRONMENT`

Uninstalls a pipx-managed Virtual Environment by deleting it and any files that point to its apps.

Arguments:
- `ENVIRONMENT` (text; required)

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx uninstall-all [OPTIONS]`

Uninstall all pipx-managed packages

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx reset [OPTIONS]`

Uninstall every pipx-managed package and remove the shared libraries, the caches, the standalone interpreters, the logs and the trash, which returns pipx to the state it had when it was installed.

Options:
- `--global`: Perform action globally for all users.
- `-y, --yes`: Reset without asking for confirmation
- `--dry-run`: Report what a reset would remove and stop
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx reinstall [OPTIONS] ENVIRONMENT`

Reinstalls a package.

Package is uninstalled, then installed with pipx install PACKAGE
with the same options used in the original install of PACKAGE.

Arguments:
- `ENVIRONMENT` (text; required)

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--python`, `--fetch-python`, `--fetch-missing-python`, `--backend`, `--output`

Mutually exclusive: `--fetch-python`, `--fetch-missing-python`

## `pipx reinstall-all [OPTIONS]`

Reinstalls all packages.

Packages are uninstalled, then installed with pipx install PACKAGE
with the same options used in the original install of PACKAGE.
Run it after upgrading Python to move all your packages to the
new version.

Rebuilds up to eight environments at once and prints the output
of each in turn; --verbose rebuilds them one at a time.

Options:
- `--global`: Perform action globally for all users.
- `--skip TEXT [TEXT ...]`: skip these packages
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--python`, `--fetch-python`, `--fetch-missing-python`, `--backend`, `--output`

Mutually exclusive: `--fetch-python`, `--fetch-missing-python`

## `pipx health [OPTIONS] [PACKAGES...]`

Check whether installed package environments can run their Python interpreter.

Arguments:
- `[PACKAGES...]` (text): Installed packages to check

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx repair [OPTIONS] [PACKAGES...]`

Reinstall packages whose environments cannot run their Python interpreter.

Arguments:
- `[PACKAGES...]` (text): Installed packages to repair

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--python`, `--fetch-python`, `--fetch-missing-python`, `--backend`, `--output`

Mutually exclusive: `--fetch-python`, `--fetch-missing-python`

## `pipx list [OPTIONS] [PACKAGES...]`

List packages and apps installed with pipx

Arguments:
- `[PACKAGES...]` (text): Installed packages to list

Options:
- `--global`: Perform action globally for all users.
- `--include-injected`: Show packages injected into the main app's environment
- `--outdated`: List packages with an available upgrade.
- `--short`: List packages only.
- `--pinned`: List pinned packages only. Pass --include-injected at the same time to list injected packages that were pinned.
- `--json`: Print the installed-package snapshot as JSON, the format install-all consumes.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

Mutually exclusive: `--short`, `--pinned`

Mutually exclusive: `--output`, `--json`

## `pipx interpreter COMMAND [ARGS]...`

Interact with interpreters managed by pipx

Commands:
- `pipx interpreter list`: List available interpreters
- `pipx interpreter prune`: Prune unused interpreters
- `pipx interpreter upgrade`: Upgrade installed interpreters to the latest available micro/patch version

## `pipx interpreter list [OPTIONS]`

List available interpreters

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx interpreter prune [OPTIONS]`

Prune unused interpreters

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx interpreter upgrade [OPTIONS]`

Upgrade installed interpreters to the latest available micro/patch version

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx cache COMMAND [ARGS]...`

Manage cached run environments

Commands:
- `pipx cache dir`: Show the cache directory
- `pipx cache purge`: Remove cached run environments

## `pipx cache dir [OPTIONS]`

Show the cache directory

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx cache purge [OPTIONS]`

Remove cached run environments

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx manifest COMMAND [ARGS]...`

Manage tools declared in an explicit manifest

Commands:
- `pipx manifest lock`: Resolve a tool manifest with nab
- `pipx manifest sync`: Apply a tool manifest

## `pipx manifest lock [OPTIONS] MANIFEST`

Resolve each locked tool in an explicit manifest into a separate PEP 751 lock file.

Arguments:
- `MANIFEST` (path; required): Path to the tool manifest.

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--output`

## `pipx manifest sync [OPTIONS] MANIFEST`

Install, upgrade, or downgrade the tools declared in an explicit manifest.

Arguments:
- `MANIFEST` (path; required): Path to the tool manifest.

Options:
- `--global`: Perform action globally for all users.
- `--prune`: Uninstall environments absent from the manifest.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--backend`, `--output`

## `pipx run [OPTIONS] [app ......]`

Download the latest version of a package to a temporary virtual environment,
then run an app from it. The environment will be cached
and reused for up to 14 days. This
means subsequent calls to 'run' for the same package will be faster
since they can reuse the cached Virtual Environment.

In support of PEP 582 'run' will use apps found in a local __pypackages__
directory, if present. This behavior is experimental and is a
companion tool to pythonloc. pipx may change or remove it
in a future release. See https://github.com/cs01/pythonloc.

Arguments:
- `[app ......]` (text): app/package name and any arguments to be passed to it

Options:
- `--global`: Perform action globally for all users.
- `--no-cache`: Do not reuse cached virtual environment if it exists
- `--refresh`: Rebuild and cache the virtual environment
- `--no-path-check`: Do not check whether the app is already on PATH
- `--python-args ARGS`: Arguments to pass to the Python interpreter that runs the application
- `--path`: Interpret app name as a local path
- `--pypackages`: Require app to be run from local __pypackages__ directory
- `--with _PACKAGE_SPEC` (repeatable): Extra dependencies to add to the temporary environment
- `--spec TEXT`: The package name or specific installation source to install the app from. For example `--spec mypackage==2.0.0` or `--spec git+https://github.com/user/repo.git@branch`
- `--system-site-packages`: Give the virtual environment access to the system site-packages dir. Not supported under the uv backend.
- `-i, --index-url TEXT`: Base URL of Python Package Index
- `-e, --editable`: Install a project in editable mode
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`, `--python`, `--fetch-python`, `--fetch-missing-python`, `--pip-args`, `--cooldown`, `--backend`

Mutually exclusive: `--no-cache`, `--refresh`

Mutually exclusive: `--fetch-python`, `--fetch-missing-python`

## `pipx exec [OPTIONS] ENVIRONMENT APP [APP_ARGS...]`

Run an application from an existing pipx environment

Arguments:
- `ENVIRONMENT` (text; required): Name of the existing pipx environment
- `APP` (text; required): Application to run
- `[APP_ARGS...]` (text): Arguments to pass to the application

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`

## `pipx runpip [OPTIONS] PACKAGE [PIPARGS...]`

Run pip, or `uv pip` under the uv backend, in an existing pipx-managed Virtual Environment

Arguments:
- `PACKAGE` (text; required): Name of the existing pipx-managed Virtual Environment to run pip in
- `[PIPARGS...]` (text): Arguments to forward to pip command

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`

## `pipx ensurepath [OPTIONS]`

Ensure directory where pipx stores apps is in your PATH environment variable. Also if pipx was installed via `pip install --user`, ensure pipx itself is in your PATH. This command may modify your shell configuration, such as '~/.bashrc', or the system PATH configuration when used with `--global`.

Options:
- `--global`: Perform action globally for all users.
- `--prepend`: Prepend directories to your PATH instead of appending. Use it to put pipx apps ahead of system apps.
- `-f, --force`: Add text to your shell's config file even if it looks like your PATH already contains paths to pipx and pipx-install apps. With --global, also replace a system PATH configuration file that holds content pipx did not write.
- `--all-shells`: Add directories to PATH in all shells instead of just the current one.
- `--dry-run`: Report what would be added to PATH without modifying PATH or any shell configuration file.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`

## `pipx environment [OPTIONS]`

Prints the names and current values of environment variables used by pipx,
followed by internal pipx variables which are derived from the environment
variables and platform specific default values.

Available variables:
PIPX_HOME, PIPX_GLOBAL_HOME, PIPX_BIN_DIR, PIPX_GLOBAL_BIN_DIR,
PIPX_MAN_DIR, PIPX_COMPLETION_DIR, PIPX_GLOBAL_MAN_DIR,
PIPX_GLOBAL_COMPLETION_DIR, PIPX_SHARED_LIBS, PIPX_DEFAULT_PYTHON,
PIPX_DEFAULT_BACKEND, PIPX_COOLDOWN, PIPX_FETCH_MISSING_PYTHON,
PIPX_FETCH_PYTHON, PIPX_DISABLE_SHARED_LIBS_AUTO_UPGRADE,
PIPX_USE_EMOJI, PIPX_MAX_LOGS

Options:
- `--global`: Perform action globally for all users.
- `-V, --value [PIPX_HOME|PIPX_GLOBAL_HOME|PIPX_BIN_DIR|PIPX_GLOBAL_BIN_DIR|PIPX_MAN_DIR|PIPX_COMPLETION_DIR|PIPX_GLOBAL_MAN_DIR|PIPX_GLOBAL_COMPLETION_DIR|PIPX_SHARED_LIBS|PIPX_DEFAULT_PYTHON|PIPX_DEFAULT_BACKEND|PIPX_COOLDOWN|PIPX_FETCH_MISSING_PYTHON|PIPX_FETCH_PYTHON|PIPX_DISABLE_SHARED_LIBS_AUTO_UPGRADE|PIPX_USE_EMOJI|PIPX_MAX_LOGS|PIPX_LOCAL_VENVS|PIPX_LOG_DIR|PIPX_TRASH_DIR|PIPX_VENV_CACHEDIR|PIPX_STANDALONE_PYTHON_CACHEDIR|PIPX_RESOLVED_BACKEND|PIPX_BACKEND_SOURCE|PIPX_UV_BINARY|UV_CACHE_DIR]`: Print the value of the variable.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`

## `pipx completions [OPTIONS]`

Print instructions on enabling shell completions for pipx

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`

## `pipx help [OPTIONS]`

Show help for pipx or a command

Options:
- `--global`: Perform action globally for all users.
- Shared options: `-q, --quiet`, `-v, --verbose`, `--skip-maintenance`
