# Automated Code Review using the ChatGPT language model

## Import statements
import argparse
import openai
import os
import requests
from github import Github

## Adding command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--openai_api_key', help='Your OpenAI API Key')
parser.add_argument('--github_token', help='Your Github Token')
parser.add_argument('--github_pr_id', help='Your Github PR ID')
parser.add_argument('--openai_engine', default="gpt-3.5-turbo", help='GPT model to use.')
parser.add_argument('--openai_temperature', default=0.5, help='Sampling temperature to use. Higher values means the model will take more risks. Recommended: 0.5')
parser.add_argument('--openai_max_tokens', default=2048, help='The maximum number of tokens to generate in the completion.')
parser.add_argument('--file_filter', default="", help='filter file to review')
args = parser.parse_args()

## Authenticating with the OpenAI API
openai.api_key = args.openai_api_key

## Authenticating with the Github API
g = Github(args.github_token)


def summary():
    repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
    pull_request = repo.get_pull(int(args.github_pr_id))

    content = get_content_patch()
    
    if len(content) == 0:
        pull_request.create_issue_comment(f"Patch file does not contain any changes")
        return

    response = openai.ChatCompletion.create(
        model=args.openai_engine,
        messages=[
            {"role": "system", "content": "You are a helpful code reviewer. \
                You will provide me summary that consists of \
                one short and clear paragraph or sentences of the general idea, \
                followed by short but more detailed explanation in list points."},
            {"role": "user", "content": "Please summarize this code patch below: \n" + content}],
        temperature=float(args.openai_temperature),
        max_tokens=int(args.openai_max_tokens)
    )
    print(response)

    for choice in response['choices']:
        print(choice['message']['content'])
        pull_request.create_issue_comment(f"{choice['message']['content']}")

            
def review():
    repo = g.get_repo(os.getenv('GITHUB_REPOSITORY'))
    pull_request = repo.get_pull(int(args.github_pr_id))

    content = get_content_patch()
    
    if len(content) == 0:
        pull_request.create_issue_comment(f"Patch file does not contain any changes")
        return

    response = openai.ChatCompletion.create(
        model=args.openai_engine,
        messages=[
            {"role": "system", "content": "You are a helpful code reviewer. \
                You will provide me with a list of feedback that consist of \
                possible bug, possible performance issue, \
                performance improvement, best practice suggestion, etc. \
                For each feedback, provide code snippet of what changed, if any."},
            {"role": "user", "content": "Please review this code patch below: \n" + content}],
        temperature=float(args.openai_temperature),
        max_tokens=int(args.openai_max_tokens)
    )
    print(response)

    for choice in response['choices']:
        print(choice['message']['content'])
        pull_request.create_issue_comment(f"{choice['message']['content']}")

             
def get_content_patch():
    url = f"https://api.github.com/repos/{os.getenv('GITHUB_REPOSITORY')}/pulls/{args.github_pr_id}"
    print(url)

    headers = {
        'Authorization': f"token {args.github_token}",
        'Accept': 'application/vnd.github.v3.diff'
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        raise Exception(response.text)

    if args.file_filter:
        diff_lines = response.text.split('\n')
        filtered_diff_lines = []

        for line in diff_lines:
            # Look for diff header lines
            if line.startswith('diff --git'):
                # Check if the file has the specified extension
                if line.endswith(args.file_filter):
                    include_file = True
                else:
                    include_file = False

            if include_file:
                filtered_diff_lines.append(line)

        return '\n'.join(filtered_diff_lines)

    return response.text

summary()

review()
