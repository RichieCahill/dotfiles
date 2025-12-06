#!/usr/bin/env python3
"""
Script to detect "evaluation warning:" in logs and suggest fixes using GitHub Models.
"""
import os
import sys
import re
import requests
import json
from pathlib import Path

# Configuration
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
PR_NUMBER = os.environ.get("PR_NUMBER") # If triggered by PR
RUN_ID = os.environ.get("RUN_ID")

# GitHub Models API Endpoint (OpenAI compatible)
# https://github.com/marketplace/models
API_BASE = "https://models.inference.ai.azure.com"
# Default to gpt-4o, but allow override via env var
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o")

def get_log_content(run_id):
    """Fetches the logs for a specific workflow run."""
    print(f"Fetching logs for run ID: {run_id}")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # List artifacts to find logs (or use jobs API)
    # For simplicity, we might need to use 'gh' cli in the workflow to download logs
    # But let's try to read from a file if passed as argument, which is easier for the workflow
    return None

def parse_warnings(log_file_path):
    """Parses the log file for evaluation warnings."""
    warnings = []
    with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if "evaluation warning:" in line:
                warnings.append(line.strip())
    return warnings

def generate_fix(warning_msg):
    """Calls GitHub Models to generate a fix for the warning."""
    print(f"Generating fix for: {warning_msg}")
    
    prompt = f"""
    I encountered the following Nix evaluation warning:
    
    `{warning_msg}`
    
    Please explain what this warning means and suggest how to fix it in the Nix code. 
    If possible, provide the exact code change in a diff format or a clear description of what to change.
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }

    payload = {
        "messages": [
            {
                "role": "system",
                "content": "You are an expert NixOS and Nix language developer."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": MODEL_NAME,
        "temperature": 0.1
    }

    try:
        response = requests.post(
            f"{API_BASE}/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: fix_eval_warnings.py <log_file>")
        sys.exit(1)

    log_file = sys.argv[1]
    if not os.path.exists(log_file):
        print(f"Log file not found: {log_file}")
        sys.exit(1)

    warnings = parse_warnings(log_file)
    if not warnings:
        print("No evaluation warnings found.")
        sys.exit(0)

    print(f"Found {len(warnings)} warnings.")
    
    # Process unique warnings to save tokens
    unique_warnings = list(set(warnings))
    
    fixes = []
    for warning in unique_warnings:
        fix = generate_fix(warning)
        if fix:
            fixes.append(f"## Warning\n`{warning}`\n\n## Suggested Fix\n{fix}\n")

    # Output fixes to a markdown file for the PR body
    with open("fix_suggestions.md", "w") as f:
        f.write("# Automated Fix Suggestions\n\n")
        f.write("\n---\n".join(fixes))

    print("Fix suggestions written to fix_suggestions.md")

if __name__ == "__main__":
    main()
