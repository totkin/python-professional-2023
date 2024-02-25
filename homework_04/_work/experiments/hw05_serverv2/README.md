# HTTP Server

## Описание

Базовый HTTP-сервер с использованием thread pool

Запуск сервера:

    python httpd.py

Нагрузочное тестирование:
    
    python httpd.py
    wrktoolbox run --settings wrk.yaml

Для НТ требуется установленный `wrk` и модуль pip `wrktoolbox`

Результаты НТ:

    Running 30s test @ http://localhost:9999/dir2/
      50 threads and 100 connections
      Thread Stats   Avg      Stdev     Max   +/- Stdev
        Latency   166.81ms    1.06s   13.37s    97.40%
        Req/Sec    56.24     38.85   232.00     65.68%
      Latency Distribution
         50%   13.12ms
         75%   15.48ms
         90%   21.99ms
         99%    6.06s
      27922 requests in 30.09s, 7.16MB read
      Socket errors: connect 0, read 0, write 0, timeout 5
    Requests/sec:    927.84
    Transfer/sec:    243.74KB
