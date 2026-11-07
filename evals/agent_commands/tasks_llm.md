Write the exact `llm` command (the `llm` CLI by Simon Willison, version 0.37.1) for each task. One command per task, no pipes unless needed.

1. Register an OpenAI-compatible endpoint at http://localhost:8000/v1 that serves the model "qwen3-32b", usable in llm under the alias "qwen", sending the stored key named "local", and marked as supporting tool calling.
2. Show the last 5 logged prompts/responses for the model gpt-4o-mini, as JSON, including token usage.
3. Embed every Markdown file under the ./docs directory (recursively) into the collection "docs", storing the text itself as well.
4. From the collection "docs", return the 3 entries most similar to the text "rate limits", in plain-text output.
5. Set a default option temperature=0.2 for the model gpt-4o so future prompts use it.
6. Run the prompt "summarize this" with the file notes.txt attached as a fragment and the system prompt "Be brief", without logging it to the database, and show token usage.
7. Convert the schema DSL "name, age int" into a JSON schema describing a list of such items.
8. Save a fragment alias "readme" that points at the file README.md.
