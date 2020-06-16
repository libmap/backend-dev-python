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

### Twitter Credentials

Some functions require a twitter developer account, copy the file `twitter-auth.template.json` to `twitter-auth.json` and put there your credentials. 

## Listener

```
./runListener.py
```

## API (Webserver)

```
./runApi.py
```
