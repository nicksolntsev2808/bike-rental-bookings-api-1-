# bike-rental-bookings-api

Учёт бронирований велопроката. Приложение на Python + FastAPI, подключение к MongoDB через `motor` (асинхронный драйвер).

### Структура
```
├── app/
│   └── main.py
├── requirements.txt
└── .env.example
```

## API методы

### Проверка состояния
```bash
curl http://127.0.0.1:8030/health
```

### Создать бронирование
```bash
curl -X POST http://127.0.0.1:8030/api/v1/bookings \
  -H 'Content-Type: application/json' \
  -d '{"customer_name":"Олег","bike_type":"горный","returned":false}'
```

### Получить список (с фильтрами)
```bash
curl http://127.0.0.1:8030/api/v1/bookings
curl "http://127.0.0.1:8030/api/v1/bookings?bike_type=горный"
curl "http://127.0.0.1:8030/api/v1/bookings?returned=false"
```

### Получить по ID
```bash
curl http://127.0.0.1:8030/api/v1/bookings/<id>
```

### Обновить (частично)
```bash
curl -X PATCH http://127.0.0.1:8030/api/v1/bookings/<id> \
  -H 'Content-Type: application/json' \
  -d '{"returned":true}'
```

### Удалить
```bash
curl -X DELETE http://127.0.0.1:8030/api/v1/bookings/<id>
```

---

## Задача: запустить через venv + systemd

MongoDB на машине уже установлен и запущен локально (слушает `127.0.0.1:27017`) — это не часть задачи. Задача — развернуть само приложение как системный сервис.

1. Создай виртуальное окружение (`venv`) в директории проекта, активируй, установи зависимости из `requirements.txt`.
2. Подготовь `.env` на основе `.env.example` — укажи реальные `HOST`/`PORT` и, если нужно, другие значения.
3. Убедись, что приложение стартует вручную из venv (`python app/main.py` или через `uvicorn`) и отвечает на `/health`.
4. Напиши systemd unit-файл для приложения самостоятельно (`[Unit]`/`[Service]`/`[Install]`):
   - `ExecStart=` — через python-интерпретатор из `venv`, не системный;
   - `EnvironmentFile=` — чтобы подхватить `.env` (вспомни про `${HOST}`/`${PORT}` подстановку в `ExecStart=`, если будешь их туда передавать явно);
   - `WorkingDirectory=`;
   - `Restart=` — подумай, какое значение подходит для сервиса, который должен сам поднимался после падения;
   - `After=` — от чего этот сервис логически зависит (вспомни, зачем это нужно, даже если MongoDB — не systemd-юнит, который ты сам поднимаешь).
5. Размести unit-файл в правильной директории systemd, перезагрузи конфигурацию (`daemon-reload`), включи автозапуск и запусти сервис.
6. Проверь статус (`systemctl status`), и что сервис переживает `systemctl restart`.
7. Проверь все пять эндпоинтов через `curl` (см. примеры выше).
8. Проверь логи сервиса через `journalctl -u <имя_сервиса>` — убедись, что там видно старт uvicorn и обращения к MongoDB.
