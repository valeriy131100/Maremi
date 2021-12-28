# Maremi
Простой бот для синхронизации [vk](https://vk.com) чата и [discord](https://discord.com) сервера. Использует [disnake](https://github.com/DisnakeDev/disnake), [vkbottle](https://github.com/vkbottle/vkbottle) и [aiosqlite](https://github.com/omnilib/aiosqlite). Для хранения некоторых изображений используется [freeimagehost](https://freeimage.host/).

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
* VK_PREFIX - префикс вк-бота, по умолчанию - /
* VK_ALIAS_PREFIX - префикс вк-бота для алиасов каналов, по умолчанию - #
* VK_GROUP_ID - id группы вконтакте в которой запущен бот
* DISCORD_TOKEN - токен для дискорд-бота
* DISCORD_PREFIX - префикс дискорд-бота, по умолчанию - m.
* DATABASE - путь до базы данных SQLite, по умолчанию - servers.db. База будет создана, если файл не найден
* FREEIMAGEHOST_KEY - токен [FreeImageHost](https://freeimage.host/page/api)

На сервере и в чате у ботов должен быть полный доступ к сообщениям, дискорд-боту необходимы также права для управления сообщениями и вебхуками. В будущем возможно понадобится администрирование.

Находясь в директории Maremi исполните:
```bash
$ bin/python main.py
```
Бот запустится.

# Основные команды
Команды указаны с префиксами по умолчанию.

* Discord
  * m.help - возвращает список команд.
  * m.connect \<chat_id\> - подключает сервер к чату ВК. Устанавливает текущий канал как канал по умолчанию.
  * m.nickname \<nickname\> - устанавливает никнейм, который будет использоваться при отправке сообщений в вк.
  * m.nickname remove - удаляет никнейм.
  * m.alias \<alias\> - устанавливает алиас для текущего канала. В алиасы можно отправлять сообщения через вк бота с помощью \#\<alias\>.
  * m.alias remove \<alias\> - удаляет алиас \<alias\>.
  * m.default - устанавливает текущий канал как канал для команды /send.
  * m.art - устанавливает текущий канал как канал для команды /art.
  * m.duplex - устанавливает текущий канал как канал для дуплекса (режим когда сообщения автоматически отсылаются из ВК в Дискорд и обратно).
  * m.split \<ref_message\> - разделяет сообщение с вложениями на отдельные. Необходимо переслать с командой оригинальное сообщение.
  * m.gallery \<ref_message|attachments\> - превращает текущее или пересланное сообщение в интерактивную галерею
* VK
  * /help - возвращает список команд.
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
