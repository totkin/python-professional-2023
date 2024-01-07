Scoring API


Задача

Реализовать декларативный язык описания и систему валидации запросов к HTTP API сервиса скоринга. Шаблон уже есть в `api.py`, тесты в `test.py`, функционал подсчета скора в `scoring.py`. API необычно тем, что пользователи дергают методы POST запросами. Чтобы получить результат пользователь отправляет в POST запросе валидный JSON определенного формата на локейшн /method

Тестирование

Запуск тестов осуществляется по комманде `python -m unittest`

Запуск приложения

`python api.py`

Примеры запросов

```sh
curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method": "online_score", "token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd", "arguments": {"phone": "79037006050", "email": "test4git@gmail.ru", "first_name": "Стансилав", "last_name": "Fantom", "birthday": "31.12.1970", "gender": 1}}' http://127.0.0.1:8080/method/
```
