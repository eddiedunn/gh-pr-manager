#!/usr/bin/env python3
# Save as test_github_client.py and run with: PYTHONPATH=src python test_github_client.py

from gh_pr_manager import github_client

print("Testing GitHub client...")

# Test authentication
auth_status = github_client.check_auth_status()
print(f"✓ Authenticated: {auth_status}")

if auth_status:
    # Test getting user login
    login = github_client.get_user_login()
    print(f"✓ User login: {login}")
    
    # Test getting organizations
    orgs = github_client.get_user_orgs()
    print(f"✓ Organizations: {orgs}")
    
    # Test getting repos for the user
    if login:
        repos = github_client.get_repos(login)
        print(f"✓ User repos: {len(repos)} found")
        if repos:
            print(f"  First few: {repos[:3]}")
else:
    print("❌ Not authenticated. Please run: gh auth login")