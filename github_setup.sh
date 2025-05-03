#!/bin/bash

# GitHub repository setup script
# This script initializes a Git repository and pushes it to GitHub

# Check if the GitHub token is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <github_token> <repo_name>"
    echo "Example: $0 ghp_abcdef123456 username/repo-name"
    exit 1
fi

GITHUB_TOKEN=$1
REPO_NAME=$2

# Extract the username and repository name
IFS='/' read -r USERNAME REPO <<< "$REPO_NAME"

if [ -z "$USERNAME" ] || [ -z "$REPO" ]; then
    echo "Error: Repository name should be in the format 'username/repo-name'"
    exit 1
fi

echo "Setting up Git repository..."

# Initialize Git repository if not already initialized
if [ ! -d .git ]; then
    git init
    echo "Git repository initialized."
else
    echo "Git repository already exists."
fi

# Configure Git with token
git config --global user.name "$USERNAME"
git config --global user.email "$USERNAME@users.noreply.github.com"

# Add all files to Git
git add .

# Commit changes
git commit -m "Initial commit"

# Add the remote repository URL with the token
REMOTE_URL="https://$GITHUB_TOKEN@github.com/$REPO_NAME.git"
git remote add origin "$REMOTE_URL" 2>/dev/null || git remote set-url origin "$REMOTE_URL"

# Push to GitHub
echo "Pushing to GitHub repository: $REPO_NAME"
git push -u origin master || git push -u origin main

echo "Repository successfully pushed to GitHub at: https://github.com/$REPO_NAME"