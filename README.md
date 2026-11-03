# Network Diagnostic Telegram Bot

Желі ақауларын диагностикалайтын Telegram-бот. Нәтижені ЖИ қарапайым тілмен түсіндіреді.

## Командалар
- /ping сайт.com: пинг
- /trace сайт.com: трассировка
- /dns сайт.com: DNS тексеру

## Орнату
1. Python орнату (python.org, "Add python.exe to PATH" галочкасымен)
2. `pip install -r requirements.txt`
3. `.env.example` файлын `.env` деп көшіріп, токен мен кілтті жаз:
   - TOKEN: @BotFather-ден
   - GEMINI_API_KEY: aistudio.google.com-нан
4. `python bot.py`

## Қауіпсіздік
- Хост атауы `HOST_RE` регулярлы өрнегімен тексеріледі (command injection-нан қорғау)
- Токен мен кілт `.env` файлында, GitHub-қа жүктелмейді
- ЖИ қолжетімсіз болса, бот қарапайым резервті түсіндірме береді

## Технологиялар
Python, python-telegram-bot, Google Gemini API, subprocess