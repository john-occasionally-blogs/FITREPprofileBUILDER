# Infrastructure Blueprint

Purpose: This file describes the project's technical foundation, including the method of hosting, the programming languages, the coding standards, and how to run the code.

> Use this file to tell your AI assistant about the environment where your application will be built and run. Fill out each section as best you can. Simple, plain English is perfect!

---

## What We're Building

> Think of this like a quick intro for a new team member. What is the app made of?

* **Programming Language:** Python (backend services), JavaScript/TypeScript (frontend)
* **Main Framework/Tool:** FastAPI (backend), React (frontend), Docker (containerization)
* **A Quick Summary:** A containerized web application that processes Marine Corps FITREP PDFs to calculate fitness report averages and predict the impact of new reports on officer profiles.

---

## How to Run it on Your Computer 

> These are the instructions for getting the app started on a local machine. It helps the AI create setup scripts and give you the right commands.

* **Installation Command:** `docker-compose up --build`
* **Startup Command:** `docker-compose up` (after initial build)
* **Local Address:** `http://localhost:3000` (frontend), `http://localhost:8000` (backend API)
* **Prerequisites:** Docker Desktop for Mac must be installed and running

---

## Project Architecture & Conventions

> This section outlines the file structure and architectural patterns based on the chosen framework.

* **Architecture:** Microservices architecture with containerized components
* **Directory Structure:**
    * **`/frontend`** - React application with TypeScript
        * `/src/components` - Reusable UI components
        * `/src/pages` - Main application screens (4 screens as per PRD)
        * `/src/services` - API client services
        * `/src/utils` - FITREP scoring utilities
    * **`/backend`** - FastAPI Python service
        * `/app/api` - API route handlers
        * `/app/services` - Business logic (PDF processing, scoring calculations)
        * `/app/models` - Database models and schemas
        * `/app/utils` - Utility functions
    * **`/pdf-processor`** - Dedicated PDF processing service
        * OCR and data extraction from FITREP PDFs
        * NAVMC 10835B form field recognition
    * **`/database`** - PostgreSQL database with persistent volume

---

## Code Generation Style Guide

When writing or modifying code, I will adhere to the following standards:

* **Python (Backend):**
    * **Variable/Function Naming:** `snake_case`
    * **Class Naming:** `PascalCase`
    * **Constants:** `UPPER_SNAKE_CASE`
    * **Linting:** `black`, `flake8`, `mypy` for type checking
* **TypeScript/JavaScript (Frontend):**
    * **Variable/Function Naming:** `camelCase`
    * **Component Naming:** `PascalCase`
    * **File Naming:** `PascalCase` for components, `kebab-case` for utilities
    * **Linting:** ESLint with TypeScript support
* **Docker:** Service names use `kebab-case`

---

## Where it Lives on the Internet & Who its Friends Are

> Will this app be online? Does it talk to other services? This helps the AI understand the app's neighborhood.

* **Hosting Provider:** Local development environment (Docker on Mac)
* **Deployment:** Self-contained containerized application stack
* **External Services:** None required - fully offline capable for security
* **Network:** All services communicate via Docker internal network
* **Security Note:** Application runs entirely locally to protect sensitive FITREP data

---

## Where Your Data is Stored

> This is one of the most important parts! How does your app remember things? This prevents the AI from trying to save files or data in the wrong place.

* **Data Storage Method:** PostgreSQL database running in Docker container with persistent volume
* **Important Notes:** 
    * All FITREP data remains local - never transmitted externally
    * PDF files are processed and deleted - only extracted data is stored
    * Database includes full audit trail for all scoring calculations
* **Schema Details:**
    * **`officers`** - Officer profiles and basic information
    * **`fitreports`** - Individual FITREP records with extracted data
    * **`trait_scores`** - The 14 trait scores (A-H) for each FITREP
    * **`relative_values`** - Calculated RV scores with historical tracking
    * **`profiles`** - Aggregated profile data by rank for quick analysis
    * **`scoring_sessions`** - Track "what-if" scenarios for impact prediction