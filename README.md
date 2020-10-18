# Backend

## Prerequisites

Create virtual environment
```
python -m venv venv
```
Activate environment and install required python packages
```
. venv/bin/activate
pip install -r requirements.txt
```

### Config

You have to copy the `config.template.json` to `config.json` and adjust it to your needs. (Twitter Credentials, ...)


## Listener

```
./runListener.py
```

## API (Webserver)

```
./runApi.py
```
