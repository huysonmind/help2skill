---
name: llm
description: "Use the llm CLI to run prompts, manage models, templates, logs and embeddings."
---

<!-- help2skill:begin program=llm max-chars=30000 (generated from the CLI; edit outside this block) -->
## `llm [OPTIONS] COMMAND [ARGS]...`

Access Large Language Models from the command-line

Documentation: https://llm.datasette.io/

LLM can run models from many different providers. Consult the
plugin directory for a list of available models:

https://llm.datasette.io/en/stable/plugins/directory.html

To get started with OpenAI, obtain an API key from them and:

    $ llm keys set openai
    Enter key: ...

Then execute a prompt like this:

    llm 'Five outrageous names for a pet pelican'

For a full list of prompting options run:

    llm prompt --help

Options:
- `--version`: Show the version and exit.

Default command: `prompt`. When the first argument is not a command name, `llm ARGS...` runs `llm prompt ARGS...`.

Commands (all levels):
- `llm aliases`: Manage model aliases
- `llm aliases list` (default command): List current aliases
- `llm aliases path`: Output the path to the aliases.json file
- `llm aliases remove`: Remove an alias
- `llm aliases set`: Set an alias for a model
- `llm chat`: Hold an ongoing chat with a model.
- `llm collections`: View and manage collections of embeddings
- `llm collections delete`: Delete the specified collection
- `llm collections list` (default command): View a list of collections
- `llm collections path`: Output the path to the embeddings database
- `llm embed`: Embed text and store or return the result
- `llm embed-models`: Manage available embedding models
- `llm embed-models default`: Show or set the default embedding model
- `llm embed-models list` (default command): List available embedding models
- `llm embed-multi`: Store embeddings for multiple strings at once in the specified collection.
- `llm fragments`: Manage fragments that are stored in the database
- `llm fragments list` (default command): List current fragments
- `llm fragments loaders`: Show fragment loaders registered by plugins
- `llm fragments remove`: Remove a fragment alias
- `llm fragments set`: Set an alias for a fragment
- `llm fragments show`: Display the fragment stored under an alias or hash
- `llm install`: Install packages from PyPI into the same environment as LLM
- `llm keys`: Manage stored API keys for different models
- `llm keys get`: Return the value of a stored key
- `llm keys list` (default command): List names of all stored keys
- `llm keys path`: Output the path to the keys.json file
- `llm keys set`: Save a key in the keys.json file
- `llm logs`: Tools for exploring logged prompts and responses
- `llm logs backup`: Backup your logs database to this file
- `llm logs list` (default command): Show logged prompts and their responses
- `llm logs off`: Turn off logging for all prompts
- `llm logs on`: Turn on logging for all prompts
- `llm logs path`: Output the path to the logs.db file
- `llm logs status`: Show current status of database logging
- `llm models`: Manage available models
- `llm models default`: Show or set the default model
- `llm models list` (default command): List available models
- `llm models options`: Manage default options for models
- `llm models options clear`: Clear default option(s) for a model
- `llm models options list` (default command): List default options for all models
- `llm models options set`: Set a default option for a model
- `llm models options show`: List default options set for a specific model
- `llm openai`: Commands for working with OpenAI and OpenAI-compatible APIs
- `llm openai endpoint`: Work with OpenAI-compatible endpoints
- `llm openai endpoint add`: Save an OpenAI-compatible endpoint to extra-openai-models.yaml
- `llm openai endpoint list`: List endpoints saved in extra-openai-models.yaml
- `llm openai endpoint path`: Output the path to the extra-openai-models.yaml file
- `llm openai endpoint prompt` (default command): Run against an OpenAI-compatible endpoint without logging.
- `llm openai endpoint remove`: Remove a saved endpoint from extra-openai-models.yaml
- `llm openai models`: List models available to you from the OpenAI API
- `llm plugins`: List installed plugins
- `llm prompt` (default command): Execute a prompt
- `llm schemas`: Manage stored schemas
- `llm schemas dsl`: Convert LLM's schema DSL to a JSON schema
- `llm schemas list` (default command): List stored schemas
- `llm schemas show`: Show a stored schema
- `llm similar`: Return top N similar IDs from a collection using cosine similarity.
- `llm templates`: Manage stored prompt templates
- `llm templates edit`: Edit the specified prompt template using the default $EDITOR
- `llm templates list` (default command): List available prompt templates
- `llm templates loaders`: Show template loaders registered by plugins
- `llm templates path`: Output the path to the templates directory
- `llm templates show`: Show the specified prompt template
- `llm tools`: Manage tools that can be made available to LLMs
- `llm tools list` (default command): List available tools, optionally including tools supported by a model
- `llm uninstall`: Uninstall Python packages from the LLM environment

Full reference for every command: [references/commands.md](references/commands.md). Read only the section of the command you need.
<!-- help2skill:end -->
