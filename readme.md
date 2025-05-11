# VirtuSSH

VirtuSSH — це мінімалістичний SSH-сервер, написаний на Python з використанням бібліотеки Paramiko. Кожен користувач має власну ізольовану віртуальну файлову систему, а доступ дозволений лише через SSH-ключі.

## Особливості

- Аутентифікація через публічні ключі (SSH)
- Віртуальна файлова система в памʼяті
- Підтримка команд:
  - `ls` — перегляд файлів
  - `cat <імʼя_файлу>` — перегляд вмісту файлу
  - `write <імʼя_файлу>` — створення/редагування файлу
  - `rm <імʼя_файлу>` — видалення файлу
  - `exit` — вихід із сесії

## Встановлення

```bash
git clone https://github.com/your-username/virtu-ssh.git
cd virtu-ssh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Запуск сервера

```bash
python ssh_server.py
```

Сервер за замовчуванням слухає порт 2200.

## Генерація SSH-ключа

На клієнті виконай:

```bash
ssh-keygen -t rsa -b 2048 -f my_user_key
```

Після цього встав вміст `my_user_key.pub` у список `AUTHORIZED_KEYS` у `ssh_server.py`.

## Підключення до сервера

```bash
ssh -p 2200 -i my_user_key <користувач>@localhost
```

## Структура проєкту

```
virtussh/
├── ssh_server.py          # Основний код сервера
├── file_system.py         # Реалізація віртуальної ФС
├── server_host_key        # Приватний хост-ключ
├── server_host_key.pub    # Публічний хост-ключ
├── requirements.txt       # Залежності
└── README.md              # Документація
```

## Ліцензія

MIT License

