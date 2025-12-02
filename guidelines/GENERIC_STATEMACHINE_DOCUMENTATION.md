State Machine Documentation Guidelines

These instructions are for producing documentation that captures the stateful behavior of a Python module — typically one implementing a long-running loop, control flow logic, or task execution pattern — in a consistent, structured Markdown format.

Scope of Application

This format applies when a module exhibits:

A persistent or reactive loop (e.g. worker, poller, daemon)

Distinct logical states (e.g. polling, sleeping, processing, error handling)

Transitions between those states based on internal logic or external events (e.g. DB response, exception)

Required Output Structure

The generated documentation must include the following top-level sections in this order:

1. Header

Format:

# State Machine Documentation: `path/to/codefile.py`


Briefly describe what the module does and why documenting its state machine is useful.

2. States

List each logical state the system enters at runtime. For each state:

Use a clear, noun-style name (e.g. Processing, Backoff, not process_data)

Provide 1–2 sentences describing what happens in that state

Include whether it’s a task-level state, worker-level state, or both

3. Transitions

Describe how the system moves between states. Include:

A bullet-point list for each transition: State A → State B, with the trigger

Group transitions by cause if helpful (e.g., “on DB success”, “on exception”)

Avoid duplicating transition info in prose and tables (choose one as primary)

4. Transition Table

Provide a tabular summary of transitions with this format:

From	To	Trigger	Notes
Startup	Connecting	run_worker() entry	Initial connection attempt
Connecting	Recovery	DB connected	Timer-based lease check

Use this to show full system flow at a glance. Keep it consistent with prose.

5. Terminal and Retry States

Clarify:

Which states represent end-of-task (e.g. done, error)

Whether the loop itself ever exits (usually it doesn't)

How retries are triggered (e.g. lease expiry, connection retry logic)

What resets or resumes look like

6. Invariants

List systemic truths that should always hold. Examples:

“Only one worker may hold a task lease at a time.”

“Tasks in running state must have a valid lease timeout.”

“Every completed task must have a done or error status and updated timestamp.”

These are useful for both developers and incident reviewers.

Output

The result must be:

A Markdown file containing all of the above sections

File name: CODEFILE_STATEMACHINE.md — where CODEFILE is the name of the code file in UPPERCASE and without .py

Saved to: docs/statemachines/

Optional Enhancements

If structure and clarity allow, include:

A visual ASCII or Mermaid diagram of the transitions

A glossary for domain-specific terms (e.g. lease, subtask, try_count)

A short “Design Considerations” section (only if the logic is nontrivial)S
