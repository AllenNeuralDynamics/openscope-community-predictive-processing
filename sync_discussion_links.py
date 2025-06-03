#!/usr/bin/env python3
"""
GitHub Action script to automatically sync discussion links in markdown files.

This script:
1. Fetches all discussions from the GitHub repository
2. Scans all markdown files in the docs/ directory
3. Finds matching discussions based on page identifiers
4. Adds or updates discussion links directly in the markdown files
5. Creates a commit with the updated links

Usage:
    python sync_discussion_links.py [--dry-run] [--github-token TOKEN]
"""

import os
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests


class DiscussionLinkSyncer:
    def __init__(self, github_token: Optional[str] = None, dry_run: bool = False):
        self.github_token = github_token or os.environ.get('GITHUB_TOKEN')
        self.dry_run = dry_run
        self.repo_owner = "allenneuraldynamics"
        self.repo_name = "openscope-community-predictive-processing"
        self.docs_dir = Path("docs")
        
        # Discussion link pattern to find existing links
        self.discussion_link_pattern = re.compile(
            r'<!-- DISCUSSION_LINK_START -->.*?<!-- DISCUSSION_LINK_END -->',
            re.DOTALL
        )
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests."""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'discussion-link-syncer'
        }
        if self.github_token:
            headers['Authorization'] = f'Bearer {self.github_token}'
        return headers
    
    def fetch_discussions(self) -> List[Dict]:
        """Fetch all discussions from the repository using GraphQL API."""
        if not self.github_token:
            print("⚠️  Warning: No GitHub token provided. API rate limits may apply.")
        
        query = """
        query($owner: String!, $repo: String!, $cursor: String) {
          repository(owner: $owner, name: $repo) {
            discussions(first: 100, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
              pageInfo {
                hasNextPage
                endCursor
              }
              nodes {
                title
                number
                url
                updatedAt
                category {
                  name
                }
                author {
                  login
                }
              }
            }
          }
        }
        """
        
        all_discussions = []
        cursor = None
        
        while True:
            variables = {
                "owner": self.repo_owner,
                "repo": self.repo_name,
                "cursor": cursor
            }
            
            response = requests.post(
                'https://api.github.com/graphql',
                headers=self.get_headers(),
                json={"query": query, "variables": variables}
            )
            
            if response.status_code != 200:
                print(f"❌ GraphQL API request failed: {response.status_code}")
                print(f"Response: {response.text}")
                return []
            
            data = response.json()
            if 'errors' in data:
                print(f"❌ GraphQL errors: {data['errors']}")
                return []
            
            discussions = data['data']['repository']['discussions']['nodes']
            all_discussions.extend(discussions)
            
            page_info = data['data']['repository']['discussions']['pageInfo']
            if not page_info['hasNextPage']:
                break
            cursor = page_info['endCursor']
        
        print(f"📝 Fetched {len(all_discussions)} discussions")
        return all_discussions
    
    def extract_page_identifier(self, file_path: Path) -> str:
        """Extract page identifier from markdown file path."""
        # Convert file path to page identifier
        # Remove docs/ prefix and .md suffix
        relative_path = file_path.relative_to(self.docs_dir)
        page_path = str(relative_path).replace('.md', '')
        
        # Special handling for different page types
        if page_path == 'index':
            return 'index'
        elif '/' in page_path:
            # For nested pages like meetings/2025-05-13, use full path
            return page_path
        else:
            # For top-level pages, use just the filename
            return page_path
    
    def find_matching_discussion(self, page_identifier: str, discussions: List[Dict]) -> Optional[Dict]:
        """Find a discussion that matches the page identifier."""
        target_title = f"Discussion: {page_identifier}"
        
        # Look for exact match first
        for discussion in discussions:
            if discussion['title'].lower() == target_title.lower():
                return discussion
        
        # Look for partial matches (fallback)
        for discussion in discussions:
            if page_identifier.lower() in discussion['title'].lower():
                return discussion
        
        return None
    
    def create_discussion_link_html(self, discussion: Optional[Dict], page_identifier: str) -> str:
        """Create the HTML for the discussion link."""
        if discussion:
            return f"""<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="{discussion['url']}" target="_blank">
            💬 Join the discussion for this page on GitHub
        </a>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->"""
        else:
            # No discussion found - create link to start new one
            discussion_title = f"Discussion: {page_identifier}"
            encoded_title = requests.utils.quote(discussion_title)
            return f"""<!-- DISCUSSION_LINK_START -->
