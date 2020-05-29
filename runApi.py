#!/usr/bin/env python
from api import create_app


def main():
    app = create_app()
    app.run(port=5000, host='0.0.0.0')
    # q = Queue()
    # p = Process(target=runListener, args=(q,))
    # p.start()
    # print(q.get())
    # p.join()

main()
