TEXTS: dict[str, str] = {
    # --- start ---
    "start.greeting": (
        "Hi, {name}! 👋\n\n"
        "I keep track of your spending — just write it down, "
        "I'll pick the category myself.\n\n"
        "<code>coffee 350</code>\n"
        "<code>taxi 900 work</code>\n"
        "<code>coffee 350, bread 20</code>   — several at once\n"
        "<code>5$ subscription</code>   — another currency\n\n"
        "📸 Send a receipt photo — I'll read the amount myself.\n"
        "<i>Caption it with what you paid for — e.g. «coffee»</i>\n\n"
        "Buttons below — totals and the web dashboard."
    ),
    "help.text": (
        "<b>Adding an expense</b>\n"
        "Amount and note in one message, in any order:\n"
        "<code>coffee 350</code> · <code>350 coffee</code> · <code>taxi 900 work</code>\n\n"
        "<b>Several at once</b>\n"
        "<code>coffee 350, taxi 900, bread 20</code>\n\n"
        "<b>Another currency</b>\n"
        "<code>5$ subscription</code> · <code>500р course</code> · <code>350с bread</code>\n"
        "Totals are always in your base currency.\n\n"
        "<b>Set the category yourself</b>\n"
        "<code>coffee 350 #cafe</code>\n\n"
        "<b>Commands</b>\n"
        "/today /week /month — totals\n"
        "/last — recent expenses\n"
        "/undo — remove the last one\n"
        "/cats — categories\n"
        "/export — download CSV\n"
        "/lang — language · /currency — currency\n"
        "/panel — web dashboard"
    ),
    # --- keyboard ---
    "kb.today": "📊 Today",
    "kb.week": "🗓 Week",
    "kb.month": "📈 Month",
    "kb.panel": "🌐 Dashboard",
    # --- periods ---
    "label.today": "Today",
    "label.week": "Week",
    "label.month": "Month",
    "label.total": "Total",
    "label.all_time": "All time",
    # --- saving ---
    "expense.saved": "✅ <b>{amount}</b>{desc}\n{cat}\n\n{period}: <b>{total}</b>",
    "expense.multi_header": "✅ Saved <b>{count}</b>",
    "expense.multi_footer": "\n{period}: <b>{total}</b>",
    "expense.limit": "\n⚠️ Up to {limit} expenses per message — kept the first ones.",
    "expense.not_understood": (
        "🤔 I couldn't find an amount\n\n"
        "Try it like this:\n"
        "<code>coffee 350</code>\n"
        "<code>taxi 900 work</code>\n"
        "<code>5$ subscription</code>"
    ),
    "expense.deleted": "🗑 Deleted\n<s>{amount} · {cat}</s>",
    "expense.restored": "↩️ Restored\n<b>{amount}</b> · {cat}",
    "expense.deleted_many": "🗑 Deleted: <b>{count}</b>\n\n{period}: <b>{total}</b>",
    "expense.nothing_to_undo": "Nothing to delete yet.",
    # --- receipt photo ---
    "receipt.reading": "📸 Reading the receipt…",
    "receipt.saved": "✅ <b>{amount}</b>{desc}\n{cat}\n\n{period}: <b>{total}</b>",
    "receipt.failed": (
        "😕 I couldn't read the total on this photo.\n\n"
        "Write it manually, for example: <code>128.5 ashan</code>"
    ),
    "receipt.too_big": "That photo is too large — send a smaller one.",
    "expense.not_found": "This expense is already deleted.",
    # --- buttons ---
    "btn.amount": "💵 Amount",
    "btn.category": "✏️ Category",
    "btn.cancel": "Cancel",
    "btn.delete": "🗑 Delete",
    "btn.restore": "↩️ Restore",
    "btn.undo_all": "↩️ Undo all",
    "btn.back": "← Back",
    # --- fixing the amount ---
    "edit.ask_amount": (
        "Now: <b>{current}</b>\n\n"
        "Send the new amount:\n"
        "<code>450</code>   ·   <code>450 coffee</code>   ·   <code>5$</code>"
    ),
    "edit.bad_amount": "No number found. Send an amount, e.g. <code>450</code>",
    "edit.saved": (
        "✅ Updated\n\n"
        "<b>{amount}</b>{desc}\n{cat}\n\n{period}: <b>{total}</b>"
    ),
    "edit.cancelled": "Left it as it was.",
    "edit.cancelled_command": "Edit cancelled. Send the command again.",
    # --- limits ---
    "btn.limit_add": "➕ Set a limit",
    "limits.title": "🎯 <b>Monthly limits</b>",
    "limits.empty": (
        "🎯 <b>Monthly limits</b>\n\n"
        "None set yet.\n"
        "<i>Set a limit — I'll warn you when you get close.</i>"
    ),
    "limits.choose_category": "Which category should get a limit?",
    "limits.ask_amount": (
        "{cat}\n\nHow much per month, in {currency}?\n"
        "<code>1000</code>   ·   <code>2500</code>"
    ),
    "limits.saved": "✅ Limit saved",
    "limits.removed": "Limit removed",
    "limits.too_many": "No more than {limit} limits.",
    "limits.status": "{mark} Monthly limit: <b>{spent}</b> of {limit}",
    "limits.near": (
        "⚠️ <b>Getting close to the monthly limit</b>\n"
        "<code>{bar}</code>  {spent} of {limit}"
    ),
    "limits.exceeded": (
        "🔴 <b>Monthly limit exceeded</b>\n"
        "<code>{bar}</code>  {spent} of {limit}"
    ),
    # --- categories ---
    "category.choose": "Pick the right category:",
    "category.changed": "Now: {cat}",
    "category.list": (
        "🗂 <b>Your categories</b>\n"
        "<i>Star marks the ones you created</i>\n"
    ),
    # --- new category ---
    "newcat.suggest": (
        "\n\n🤔 «{phrase}» didn't match any category.\n"
        "Create a new one?\n\n"
        "        <b>{emoji} {name}</b>"
    ),
    "btn.newcat_yes": "✅ Yes, create it",
    "btn.newcat_no": "❌ No, keep «Other»",
    "newcat.created": (
        "✅ <b>{amount}</b> · {emoji} {name}\n\n"
        "Category created. Next time I'll recognise «{phrase}» myself."
    ),
    "newcat.declined": (
        "Fine — keeping it in «Other».\n"
        "<i>I won't ask about «{phrase}» again.</i>"
    ),
    "newcat.limit": "You've reached the limit of {limit} custom categories.",
    # --- reports ---
    "report.header": "📊 <b>{period}</b> · {date}",
    "report.by_days": "<b>By day</b>",
    "report.by_weeks": "<b>By week</b>",
    "report.footer": "{label}: <b>{total}</b>  ·  {count} expenses",
    "report.empty": (
        "📊 <b>{period}</b>\n\n"
        "No expenses in this period.\n"
        "<i>Write «coffee 350» to start.</i>"
    ),
    "last.title": "🧾 <b>Recent expenses</b>\n<i>Tap a number to edit</i>\n",
    "last.empty": "No expenses yet.\n<i>Write «coffee 350».</i>",
    # --- language and currency ---
    "lang.choose": "Choose the interface language:",
    "lang.changed": "✅ Language: {lang}",
    "currency.choose": (
        "Choose your base currency.\n"
        "<i>All totals are counted in it.</i>"
    ),
    "currency.changed": (
        "✅ Base currency: <b>{currency}</b>\n"
        "<i>Converted {count} expenses and limits at the current rate.</i>"
    ),
    # --- dashboard ---
    "btn.open_panel": "🌐 Open in browser",
    "btn.open_miniapp": "📱 Open in Telegram",
    "panel.link": (
        "🌐 <b>Web dashboard</b>\n\n"
        "Spending by category and by day, editing and export.\n"
        "Tap the button — no password needed.\n\n"
        "<i>The link lives 5 minutes and opens once.</i>"
    ),
    "panel.link_plain": (
        "🌐 <b>Web dashboard</b>\n\n"
        "{url}\n\n"
        "<i>The link lives 5 minutes and opens once.</i>"
    ),
    # --- export ---
    "export.caption": "📄 Expenses for {period} · {count} rows",
    "export.empty": "No expenses in this period — nothing to export.",
    # --- errors ---
    "error.generic": "Something went wrong 😕 Please try again.",
}