<div class="discussion-link">
    <hr>
    <p>
        <a href="https://github.com/{self.repo_owner}/{self.repo_name}/discussions/new?category=q-a&title={encoded_title}" target="_blank">
            💬 Start a discussion for this page on GitHub
        </a>
        <span class="note">(A GitHub account is required to create or participate in discussions)</span>
    </p>
</div>
<!-- DISCUSSION_LINK_END -->"""
    
    def update_markdown_file(self, file_path: Path, discussion: Optional[Dict], page_identifier: str) -> bool:
        """Update a markdown file with the discussion link at the bottom."""
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # Create the new discussion link HTML
            new_link_html = self.create_discussion_link_html(discussion, page_identifier)
            
            # Check if there's already a discussion link
            if self.discussion_link_pattern.search(content):
                # Replace existing link
                content = self.discussion_link_pattern.sub(new_link_html, content)
                action = "Updated"
            else:
                # Add new link at the very bottom of the file
                content = content.rstrip() + '\n\n' + new_link_html + '\n'
                action = "Added"
            
            # Only write if content changed
            if content != original_content:
                if not self.dry_run:
                    file_path.write_text(content, encoding='utf-8')
                
                discussion_info = f"Discussion #{discussion['number']}" if discussion else "New discussion link"
                print(f"✅ {action} discussion link at bottom of {file_path}: {discussion_info}")
                return True
            else:
                print(f"⚪ No changes needed for {file_path}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating {file_path}: {e}")
            return False
    
    def find_markdown_files(self) -> List[Path]:
        """Find all markdown files in the docs directory."""
        markdown_files = []
        for md_file in self.docs_dir.rglob("*.md"):
            # Skip template files and other non-content files
            if 'template' not in str(md_file).lower():
                markdown_files.append(md_file)
        return sorted(markdown_files)
    
    def sync_all_links(self) -> Tuple[int, int]:
        """Sync discussion links for all markdown files."""
        print(f"🔍 Scanning for markdown files in {self.docs_dir}...")
        
        # Fetch discussions from GitHub
        discussions = self.fetch_discussions()
        if not discussions:
            print("❌ Failed to fetch discussions. Aborting.")
            return 0, 0
        
        # Find all markdown files
        markdown_files = self.find_markdown_files()
        print(f"📄 Found {len(markdown_files)} markdown files")
        
        # Process each file
        updated_count = 0
        total_count = len(markdown_files)
        
        for md_file in markdown_files:
            page_identifier = self.extract_page_identifier(md_file)
            discussion = self.find_matching_discussion(page_identifier, discussions)
            
            if self.update_markdown_file(md_file, discussion, page_identifier):
                updated_count += 1
        
        return updated_count, total_count
    
    def run(self):
        """Run the discussion link sync process."""
        print("🚀 Starting discussion link sync...")
        print(f"Repository: {self.repo_owner}/{self.repo_name}")
        print(f"Docs directory: {self.docs_dir}")
        print(f"Dry run: {self.dry_run}")
        print()
        
        updated_count, total_count = self.sync_all_links()
        
        print()
        print("📊 Summary:")
        print(f"   Total files processed: {total_count}")
        print(f"   Files updated: {updated_count}")
        print(f"   Files unchanged: {total_count - updated_count}")
        
        if self.dry_run:
            print("\n⚠️  This was a dry run. No files were actually modified.")
        elif updated_count > 0:
            print(f"\n✅ Successfully updated {updated_count} files with discussion links!")
        else:
            print("\n⚪ No files needed updates.")


def main():
    parser = argparse.ArgumentParser(description='Sync GitHub discussion links in markdown files')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--github-token', help='GitHub API token (can also use GITHUB_TOKEN env var)')
    
    args = parser.parse_args()
    
    syncer = DiscussionLinkSyncer(
        github_token=args.github_token,
        dry_run=args.dry_run
    )
    syncer.run()


if __name__ == '__main__':
    main()
