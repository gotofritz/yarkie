# Yarkie Tools Refactoring Plan

## 1. Overview

This document outlines a plan for refactoring the Yarkie Tools Python application. The primary goal is to simplify the architecture, improve modularity, and increase maintainability by addressing architectural smells and establishing clearer patterns. The refactoring will be done in small, incremental steps to minimize disruption.

## 2. Current State Analysis

The application is a command-line interface built with Click. While functional, it exhibits several architectural issues stemming from past refactoring attempts, leading to a "messy" state.

**Key Architectural Points:**

- **Good Separation of Concerns:** The data layer is well-structured, with a clear distinction between Pydantic models (`tools/models`) for data transfer objects (DTOs) and the SQLAlchemy ORM layer (`tools/orm`) for database mapping.
- **Configuration Redundancy:** There are two conflicting sources of configuration:
  1.  A modern, Pydantic-based system in `tools/config/app_config.py`.
  2.  A legacy, hardcoded file at `tools/settings.py`, which is marked for removal.
- **Coupled `AppContext`:** The `AppContext` class (`tools/app_context.py`) acts as a Service Locator, but it is also responsible for creating the services it provides. This couples the context to the construction logic of its dependencies, making it less modular and harder to test.
- **Unclear Code Scope:** A top-level `scripts/` directory contains various scripts whose purpose and relationship to the main `tools` application are unclear. They may be legacy or one-off utilities.

## 3. Incremental Refactoring Breakdown

The refactoring is broken down into the following incremental steps.

### Step 1: Unify Configuration

**Subtasks:**

- Identify all modules that import from `tools.settings`.
- Replace those imports with configuration `app_config`, which is made available to functions by click commands, which get from `AppContext` (e.g., `ctx.obj.config`).
- Delete the `tools/settings.py` file.
- **Reasoning:** This will create a single source of truth for all configuration, eliminating redundancy and making the application easier to configure and understand.
- **Dependencies:** None.
- **Complexity:** Small.

### Step 2: Decouple Services from `AppContext`

**Subtasks:**

- Introduce factory functions or a simple dependency injection (DI) container responsible for creating services (e.g., `LocalDBRepository`).
- Modify `AppContext` to accept already-instantiated services in its constructor.
- Update the application's entry point (`tools/cli.py`) to use the new factories to build services and pass them to the `AppContext`.
- **Reasoning:** This will decouple `AppContext` from the responsibility of creating services, adhering to the Single Responsibility Principle. It will make the application more modular and significantly easier to test, as mock services can be injected during tests.
- **Dependencies:** Step 1 is recommended but not strictly required.
- **Complexity:** Medium.

### Step 3: Analyze and Refactor Command Logic

**Subtasks:**

- Review the command logic in `tools/commands/playlist/`, `tools/commands/discogs/`, and `tools/commands/db/`.
- Identify common patterns and duplicated code (e.g., data fetching, API interaction).
- Extract this shared logic into new, reusable services within the `tools/services/` directory.
- **Reasoning:** Centralizing shared logic reduces code duplication, improves maintainability, and clarifies the responsibilities of each module. Commands will become simpler orchestrators that delegate work to services.
- **Dependencies:** Step 2. Having a clear service pattern will make this step much cleaner.
- **Complexity:** Medium.

### Step 4: Clarify and Integrate `scripts/` Directory

**Subtasks:**

- Analyze each script in the `scripts/` directory to determine its purpose.
- For scripts that are still useful, refactor them into proper `click` commands within the main `tools` application.
- For scripts that are obsolete or one-offs, document their purpose (if necessary) and then remove them.
- **Reasoning:** This will reduce codebase clutter, eliminate ambiguity, and ensure that all relevant functionality is integrated into and managed by the main application.
- **Dependencies:** None.
- **Complexity:** Small.

## 4. Integration and Verification

Each step should be performed on a separate branch. After each step, the following verification should be performed:

- **Run Quality Assurance:** Execute `task qa` to ensure that all linting and type checks pass.
- **Run Tests:** Execute `task test` to ensure that all existing tests pass and that coverage does not decrease.
- **Add Tests:** Where new services are created or logic is significantly refactored, new unit tests should be added to validate the changes.

## 5. Potential Blockers

- The primary blocker is a lack of complete understanding of the business logic within the commands and scripts. The analysis steps (Step 3 and Step 4) are designed to mitigate this by explicitly dedicating time to investigation before making changes.
- Existing tests may be insufficient to cover all refactoring changes, requiring additional test-writing efforts.
