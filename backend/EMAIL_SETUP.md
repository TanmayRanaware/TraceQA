# Email Setup for TraceQA

This document explains how to set up email functionality for sending test cases to Business Analysts.

## Overview

The email functionality allows users to send generated test cases directly to a Business Analyst via email with an Excel attachment. The system uses Gmail API for sending emails.

## Environment Variables

Add the following environment variables to your `.env` file:

```bash
BA_EMAIL=bhanagearshan@gmail.com
ADMIN_EMAIL=traceqaadmin@gmail.com
```

## Gmail API Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API for your project

### 2. Create OAuth 2.0 Credentials

1. Go to "Credentials" in the Google Cloud Console
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Desktop application" as the application type
4. Download the credentials JSON file
5. Rename it to `credentials.json` and place it in the backend directory

### 3. First-time Authentication

When you first run the application, it will:
1. Open a browser window for OAuth authentication
2. Ask you to sign in to your Google account
3. Request permission to send emails on your behalf
4. Save the authentication token to `token.json`

## Usage

1. Generate test cases in the Test Generation tab
2. Click the "Send to BA" button that appears after test generation
3. The system will:
   - Generate an Excel file with the test cases
   - Send an email to the BA with the Excel file attached
   - Show success/error messages in the UI

## Email Content

- **To**: BA_EMAIL from environment variables
- **From**: ADMIN_EMAIL from environment variables
- **Subject**: "Please verify the Test Cases generated"
- **Body**: Includes journey name, test count, and generation timestamp
- **Attachment**: Excel file with structured test cases

## Fallback Mode

If Gmail API credentials are not configured, the system will fall back to logging mode where email details are logged to the console instead of actually sending emails.

## Security Notes

- Keep your `credentials.json` and `token.json` files secure
- Never commit these files to version control
- The `token.json` file contains refresh tokens and should be treated as sensitive

## Troubleshooting

### Common Issues

1. **"Gmail API not authenticated"**: Check that `credentials.json` exists and is properly formatted
2. **"Insufficient permissions"**: Ensure the Gmail API is enabled and OAuth scopes are correct
3. **"Token expired"**: Delete `token.json` and re-authenticate

### Debug Mode

Check the backend logs for detailed error messages about email sending failures.
