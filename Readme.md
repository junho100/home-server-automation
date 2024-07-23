# Home Server Setup Automation
Setting up home server automatically using container.

## Main Idea

- Setup virtual linux environment using docker container.
- For SSH connection, use Selenium to automate port forwarding configuration.
- Use flask server for one time key server.

## Overall Architecture

![home-server drawio](https://github.com/user-attachments/assets/d426a608-1565-4ac0-89b3-cfdb55c8058a)

## Development Environment

- Python 3.9
- Docker 26.1.4
- Docker API 7.1.0
- Selenium 4.21.0
- Flask 3.0.3
- Ubuntu 24.04

## Installation
1. create python virtual environment
```commandline
python -m venv venv
source venv/bin/activate
```

2. install required packages
```commandline
pip3 install -e .
```

## How to use

```commandline
python main.py
```
