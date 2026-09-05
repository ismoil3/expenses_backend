TEXTS: dict[str, str] = {
    # --- начало ---
    "start.greeting": (
        "Привет, {name}! 👋\n\n"
        "Я считаю ваши расходы — просто напишите, "
        "категорию определю сам.\n\n"
        "<code>кофе 350</code>\n"
        "<code>такси 900 работа</code>\n"
        "<code>кофе 350, хлеб 20</code>   — несколько сразу\n"
        "<code>5$ подписка</code>   — другая валюта\n\n"
        "📸 Пришлите фото чека — прочитаю сумму сам.\n"
        "<i>Подпишите фото, за что платили — например «кофе»</i>\n\n"
        "Кнопки снизу — итоги и веб-панель."
    ),
    "help.text": (
        "<b>Добавить расход</b>\n"
        "Сумма и описание одним сообщением, в любом порядке:\n"
        "<code>кофе 350</code> · <code>350 кофе</code> · <code>такси 900 работа</code>\n\n"
        "<b>Несколько сразу</b>\n"
        "<code>кофе 350, такси 900, хлеб 20</code>\n\n"
        "<b>Другая валюта</b>\n"
        "<code>5$ подписка</code> · <code>500р курс</code> · <code>350с хлеб</code>\n"
        "Итоги всегда в вашей основной валюте.\n\n"
        "<b>Задать категорию самому</b>\n"
        "<code>кофе 350 #cafe</code>\n\n"
        "<b>Команды</b>\n"
        "/today /week /month — итоги\n"
        "/last — последние расходы\n"
        "/undo — удалить последний\n"
        "/cats — категории\n"
        "/export — выгрузить CSV\n"
        "/lang — язык · /currency — валюта\n"
        "/panel — веб-панель"
    ),
    # --- клавиатура ---
    "kb.today": "📊 Сегодня",
    "kb.week": "🗓 Неделя",
    "kb.month": "📈 Месяц",
    "kb.panel": "🌐 Панель",
    # --- периоды ---
    "label.today": "Сегодня",
    "label.week": "Неделя",
    "label.month": "Месяц",
    "label.total": "Всего",
    "label.all_time": "Всё время",
    # --- сохранение ---
    "expense.saved": "✅ <b>{amount}</b>{desc}\n{cat}\n\n{period}: <b>{total}</b>",
    "expense.multi_header": "✅ Записал <b>{count}</b>",
    "expense.multi_footer": "\n{period}: <b>{total}</b>",
    "expense.limit": "\n⚠️ В одном сообщении до {limit} расходов — взял первые.",
    "expense.not_understood": (
        "🤔 Не нашёл сумму\n\n"
        "Напишите так:\n"
        "<code>кофе 350</code>\n"
        "<code>такси 900 работа</code>\n"
        "<code>5$ подписка</code>"
    ),
    "expense.deleted": "🗑 Удалено\n<s>{amount} · {cat}</s>",
    "expense.restored": "↩️ Вернул\n<b>{amount}</b> · {cat}",
    "expense.deleted_many": "🗑 Удалено: <b>{count}</b>\n\n{period}: <b>{total}</b>",
    "expense.nothing_to_undo": "Пока нечего удалять.",
    # --- фото чека ---
    "receipt.reading": "📸 Читаю чек…",
    "receipt.saved": "✅ <b>{amount}</b>{desc}\n{cat}\n\n{period}: <b>{total}</b>",
    "receipt.failed": (
        "😕 Не смог разобрать сумму на этом фото.\n\n"
        "Напишите вручную, например: <code>128.5 ашан</code>"
    ),
    "receipt.too_big": "Фото слишком большое — пришлите поменьше.",
    "expense.not_found": "Этот расход уже удалён.",
    # --- кнопки ---
    "btn.amount": "💵 Сумма",
    "btn.category": "✏️ Категория",
    "btn.cancel": "Отмена",
    "btn.delete": "🗑 Удалить",
    "btn.restore": "↩️ Вернуть",
    "btn.undo_all": "↩️ Отменить всё",
    "btn.back": "← Назад",
    # --- исправление суммы ---
    "edit.ask_amount": (
        "Сейчас: <b>{current}</b>\n\n"
        "Напишите новую сумму:\n"
        "<code>450</code>   ·   <code>450 кофе</code>   ·   <code>5$</code>"
    ),
    "edit.bad_amount": "Не нашёл число. Напишите сумму, например <code>450</code>",
    "edit.saved": (
        "✅ Исправлено\n\n"
        "<b>{amount}</b>{desc}\n{cat}\n\n{period}: <b>{total}</b>"
    ),
    "edit.cancelled": "Оставил как было.",
    "edit.cancelled_command": "Отменил исправление. Повторите команду.",
    # --- лимиты ---
    "btn.limit_add": "➕ Поставить лимит",
    "limits.title": "🎯 <b>Лимиты на месяц</b>",
    "limits.empty": (
        "🎯 <b>Лимиты на месяц</b>\n\n"
        "Пока не заданы.\n"
        "<i>Поставьте лимит — предупрежу, когда подойдёте к нему.</i>"
    ),
    "limits.choose_category": "На какую категорию поставить лимит?",
    "limits.ask_amount": (
        "{cat}\n\nСколько в месяц, в {currency}?\n"
        "<code>1000</code>   ·   <code>2500</code>"
    ),
    "limits.saved": "✅ Лимит сохранён",
    "limits.removed": "Лимит снят",
    "limits.too_many": "Больше {limit} лимитов не получится.",
    "limits.status": "{mark} Лимит за месяц: <b>{spent}</b> из {limit}",
    "limits.near": (
        "⚠️ <b>Подходите к месячному лимиту</b>\n"
        "<code>{bar}</code>  {spent} из {limit}"
    ),
    "limits.exceeded": (
        "🔴 <b>Месячный лимит превышен</b>\n"
        "<code>{bar}</code>  {spent} из {limit}"
    ),
    # --- категории ---
    "category.choose": "Выберите подходящую категорию:",
    "category.changed": "Теперь: {cat}",
    "category.list": (
        "🗂 <b>Ваши категории</b>\n"
        "<i>Звёздочка — созданная вами</i>\n"
    ),
    # --- новая категория ---
    "newcat.suggest": (
        "\n\n🤔 «{phrase}» не подошло ни к одной категории.\n"
        "Создать новую?\n\n"
        "        <b>{emoji} {name}</b>"
    ),
    "btn.newcat_yes": "✅ Да, создать",
    "btn.newcat_no": "❌ Нет, оставить «Другое»",
    "newcat.created": (
        "✅ <b>{amount}</b> · {emoji} {name}\n\n"
        "Категория создана. В следующий раз «{phrase}» узнаю сам."
    ),
    "newcat.declined": (
        "Хорошо — оставляю в «Другое».\n"
        "<i>Больше про «{phrase}» не спрошу.</i>"
    ),
    "newcat.limit": "Достигнут предел в {limit} своих категорий.",
    # --- отчёты ---
    "report.header": "📊 <b>{period}</b> · {date}",
    "report.by_days": "<b>По дням</b>",
    "report.by_weeks": "<b>По неделям</b>",
    "report.footer": "{label}: <b>{total}</b>  ·  расходов: {count}",
    "report.empty": (
        "📊 <b>{period}</b>\n\n"
        "За этот период расходов нет.\n"
        "<i>Напишите «кофе 350», чтобы начать.</i>"
    ),
    "last.title": "🧾 <b>Последние расходы</b>\n<i>Нажмите номер, чтобы изменить</i>\n",
    "last.empty": "Расходов пока нет.\n<i>Напишите «кофе 350».</i>",
    # --- язык и валюта ---
    "lang.choose": "Выберите язык интерфейса:",
    "lang.changed": "✅ Язык: {lang}",
    "currency.choose": (
        "Выберите основную валюту.\n"
        "<i>В ней считаются все итоги.</i>"
    ),
    "currency.changed": (
        "✅ Основная валюта: <b>{currency}</b>\n"
        "<i>Перевёл {count} расходов и лимиты по текущему курсу.</i>"
    ),
    # --- панель ---
    "btn.open_panel": "🌐 Открыть в браузере",
    "btn.open_miniapp": "📱 Открыть в Telegram",
    "panel.link": (
        "🌐 <b>Веб-панель</b>\n\n"
        "Расходы по категориям и дням, правка и выгрузка.\n"
        "Вход по кнопке — пароль не нужен.\n\n"
        "<i>Ссылка живёт 5 минут и открывается один раз.</i>"
    ),
    "panel.link_plain": (
        "🌐 <b>Веб-панель</b>\n\n"
        "{url}\n\n"
        "<i>Ссылка живёт 5 минут и открывается один раз.</i>"
    ),
    # --- экспорт ---
    "export.caption": "📄 Расходы за {period} · {count} шт.",
    "export.empty": "За этот период расходов нет — выгружать нечего.",
    # --- ошибки ---
    "error.generic": "Что-то пошло не так 😕 Попробуйте ещё раз.",
}
