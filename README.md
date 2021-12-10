# Maremi
Простой бот для синхронизации vk чата и discord сервера. Использует discord.py, vkbottle и aiosqlite.

# Установка
Вам понадобится установленный Python 3.9 и git.

Склонируйте репозиторий:
```bash
$ git clone https://github.com/valeriy131100/Maremi
```

Создайте в этой папке виртуальное окружение:
```bash
$ python3 -m venv [полный путь до папки Maremi]
```

Активируйте виртуальное окружение и установите зависимости:
```bash
$ cd Maremi
$ source bin/activate
$ pip install -r requirements.txt
```
# Использование
Заполните файл .env.example и переименуйте его в .env или иным образом передайте переменные среды:
* VK_TOKEN - токен для вк-бота
* DISCORD_TOKEN - токен для дискорд-бота

На сервере и в чате у ботов должен быть полный доступ к сообщениям. В будущем возможно понадобится администрирование.

Находясь в директории Maremi исполните:
```bash
$ bin/python main.py
```
Бот запустится.

# Основные команды
* Discord
  * m.start - тестовая команда. Возвращает айди канала.
  * m.connect \<chat_id\> - подключает сервер к чату ВК. Устанавливает текущий канал как канал по умолчанию.
  * m.set nickname \<nickname\> - устанавливает никнейм, который будет использоваться при отправке сообщений в вк.
  * m.remove nickname - удаляет никнейм.
  * m.make alias \<alias\> - устанавливает алиас для текущего канала. В алиасы можно отправлять сообщения через вк бота с помощью \#\<alias\>.
  * m.remove alias \<alias\> - удаляет алиас \<alias\>.
  * m.set default - устанавливает текущий канал как канал для команды /send.
  * m.set art - устанавливает текущий канал как канал для команды /art.
  * m.set duplex - устанавливает текущий канал как канал для дуплекса (режим когда сообщения автоматически отсылаются из ВК в Дискорд и обратно).
  * m.split \<ref_message\> - разделяет сообщение с вложениями на отдельные. Необходимо переслать с командой оригинальное сообщение.
* VK
  * /start - тестовая команда. Возвращает айди чата.
  * /nickname \<nickname\> - устанавливает никнейм, который будет использоваться при отправке сообщений в дискорд.
  * /removenickname - удаляет никнейм.
  * /makeonline - дает возможность подключить этот чат к серверу в дискорде. Возвращает команду для подключения.
  * /makeoffline - убирает возможность подключить этот чат к серверу.
  * /send - отсылает сообщение в канал default.
  * /art - отсылает сообщение в канал art.
  * \#\<alias\> - отсылает сообщение в канал с указанным алиасом.
  * любое сообщение не команда - отсылает в канал duplex, если таковой есть.

# Предостережения
* Автор совершенно не знаком с асинхронным программированием и async и await везде понатыканы просто из-за библиотек ботов. Не пытайтесь запускать много серверов или использовать бота на крупных серверах, это может иметь непредсказуемые последствия. Также в боте сейчас нет абсолютно никакой проверки ролей, а соединение сервера и чата весьма небезопасно. 
* Код лицензирован под MIT, делайте с ним что хотите, лишь бы он не обрел сознание :)
* Проект написан лишь для удобства общения с группой друзей и находится в глубокой альфе, так что фичи еще будут добавляться и перерабатываться.
