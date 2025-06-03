# GitHub Actions Automation

This project uses several GitHub Actions workflows to automatically maintain and update various markdown files. These automations ensure the documentation stays current without manual intervention.

## Active Workflows

### 1. Sync Discussion Links (`.github/workflows/sync-discussion-links.yml`)

**Purpose**: Automatically adds discussion links to documentation pages

**Triggers**:

- When discussions are created, edited, or deleted
- When markdown files in `docs/` are updated
- Manual trigger from GitHub Actions interface
- Weekly schedule (Mondays at 6 AM UTC)

**What it does**:

- Scans all markdown files in the `docs/` directory
- Matches pages to GitHub discussions using title patterns
- Adds styled discussion links at the top of matching pages
- Commits changes with detailed commit messages

**Files modified**: All `.md` files in `docs/` that have matching discussions

---

### 2. Deploy MkDocs to GitHub Pages (`.github/workflows/gh-pages.yml`)

**Purpose**: Builds and deploys the website to GitHub Pages

**Triggers**:

- When code is pushed to the main branch
- After the "Sync Discussion Links" workflow completes successfully

**What it does**:

- Sets up Python environment
- Installs dependencies from `requirements.txt`
- Runs `update_mkdocs.py` to update navigation
- Builds the MkDocs site
- Deploys to GitHub Pages using `mkdocs gh-deploy`

**Output**: Live website at [allenneuraldynamics.github.io/openscope-community-predictive-processing](https://allenneuraldynamics.github.io/openscope-community-predictive-processing/)

---

## Automation Scripts

### `sync_discussion_links.py`

**Purpose**: Core script for discussion link automation

**Key features**:

- Uses GitHub GraphQL API for reliable data fetching
- Extracts page identifiers from file paths
- Matches discussions using exact title patterns
- Handles edge cases and provides detailed logging
- Only modifies files when necessary

**Authentication**: Uses `GITHUB_TOKEN` environment variable


---

### `update_mkdocs.py`

**Purpose**: Dynamically updates the MkDocs navigation structure

**What it does**:

- Scans the `docs/` directory structure
- Automatically adds new files to the navigation
- Maintains consistent organization
- Handles special cases like meeting dates and experiment files

**Benefits**: New documentation pages appear in navigation without manual updates

---

## Monitoring and Maintenance

### Viewing Workflow Runs

1. Go to the **Actions** tab in the GitHub repository
2. Select a workflow to see recent runs
3. Click on individual runs for detailed logs
4. Check for errors or warnings in the output

### Manual Triggering

Both workflows can be manually triggered:

1. Navigate to **Actions** tab
2. Select the desired workflow
3. Click **"Run workflow"** button
4. Choose the branch (usually `main`)
5. Click **"Run workflow"** to start
