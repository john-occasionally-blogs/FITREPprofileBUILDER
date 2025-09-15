# Development Workflow Blueprint

Purpose: This file explains the step-by-step process the AI will follow to autonomously build and implement the project features.

> Use this file to outline the development workflow and execution process for your project. This guide ensures consistent implementation practices and helps your AI assistant understand how to systematically build and maintain your application.

<!-- Don’t worry if this feels advanced. The AI handles most of this automatically.-->

---

## 1. Plan Creation Process

This section describes how development plans are created and structured for systematic implementation.

When the user requests to implement the application, I will perform the following steps:

1. Create a directory named `.implementation` in the project root.
2. Create a file named `plan.json` inside the `.implementation` directory.
3. The `plan.json` file will contain a JSON object with a single key, `"plan"`, which is an array of step objects.
4. Each step object in the array will have the following structure:
    * `step`: A unique integer representing the step number.
    * `prompt`: A verbose, detailed, and clear instruction for an LLM to accomplish the task for that step.
    * `status`: The current status of the step (e.g., "pending", "completed", "failed").
    * `git_hash`: The Git hash of the commit after the step is completed (or `null`).
    * `summary`: A brief summary of the actions taken in the step (or `null`).
    * `timestamp`: The ISO 8601 timestamp of when the step was completed (or `null`).

---

## 2. Plan Execution and Updates

> This section outlines how the development plan is executed and how progress is tracked throughout the implementation process.

Once the user gives the green light to start the implementation, I will execute all steps in the `plan.json` sequentially and autonomously. I will not ask for permission to proceed between steps.

After each step is successfully completed, I will silently update the `plan.json` file by:
1. Reading the `.implementation/plan.json` file.
2. Finding the step that was just completed.
3. Updating the `status` of that step to "completed".
4. Setting the `summary` field to a brief description of the action I took.
5. Setting the `timestamp` to the current ISO 8601 time.
6. If a git commit was made, I will update the `git_hash` with the hash of that commit.
7. Writing the updated `plan.json` object back to the file.

I will only communicate with the user if a step fails or after the entire plan has been successfully completed.

---

## 3. Execution Constraints and Error Handling

> This section defines the boundaries and error handling procedures during plan execution.

If any step fails, I will stop execution, update the status to "failed", and immediately seek guidance from the user before proceeding.

---

## 4. Self-Optimization Routine (Required Default Behavior)

> This section describes the mandatory self-improvement process that occurs after every code generation or tool use action.

After every code generation or tool use action you perform, you MUST follow this self-optimization routine:

### Analyze
Briefly analyze the user's last action (e.g., did they correct your code, provide a clarification, rerun a command with a new flag?). Also, analyze the changes you just made to the filesystem.

### Compare
Compare this analysis against the current state of all .md context files (claude.md, prd.md, sbom.md, etc.).

### Recommend
If you identify a pattern of correction or a potential for future streamlining, recommend a specific, minimal edit to one of the .md files. For each recommendation, you MUST include:
- **Proposed Change:** The exact text to be added, removed, or changed.
- **Reasoning (Why):** A concise explanation of how this change will improve future interactions (e.g., "This adds the --fix flag to the lint command, which the user has added manually three times, saving a future step.").
- **Risk / New Burden:** Any potential risks or new responsibilities this change introduces for the user.

Please note, it is perfectly ok if you do NOT identify a pattern for improvement and no changes need to be made. We want to improve slowly and iteratively.

### Propose Diff
If the user accepts the recommendation, propose the exact diff or patch to apply the change to the relevant .md file.

---

## 5. Code Commit Workflow and Changelog Execution

When a step in the plan results in a code change, I will create a git commit.

* **Commit Message Style:** Commit messages should follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format (e.g., `feat: add user login button`).
* **Changelog:** After a set of features is complete, I will update the `changelog.md` file.