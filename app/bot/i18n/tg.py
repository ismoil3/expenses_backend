TEXTS: dict[str, str] = {
    # --- оғоз ---
    "start.greeting": (
        "Салом, {name}! 👋\n\n"
        "Ман харҷҳои шуморо ҳисоб мекунам — танҳо нависед, "
        "категорияро худам муайян мекунам.\n\n"
        "<code>кофе 350</code>\n"
        "<code>такси 900 кор</code>\n"
        "<code>кофе 350, нон 20</code>   — якчандто якбора\n"
        "<code>5$ обуна</code>   — валютаи дигар\n\n"
        "📸 Акси чекро фиристед — суммаро худам мехонам.\n"
        "<i>Дар зери акс нависед, ки барои чӣ буд — масалан «кофе»</i>\n\n"
        "Тугмаҳои поён — ҳисобот ва панели веб."
    ),
    "help.text": (
        "<b>Иловаи харҷ</b>\n"
        "Сумма ва тавсиф дар як паём, бо ҳар тартиб:\n"
        "<code>кофе 350</code> · <code>350 кофе</code> · <code>такси 900 кор</code>\n\n"
        "<b>Якчандто якбора</b>\n"
        "<code>кофе 350, такси 900, нон 20</code>\n\n"
        "<b>Валютаи дигар</b>\n"
        "<code>5$ обуна</code> · <code>500р курс</code> · <code>350с нон</code>\n"
        "Ҳисобот ҳамеша дар валютаи асосии шумо.\n\n"
        "<b>Категорияро худатон нишон диҳед</b>\n"
        "<code>кофе 350 #cafe</code>\n\n"
        "<b>Командаҳо</b>\n"
        "/today /week /month — ҳисобот\n"
        "/last — харҷҳои охирин\n"
        "/undo — охиринро нест кардан\n"
        "/cats — категорияҳо\n"
        "/export — файли CSV\n"
        "/lang — забон · /currency — валюта\n"
        "/panel — панели веб"
    ),
    # --- клавиатура ---
    "kb.today": "📊 Имрӯз",
    "kb.week": "🗓 Ҳафта",
    "kb.month": "📈 Моҳ",
    "kb.panel": "🌐 Панел",
    # --- давраҳо ---
    "label.today": "Имрӯз",
    "label.week": "Ҳафта",
    "label.month": "Моҳ",
    "label.total": "Ҳамагӣ",
    "label.all_time": "Ҳама вақт",
    # --- сабти харҷ ---
    "expense.saved": "✅ <b>{amount}</b>{desc}\n{cat}\n\n{period}: <b>{total}</b>",
    "expense.multi_header": "✅ <b>{count} харҷ</b> сабт шуд",
    "expense.multi_footer": "\n{period}: <b>{total}</b>",
    "expense.limit": "\n⚠️ Дар як паём то {limit} харҷ — аввалинҳояшро гирифтам.",
    "expense.not_understood": (
        "🤔 Сумма ёфт нашуд\n\n"
        "Ин тавр нависед:\n"
        "<code>кофе 350</code>\n"
        "<code>такси 900 кор</code>\n"
        "<code>5$ обуна</code>"
    ),
    "expense.deleted": "🗑 Нест шуд\n<s>{amount} · {cat}</s>",
    "expense.restored": "↩️ Баргашт\n<b>{amount}</b> · {cat}",
    "expense.deleted_many": "🗑 <b>{count} харҷ</b> нест шуд\n\n{period}: <b>{total}</b>",
    "expense.nothing_to_undo": "Ҳанӯз харҷе нест, ки нест кунам.",
    # --- акси чек ---
    "receipt.reading": "📸 Чекро мехонам…",
    "receipt.saved": "✅ <b>{amount}</b>{desc}\n{cat}\n\n{period}: <b>{total}</b>",
    "receipt.failed": (
        "😕 Суммаро аз ин акс хонда натавонистам.\n\n"
        "Дастӣ нависед, масалан: <code>128.5 ашан</code>"
    ),
    "receipt.too_big": "Акс хеле калон аст — хурдтарашро фиристед.",
    "expense.not_found": "Ин харҷ аллакай нест шудааст.",
    # --- тугмаҳо ---
    "btn.amount": "💵 Сумма",
    "btn.category": "✏️ Категория",
    "btn.cancel": "Бекор",
    "btn.delete": "🗑 Нест",
    "btn.restore": "↩️ Баргардонед",
    "btn.undo_all": "↩️ Ҳамаро бекор кун",
    "btn.back": "← Бозгашт",
    # --- ислоҳи сумма ---
    "edit.ask_amount": (
        "Ҳозир: <b>{current}</b>\n\n"
        "Суммаи навро нависед:\n"
        "<code>450</code>   ·   <code>450 кофе</code>   ·   <code>5$</code>"
    ),
    "edit.bad_amount": "Рақам ёфт нашуд. Суммаро нависед, масалан <code>450</code>",
    "edit.saved": (
        "✅ Ислоҳ шуд\n\n"
        "<b>{amount}</b>{desc}\n{cat}\n\n{period}: <b>{total}</b>"
    ),
    "edit.cancelled": "Ҳамон тавр монд.",
    "edit.cancelled_command": "Ислоҳ бекор шуд. Командаро такрор кунед.",
    # --- лимитҳо ---
    "btn.limit_add": "➕ Лимит гузоштан",
    "limits.title": "🎯 <b>Лимитҳои моҳона</b>",
    "limits.empty": (
        "🎯 <b>Лимитҳои моҳона</b>\n\n"
        "Ҳанӯз гузошта нашудаанд.\n"
        "<i>Лимит гузоред — ҳангоми наздик шудан огоҳ мекунам.</i>"
    ),
    "limits.choose_category": "Ба кадом категория лимит гузорем?",
    "limits.ask_amount": (
        "{cat}\n\nДар як моҳ чанд, бо {currency}?\n"
        "<code>1000</code>   ·   <code>2500</code>"
    ),
    "limits.saved": "✅ Лимит сабт шуд",
    "limits.removed": "Лимит бардошта шуд",
    "limits.too_many": "Зиёда аз {limit} лимит намешавад.",
    "limits.status": "{mark} Лимити моҳ: <b>{spent}</b> аз {limit}",
    "limits.near": (
        "⚠️ <b>Ба лимити моҳона наздик шудед</b>\n"
        "<code>{bar}</code>  {spent} аз {limit}"
    ),
    "limits.exceeded": (
        "🔴 <b>Лимити моҳона гузашт</b>\n"
        "<code>{bar}</code>  {spent} аз {limit}"
    ),
    # --- категорияҳо ---
    "category.choose": "Категорияи мувофиқро интихоб кунед:",
    "category.changed": "Акнун: {cat}",
    "category.list": (
        "🗂 <b>Категорияҳои шумо</b>\n"
        "<i>Ситорача — категорияи худсохт</i>\n"
    ),
    # --- категорияи нав ---
    "newcat.suggest": (
        "\n\n🤔 «{phrase}»-ро ба ягон категория мувофиқ карда натавонистам.\n"
        "Категорияи нав созем?\n\n"
        "        <b>{emoji} {name}</b>"
    ),
    "btn.newcat_yes": "✅ Ҳа, бисоз",
    "btn.newcat_no": "❌ Не, «Дигар» монад",
    "newcat.created": (
        "✅ <b>{amount}</b> · {emoji} {name}\n\n"
        "Категорияи нав сохта шуд. Дафъаи оянда «{phrase}»-ро худам мешиносам."
    ),
    "newcat.declined": (
        "Хуб — дар «Дигар» мемонад.\n"
        "<i>Дигар дар бораи «{phrase}» намепурсам.</i>"
    ),
    "newcat.limit": "Ҳадди {limit} категорияи худсохт пур шудааст.",
    # --- ҳисобот ---
    "report.header": "📊 <b>{period}</b> · {date}",
    "report.by_days": "<b>Аз рӯи рӯзҳо</b>",
    "report.by_weeks": "<b>Аз рӯи ҳафтаҳо</b>",
    "report.footer": "{label}: <b>{total}</b>  ·  {count} харҷ",
    "report.empty": (
        "📊 <b>{period}</b>\n\n"
        "Дар ин давра харҷ нест.\n"
        "<i>Барои оғоз «кофе 350» нависед.</i>"
    ),
    "last.title": "🧾 <b>Харҷҳои охирин</b>\n<i>Барои таҳрир рақамро пахш кунед</i>\n",
    "last.empty": "Ҳанӯз харҷ нест.\n<i>«кофе 350» нависед.</i>",
    # --- забон ва валюта ---
    "lang.choose": "Забони интерфейсро интихоб кунед:",
    "lang.changed": "✅ Забон: {lang}",
    "currency.choose": (
        "Валютаи асосиро интихоб кунед.\n"
        "<i>Ҳама ҳисоботҳо дар ҳамин ҳисоб мешаванд.</i>"
    ),
    "currency.changed": (
        "✅ Валютаи асосӣ: <b>{currency}</b>\n"
        "<i>{count} харҷ ва лимитҳо бо курси ҷорӣ гузаронида шуданд.</i>"
    ),
    # --- панел ---
    "btn.open_panel": "🌐 Дар браузер кушодан",
    "btn.open_miniapp": "📱 Дар Telegram кушодан",
    "panel.link": (
        "🌐 <b>Панели веб</b>\n\n"
        "Харҷҳо аз рӯи категория ва рӯзҳо, таҳрир ва содирот.\n"
        "Вуруд бо тугма — парол лозим нест.\n\n"
        "<i>Линк 5 дақиқа ва танҳо як маротиба кор мекунад.</i>"
    ),
    "panel.link_plain": (
        "🌐 <b>Панели веб</b>\n\n"
        "{url}\n\n"
        "<i>Линк 5 дақиқа ва танҳо як маротиба кор мекунад.</i>"
    ),
    # --- экспорт ---
    "export.caption": "📄 Харҷҳои {period} · {count} сабт",
    "export.empty": "Дар ин давра харҷ нест — чизе барои содирот нест.",
    # --- хатоҳо ---
    "error.generic": "Чизе нодуруст шуд 😕 Аз нав кӯшиш кунед.",
}
