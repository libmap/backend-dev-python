#!./venv/bin/python
import os
from lib.shared import base_folder
from api import create_app
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(base_folder, 'log/api.log')),
        logging.StreamHandler()
    ]
)

app = create_app()
try:
    app.run(port=5000, host='0.0.0.0')
except KeyboardInterrupt:
    pass
