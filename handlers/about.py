from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("about"))
async def about_handler(message: Message):
    text = (
        "⚡ О боте и юнит-системе\n\n"
        
        "Этот бот помогает вести учет домашних дел с использованием юнит-системы, где каждая выполненная задача оценивается в баллах (юнитах).\n\n"

        "⚠ Важно! Юнит-система — это не волшебное решение, которое само по себе наведет порядок. "
        "Ее эффективность зависит от честности и ответственности участников. "
        "Каждый член группы должен признавать свои успехи и недочеты, а также нести ответственность за невыполненные задачи.\n\n"
        
        "Особенно это касается общего баланса группы: если он уходит в минус, игнорирование проблемы приведет "
        "к снижению мотивации и разрушению системы. Поэтому важно заранее определить механизмы ответственности — будь то "
        "дополнительные задания, бонусы за перевыполнение или другие стимулы, которые помогут сохранить баланс между свободой и обязанностями.\n\n"

        "🔹 Основные термины юнит-системы\n\n"

        "📌 Спринт – период учета задач, в течение которого участники выполняют дела и накапливают юниты.\n"
        "▪ При создании группы задается день начала спринта и его длительность (по умолчанию: понедельник, 7 дней).\n"
        "▪ В конце каждого спринта бот подводит итоги и перераспределяет юниты.\n\n"

        "📌 Личный баланс – счет каждого участника группы.\n"
        "▪ Позволяет “запасать” юниты и использовать их в последующих спринтах, например, чтобы компенсировать невыполненные задачи.\n"
        "▪ Участники могут переводить юниты друг другу по договоренности.\n\n"

        "📌 Общий баланс группы – фонд, который накапливает юниты всех участников.\n"
        "▪ Может использоваться для групповых поощрений (например, накопили 100 юнитов – купили себе день отдыха).\n"
        "▪ В будущем появится магазин бенефитов внутри группы, где юниты можно будет тратить на приятные бонусы.\n\n"

        "📌 Распределение нагрузки – система, определяющая, кто и сколько должен выполнить задач.\n"
        "▪ При создании группы автоматически распределяется нагрузка поровну, но администратор может изменить проценты вручную.\n\n"

        "📌 Санкции за невыполнение плана\n"
        "▪ Если группа не выполняет минимальный объем задач, юниты списываются с баланса группы.\n"


        "🔹 Как работает бот?\n\n"

        "1️⃣ Создание или присоединение к группе\n"
        "▪ Можно создать свою группу или войти в существующую (по паролю).\n"
        "▪ В настройках группы указываются день начала учета, длительность спринта и правила распределения нагрузки.\n\n"

        "2️⃣ Добавление и выполнение задач\n"
        "▪ Задачи можно загрузить списком (Excel/CSV) или добавить вручную.\n"
        "▪ Каждая задача имеет стоимость в юнитах и частоту выполнения (например, “помыть полы – 3 раза в неделю, 5 юнитов за раз”).\n"
        "▪ Чтобы выполнить задачу, пользователь выбирает ее и отправляет подтверждение.\n"
        "▪ Партнеры проверяют выполнение, чтобы юниты были зачислены.\n\n"

        "3️⃣ Подведение итогов\n"
        "▪ В день окончания спринта бот анализирует выполненные задачи и начисляет/списывает юниты.\n"
        "▪ Общий баланс группы увеличивается, если план выполнен. Если нет – начисляется штраф.\n"
        "▪ Каждый участник получает отчет с личными результатами.\n\n"

        "4️⃣ Работа с балансом\n"
        "▪ Можно переводить юниты другим участникам.\n"

        "🎯 Зачем использовать юнит-систему?\n"
        "✔ Четкое и справедливое распределение обязанностей.\n"
        "✔ Исключение конфликтов на тему “кто сколько сделал”.\n"
        "✔ Видимость вклада каждого участника.\n"
        "✔ Мотивация выполнять задачи вовремя.\n\n"

        "🔹 Основные команды бота:\n"
        "🔹 /help – список всех доступных команд.\n"
        "🔹 /group_info – информация о текущей группе.\n"
        "🔹 /tasks – список задач на текущий спринт.\n"
        "🔹 /add_task – добавить задачу вручную или загрузить список.\n"
        "🔹 /temp_results – промежуточные итоги спринта (показывает список выполненных задач, накопленные юниты и прогресс плана в виде полоски).\n"
        "🔹 /balance – просмотр личного баланса.\n\n"

        "🚀 Настраивайте, мотивируйте и добивайтесь порядка в домашних делах с юнит-системой!"
    )

    await message.answer(text)