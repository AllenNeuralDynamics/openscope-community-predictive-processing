# Serving and Testing the Website Locally

This guide explains how to set up and serve the OpenScope Community Predictive Processing website locally to test your content before submitting changes.

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python** (version 3.6 or higher)
2. **pip** (Python package manager)
3. **Git** (version control system)

## Setting Up Your Environment

Follow these steps to set up your local environment for testing the website:

### 1. Clone the Repository (if you haven't already)

```bash
git clone https://github.com/allenneuraldynamics/openscope-community-predictive-processing.git
cd openscope-community-predictive-processing
```

### 2. Create a Virtual Environment (Recommended)

Creating a virtual environment helps isolate the dependencies for this project:

```bash
# For macOS/Linux
python -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Required Dependencies

Install MkDocs and all the required dependencies:

```bash
pip install -r requirements.txt
```

## Serving the Website Locally

### Starting the Local Server

Once you have set up your environment, you can serve the website locally:

```bash
mkdocs serve
```

This command starts a local server and automatically rebuilds the site when you make changes to the documentation.

### Accessing the Local Website

Open your web browser and navigate to:

```
http://127.0.0.1:8000
```

The website should be visible and fully functional, allowing you to test your changes in real-time.

## Testing Your Content

When making changes to the documentation, follow these practices for testing:

### 1. Check Navigation

Verify that any new pages you've added appear correctly in the navigation menu. If they don't appear, ensure they are properly listed in the `mkdocs.yml` file under the `nav` section.

### 2. Test Links

Check that all internal and external links work correctly. For internal links, use relative paths like:

```markdown
[Link to another page](another-page.md)
[Link to a section in another folder](folder/page.md#section)
```

### 3. Verify Images

If you've added images, ensure they display correctly. Images should be placed in the `docs/img/` directory or an appropriate subfolder, and referenced using relative paths:

```markdown
![Image description](img/subfolder/image.png)
```

### 4. Check Formatting

Test that Markdown formatting appears as expected, especially for:
- Code blocks
- Tables
- Admonitions (note, warning, etc.)
- Nested lists

### 5. Mobile View

Use your browser's developer tools to test how the site appears on mobile devices by toggling the device view.

## Common Issues and Solutions

### Site Navigation Not Updating

If your changes to the navigation structure in `mkdocs.yml` don't appear:

1. Stop the server (`Ctrl+C`)
2. Start it again with `mkdocs serve`

### Syntax Errors in YAML

If the server fails to start due to errors in `mkdocs.yml`:

1. Check the error message for the line number with the issue
2. Verify proper indentation and formatting in that section
3. Ensure all strings that contain special characters are properly quoted

### Page Not Found Errors

If you encounter 404 errors:

1. Check that the file exists in the specified location
2. Ensure the file is correctly listed in the `mkdocs.yml` navigation
3. Verify that the file has a `.md` extension in the file system

## Building the Site

To build a static version of the site (useful for verifying the final result):

```bash
mkdocs build
```

This creates a `site` directory containing the built website. You can open `site/index.html` in your browser to view it.

## Website Structure and Deployment Process

### Website Structure

The OpenScope Community Predictive Processing website is built with [MkDocs](https://www.mkdocs.org/), a static site generator that's specifically designed for project documentation:

1. **Main Configuration**: The `mkdocs.yml` file in the root directory controls:
   - Site navigation structure
   - Theme configuration (we use ReadTheDocs theme)
   - Plugins and extensions
   - Custom CSS and JavaScript

2. **Content Organization**: 
   - All documentation content is stored in the `docs/` directory
   - Markdown (`.md`) files contain the actual content
   - Images and other assets are stored in `docs/img/`
   - JavaScript files for extended functionality are in `docs/js/`

3. **Templates and Standardization**:
   - The `docs/template-files/` directory contains templates for new experiments and meetings
   - Use these templates to maintain consistency across the project documentation
   - Templates follow standardized formats for easier data extraction and processing

### GitHub Actions for Automatic Deployment

The website is automatically built and deployed using GitHub Actions whenever changes are merged to the main branch:

1. **Workflow Configuration**: The GitHub Actions workflow is defined in `.github/workflows/` directory
   - It specifies when builds should trigger (typically on push to main)
   - Sets up the Python environment
   - Installs dependencies
   - Builds and deploys the site

2. **Custom Python Scripts**:
   - `update_mkdocs.py` in the root directory is executed during the GitHub Actions workflow
   - This script performs additional processing before the site is built:
     - Updates navigation structure
     - Verifies file integrity
     - Cross-references content
     - Generates additional dynamic content if needed

### Contribution Workflow

When contributing to the documentation, follow this workflow:

1. **Create a Feature Branch**:
   ```bash
   git checkout -b docs/your-feature-name
   ```

2. **Make Your Changes**:
   - Add or modify content in the `docs/` directory
   - Test locally using `mkdocs serve`
   - Ensure all links work and content displays correctly

3. **Commit and Push**:
   ```bash
   git add .
   git commit -m "Descriptive message about your changes"
   git push -u origin docs/your-feature-name
   ```

4. **Submit a Pull Request**:
   - Go to the GitHub repository page
   - Create a new Pull Request from your branch to main
   - Provide a detailed description of your changes
   - Request reviews from relevant team members

5. **Review Process**:
   - Pull requests require approval before they can be merged
   - Reviewers may suggest changes or improvements
   - Address any feedback by making additional commits to your branch

6. **Merge and Deploy**:
   - Once approved, your changes will be merged into main
   - GitHub Actions will automatically build and deploy the updated site
   - Your changes will be visible on the live site shortly after merging

### Best Practices

1. **Make Focused Changes**: Each branch should address a specific feature or fix
2. **Keep Changes Small**: Smaller PRs are easier to review and less prone to conflicts
3. **Update Navigation**: If adding new pages, ensure they're properly added to the `nav` section in `mkdocs.yml`
4. **Test Thoroughly**: Always test your changes locally before submitting a PR
5. **Document Your Changes**: Provide clear descriptions of what you've changed and why

## Additional Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Markdown Guide](https://www.markdownguide.org/basic-syntax/)
- [ReadTheDocs Theme](https://mkdocs.readthedocs.io/) (used by this project)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Flow](https://docs.github.com/en/get-started/quickstart/github-flow) (branching workflow)
