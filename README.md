# YaTube 

### Описание проекта
Социальная сеть для блогеров. 

Возможности:
- создание собственного блога
- подписка на блоги других авторов
- комментарии к постам

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```
git clone https://github.com/ilgiz-n/hw05_final.git
```

```
cd api_yamdb
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

```
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py makemigrations
```

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```

Проект будет доступен по адресу:

http://127.0.0.1:8000

### Системные требования

- Python 3.7.3
- Django 2.2.16
- mixer, Pillow, pytest, pytest-django, pytest-pythonpath, requests, six, sorl-thumbnail, Faker

