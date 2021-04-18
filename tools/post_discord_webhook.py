import asyncio
import datetime
import os
import subprocess
import typing

import aiohttp

from randovania import VERSION


async def post_to_discord():
    git_result = subprocess.run(["git", "show"], check=True, stdout=subprocess.PIPE, text=True).stdout.split("\n")
    commit_hash = git_result[0].split()[1]

    message = ""
    for line in git_result[4:]:
        if line.startswith("diff --git"):
            break
        else:
            message += line
            message += "\n"

    run_id = os.environ["GITHUB_RUN_ID"]
    org_name = "randovania"
    repo_name = "randovania"

    async with aiohttp.ClientSession() as session:
        session.headers['Authorization'] = f"Bearer {os.environ['GITHUB_TOKEN']}"

        async with session.get(f"https://api.github.com/repos/{org_name}/{repo_name}/actions/runs/{run_id}",
                               raise_for_status=True) as response:
            run_details = await response.json()
            check_suite_id = run_details["check_suite_id"]

        async with session.get(f"https://api.github.com/repos/{org_name}/{repo_name}/actions/runs/{run_id}/artifacts",
                               raise_for_status=True) as response:
            artifacts = await response.json()

    fields = [
        {
            "name": typing.cast(str, artifact["name"]).replace("Executable", "").strip(),
            "value": f"[Download](https://github.com/{org_name}/{repo_name}/suites/{check_suite_id}/artifacts/{artifact['id']})",
            "inline": True
        }
        for artifact in artifacts["artifacts"]
    ]

    webhook_data = {
        "embeds": [{
            "color": 0x2ecc71,
            "title": f"Randovania {VERSION}",
            "url": f"https://github.com/randovania/randovania/commit/{commit_hash}",
            "description": message.strip(),
            "fields": fields,
            "timestamp": datetime.datetime.now().isoformat()
        }]
    }
    webhook_url = os.environ["DISCORD_WEBHOOK"]
    async with aiohttp.ClientSession() as session:
        async with session.post(webhook_url, json=webhook_data, raise_for_status=True) as response:
            print(await response.text())


if __name__ == '__main__':
    asyncio.run(post_to_discord())
