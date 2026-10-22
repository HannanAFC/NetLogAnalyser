# NetLogAnalyser

A real-time network log analysis platform. Users send network packet data to a
REST API using an API key; the data is stored, enriched with geo and anomaly
information, and streamed live to a React dashboard.

Want to see the full documentation? Check out [NetLogAnalyser Docs](https://docs.netloganalyser.com).

# Table of Contents
- [Usage](#usage)
    - [Quick Start](#quick-start)
        - [Account Setup](#account-setup)
        - [Python packet sender example](#python-packet-sender-example)
    - [Self-hosting](#self-hosting)
        - [Requirements](#requirements)
        - [One-command install](#one-command-install)
- [Architecture](#architecture)
- [Development Setup](#development-setup)

## Usage
NetLogAnalyser is completely free to use, there is a hosted version which requires no setup, or a self-hosted instance which can be used if you want to have full control over your data. The self-hosted instance has complete feature parity with the hosted version, however features like the email service and S3 storage will require extra setup and is not provided.

### Quick Start
#### Account Setup
To start using NetLogAnalyser, navigate to the [website](https://www.netloganalyser.com/), here you can register an account. Once registered, head to [settings](https://www.netloganalyser.com/settings) and create an API key, this is what allows you to send network logs to the API. Give it a label e.g. `Home Network` and click create, **make sure to save the API key in a secure location**, as this is the only time the key will be shown, if you lose it you'll have to create a new one.

#### Python packet sender example
That's it, you're ready to start sending network logs. You can try it out by sending a request to the API, here's an example script to test it out with.
```Python
import datetime as dt
import requests

API = "https://YOUR_BACKEND/ingest"
KEY = "key_your_key_here"

def send(entries: list[dict]) -> None:
    resp = requests.post(
        API,
        json={"entries": entries},
        headers={"X-API-Key": KEY},
        timeout=10,
    )
    resp.raise_for_status()
    body = resp.json()
    for err in body["errors"]:
        print("rejected", entries[err["index"]], err["detail"])

send([{
    "src_ip": "198.51.100.4",
    "dst_ip": "10.0.0.5",
    "src_port": 40000,
    "dst_port": 22,
    "protocol": "TCP",
    "packet_size_bytes": 64,
    "flags": "SYN",
    "raw_payload": {},
    "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
}])
```

### Self-hosting
NetLogAnalyser can be used in a fully self-hosted instance.
#### Requirements
- Docker with the compose plugin (Docker Desktop, or Docker Engine + `docker compose`)
- `curl` and `openssl` which are required by the installer
- *Optional:* A free [MaxMind GeoLite2 account](https://www.maxmind.com/en/create-account) if you want geo enrichment

#### One-command install
```bash
curl -fsSL https://raw.githubusercontent.com/HannanAFC/NetLogAnalyser/main/selfhost/install.sh | bash
```

For more advanced setup instructions, please review the [full documentation](https://docs.netloganalyser.com/docs/selfhost-install).

The documentation includes details about fine tuning the anomaly detection, this may be desired as all networks are different and anomaly detection requires context about the network, the default settings are generalised in order to be effective across a large range of networks - this means it may not perform as good with networks that have unique traffic patterns. The [log_sender CLI tool](https://github.com/HannanAFC/NetLogAnalyser/tree/main/tools/log_sender) can replay network packet streams, this can be used to fine tune the settings of a self-hosted instance to be more effective at detecting anomalies in specific traffic.

## Architecture
```
Browser (React SPA)
    │  access token in memory, refresh token in an httpOnly cookie
    │  live dashboard
    ▼
FastAPI backend ────────────────┐
    │  /ingest  (API key)       │ enqueue jobs
    │  /logs, /analytics, ...   ▼
    │  /ws/live            Redis ──► Arq worker (exports, account deletion)
    ▼                        ▲
Postgres                     └─ rate limits, pub/sub, locks, download tokens
```

## Development Setup
Development should be done using Docker to run the application. This way Python and Node versions are entirely independent of the host machine. To get started, clone the repo.

```sh
git clone https://github.com/HannanAFC/NetLogAnalyser.git
```

Then you need to navigate to the directory of the project, and create a `.env` file, you can simply copy the contents of `.env.example`, this should be fine for developemnt, you can also enable the testing endpoints `ENABLE_TEST_ENDPOINTS` as they are needed in order to run the frontend integration tests.

After this is done, open a shell inside of the project directory and start the Docker compose stack:
```Bash
docker compose --profile dev up
```

**Always run the `dev` profile in development**, if you don't do this then some of the required containers will not be started.

When writing code, make sure to run the tests to make sure the application still works properly, `/backend`, `/frontend` and `/docs-site` all have their own tests that they need to pass, otherwise a pull-request won't pass it's checks.

When adding new features, **especially** to the backend, make sure to write **new** tests to make sure the feature handles edge cases and errors properly, and is secure.

Each section of the application (`/backend`, `/frontend`, `/docs-site`) includes its own README.md which can be referenced when figuring out how something works, expected coding patterns and formatting as well as how to run tests.