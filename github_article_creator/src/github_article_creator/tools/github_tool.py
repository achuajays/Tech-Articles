from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import requests
import base64
import os
from pathlib import Path
from typing import Type

class GithubUploadInput(BaseModel):
    """Input schema for GithubMarkdownUploader tool."""
    file_folder: str = Field(..., description="a good name for the folder . remember dont use the folder name that already used")

class GithubMarkdownUploader(BaseTool):
    name: str = "Github Markdown Uploader"
    description: str = """Uploads a markdown file to a GitHub repository. Use this tool when you need to add or update markdown documentation in a GitHub repository. The tool handles both new file creation and updates to existing files."""

    args_schema: Type[BaseModel] = GithubUploadInput

    def _run(self, file_folder: str) -> str:
        # Read the markdown file
        file_path =  "Readme.md"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return f"Error: File {file_path} not found"
        except Exception as e:
            return f"Error reading file: {str(e)}"

        # Encode content to base64
        content_encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')

        owner = os.getenv("GITHUB_OWNER")
        repo = os.getenv("GITHUB_REPO")
        token = os.getenv("GITHUB_TOKEN")
        github_path = f"docs/{file_folder}/{file_path}"
        commit_message = "file update"
        # Set up API URL and headers
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{github_path}"
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }

        # Check if file already exists (to get SHA for updates)
        response = requests.get(url, headers=headers)
        sha = None
        if response.status_code == 200:
            sha = response.json().get('sha')

        # Prepare commit message
        if not commit_message:
            filename = Path(file_path).name
            action = "Update" if sha else "Add"
            commit_message = f"{action} {filename}"

        # Prepare payload
        payload = {
            'message': commit_message,
            'content': content_encoded
        }

        # Add SHA for updates
        if sha:
            payload['sha'] = sha

        # Upload file
        response = requests.put(url, json=payload, headers=headers)

        if response.status_code in [200, 201]:
            return f"Success: File uploaded to {github_path}. View at: {response.json()['content']['html_url']}"
        else:
            return f"Failed to upload file. Error: {response.status_code} - {response.json().get('message', 'No error message')}"
