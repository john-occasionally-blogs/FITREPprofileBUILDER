# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains "Vibe MD Templates" - a comprehensive collection of interconnected Markdown templates designed to streamline AI-assisted software development workflows. The templates provide structured documentation frameworks that help both developers and AI assistants understand project requirements, architecture, and implementation strategies.

## Template Architecture

The project uses a sophisticated context-driven architecture with the following core files:

- **`claude.md`** - Master context blueprint with conflict resolution rules (template)
- **`prd.md`** - Product Requirements Document template for features and goals
- **`infra.md`** - Infrastructure and technical foundation template
- **`workflow.md`** - Development workflow and execution process template
- **`security.md`** - Security requirements and best practices template
- **`sbom.md`** - Software Bill of Materials template for dependencies
- **`tests.md`** - Testing strategy and frameworks template
- **`changelog.md`** - Version history and change tracking template
- **`Init.md`** - Interactive setup guide for populating templates

## Context File Priority System

When working with these templates, follow the conflict resolution matrix defined in `claude.md`:

1. **Priority 1** - Safety & Supply Chain: `security.md` and `sbom.md` (Override all other documents)
2. **Priority 2** - Runtime Environment: `infra.md` (Override incompatible feature requests)
3. **Priority 3** - Global Conventions: `claude.md` (Baseline project rules)
4. **Priority 4** - Feature Requirements: `prd.md` (May refine but not violate higher constraints)
5. **Priority 5** - Process & Workflow: `workflow.md` (Governs plan creation and execution)

## Working with Templates

### Setup and Customization
1. The templates contain placeholders in brackets like `[e.g., "Example content"]`
2. Use the `Init.md` interactive guide to populate templates systematically
3. Each template includes guided questions and example content
4. Templates are technology-agnostic and work with any programming language/framework

### Development Workflow
When implementing features using these templates:
1. Always consult `workflow.md` for the step-by-step process
2. Create `.implementation/plan.json` for systematic development
3. Follow the self-optimization routine after every action
4. Use Conventional Commits format for commit messages
5. Update `changelog.md` after feature completion

### Template Validation
Before using templates in a project:
- Ensure all bracketed placeholders are replaced with actual values
- Verify conflict resolution rules are properly configured
- Confirm technology stack is defined in `infra.md` and `sbom.md`
- Validate security requirements are addressed in `security.md`

## Key Features

- **Security-First Approach**: Built-in security considerations and dependency management
- **Conflict Resolution System**: Sophisticated priority system for consistent AI decision-making  
- **Technology Agnostic**: Works with local applications, web apps, mobile apps, and backend services
- **Self-Optimizing**: Templates include routines for continuous improvement
- **Autonomous Development**: Designed to enable AI assistants to work independently

## Template Structure

Each template serves a specific role:
- Core templates (Required): `claude.md`, `prd.md`, `infra.md`, `workflow.md`
- Supporting templates (Recommended): `security.md`, `sbom.md`, `tests.md`, `changelog.md`
- Utility files: `Init.md` for interactive setup, `README.md` for overview

## Usage Notes

- Templates are designed for student and indie developer projects
- Focus on enabling autonomous AI development workflows
- Emphasize consistent project setup and documentation standards
- Support both local and cloud-based application development
- Include comprehensive examples and best practice recommendations