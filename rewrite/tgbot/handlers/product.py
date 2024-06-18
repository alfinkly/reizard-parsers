from aiogram import Router
from aiogram.types import CallbackQuery

from database.database import ORM

router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith('category:'))
async def process_category_selection(callback: CallbackQuery, callback_data: CallbackQuery, orm: ORM):
    category_name = callback_data.data

    products = await orm.product_repo.select_site_products(1)

    message_text = f"Продукты в категории '{category_name}':\n"
    message_text += "\nArbuz:\n" + "\n".join([prod['name'] for prod in await orm.product_repo.select_site_products(1)])
    message_text += "\n\nClever:\n" + "\n".join(
        [prod['name'] for prod in await orm.product_repo.select_site_products(2)])
    # message_text += "\n\nKaspi:\n" + "\n".join([prod['name'] for prod in await
    # orm.product_repo.select_site_products(3)])

    await callback.bot.send_message(callback.from_user.id, message_text)
    await callback.answer()



@router.callback_query_handler(text='share_contact')
async def prompt_for_contact(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    # Отправляем пользователю инструкцию, как поделиться контактом
    await bot.send_message(callback_query.from_user.id,
                           "Пожалуйста, отправьте ваш контакт через прикрепление -> Контакт.")
    # Удаляем исходное сообщение с кнопкой
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)


@router.message_handler(content_types=['contact'], state='*')
async def contact_received(message: types.Message, state: FSMContext):
    contact = message.contact
    await db['user_contacts'].update_one(
        {'user_id': message.from_user.id},
        {'$set': {'phone_number': contact.phone_number, 'first_name': contact.first_name,
                  'last_name': contact.last_name}},
        upsert=True
    )

    await message.answer("Спасибо за предоставленную информацию!", reply_markup=types.ReplyKeyboardRemove())

    # После получения контакта, предлагаем выбрать категорию
    markup = await category_keyboard()
    await message.answer("Выберите категорию:", reply_markup=markup)
    await ProductSearch.choosing_category.set()


async def show_products(message: types.Message, state: FSMContext, page: int = 0):
    data = await state.get_data()
    matched_products = data.get('matched_products', [])
    # sent_products теперь используется для кэширования товаров, отправленных на каждой странице
    page_cache = data.get('page_cache', {})
    sent_products = data.get('sent_products', set())  # Общий кэш отправленных товаров
    last_message_ids = data.get('last_message_ids', [])

    items_per_page = 5
    total_pages = (len(matched_products) + items_per_page - 1) // items_per_page

    if page in page_cache:
        # Извлекаем товары из кэша страницы, если уже просматривали эту страницу
        page_products = page_cache[page]
    else:
        # Выбираем товары для текущей страницы, если впервые на ней
        start_index = page * items_per_page
        end_index = start_index + items_per_page
        page_products = []
        for prod in matched_products[start_index:end_index]:
            arbuz_id = prod[0]['_id'] if prod[0] else None
            klever_id = prod[1]['_id'] if prod[1] else None
            kaspi_id = prod[2]['_id'] if len(prod) > 2 and prod[2] else None

            # Проверяем, не был ли товар уже отправлен
            if not any(pid in sent_products for pid in [arbuz_id, klever_id, kaspi_id]):
                page_products.append(prod)
                # Добавляем ID отправленных товаров в общий кэш
                if arbuz_id: sent_products.add(arbuz_id)
                if klever_id: sent_products.add(klever_id)
                if kaspi_id: sent_products.add(kaspi_id)

        # Кэшируем товары текущей страницы
        page_cache[page] = page_products

    if not page_products:
        await message.answer("Товары не найдены или вы достигли конца списка.")
        return

    for product_pair in page_products:
        arbuz_product, klever_product, kaspi_product = product_pair if len(product_pair) > 2 else (
            product_pair[0], product_pair[1], None)
        arbuz_text, klever_text, kaspi_text, image_url = format_message(arbuz_product, klever_product,
                                                                        kaspi_product)  # Обновите функцию format_message
        text = arbuz_text + "\n" + klever_text + "\n" + kaspi_text  # Добавление текста для "Каспий"

        markup = InlineKeyboardMarkup(row_width=2)
        if arbuz_product and klever_product:
            product_id = arbuz_product.get('_id', klever_product.get('_id', 'unknown'))
            markup.add(
                InlineKeyboardButton("Соответствует", callback_data=f"match:{product_id}"),
                InlineKeyboardButton("Не соответствует", callback_data=f"nomatch:{product_id}")
            )

        try:
            if image_url and image_url.startswith('http'):
                sent_message = await message.bot.send_photo(chat_id=message.chat.id, photo=image_url, caption=text,
                                                            reply_markup=markup)
            else:
                raise ValueError("Invalid image URL")
        except Exception as e:
            print(f"Ошибка при отправке изображения: {e}. Отправляю сообщение без изображения.")
            sent_message = await message.answer(text, reply_markup=markup)

        # Добавляем ID отправленного товара в список отправленных
        if arbuz_product:
            sent_products.add(arbuz_product['_id'])
        if klever_product:
            sent_products.add(klever_product['_id'])

        last_message_ids.append(sent_message.message_id)

    await state.update_data(page_cache=page_cache, sent_products=sent_products, last_message_ids=last_message_ids)

    navigation_markup = InlineKeyboardMarkup(row_width=2)
    if page > 0:
        navigation_markup.insert(InlineKeyboardButton("⬅ Назад", callback_data=f"page:{page - 1}"))
    if page + 1 < total_pages:
        navigation_markup.insert(InlineKeyboardButton("Вперед ➡", callback_data=f"page:{page + 1}"))

    navigation_markup.insert(InlineKeyboardButton("🔍 Инлайн-поиск", switch_inline_query_current_chat=""))

    navigation_message = await message.answer("Перейдите на следующую страницу или используйте инлайн-поиск:",
                                              reply_markup=navigation_markup)
    last_message_ids.append(navigation_message.message_id)

    # Обновляем состояние с новым списком ID отправленных сообщений и товаров
    await state.update_data(page_cache=page_cache, sent_products=sent_products, last_message_ids=last_message_ids)


@router.inline_handler(state='*')
async def inline_query_handler(inline_query: types.InlineQuery, state: FSMContext):
    # Сохраняем текущее состояние пользователя и его данные
    current_state = await state.get_state()
    user_data = await state.get_data()

    # Сбрасываем состояние пользователя для обработки инлайн-запроса
    await state.finish()

    query = inline_query.query.strip()
    results = []

    if query:
        try:
            # Использование индекса `name_text` для ускорения поиска
            projection = {'_id': True, 'name': True, 'price': True, 'image_url': True, 'link': True}
            search_results_arbuz = await arbuz_collection.find(
                {'$text': {'$search': query}},
                projection
            ).sort('name', pymongo.ASCENDING).limit(10).to_list(None)
            search_results_klever = await klever_collection.find(
                {'$text': {'$search': query}},
                projection
            ).sort('name', pymongo.ASCENDING).limit(10).to_list(None)

            # Объединение результатов из обеих коллекций
            combined_results = search_results_arbuz + search_results_klever
            unique_results = {result['name']: result for result in combined_results}.values()

            for result in unique_results:
                full_url = result["link"]
                if not full_url.startswith('http'):
                    full_url = 'https://arbuz.kz' + full_url
                photo_url = result["image_url"]
                title = result['name']
                price = result['price']

                keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton(text="Подробнее", url=full_url))

                results.append(
                    InlineQueryResultArticle(
                        id=str(result['_id']),
                        title=title,
                        input_message_content=InputTextMessageContent(
                            message_text=f"<b>{title}</b>\nЦена: {price}\n<a href='{full_url}'>Ссылка на товар</a>",
                            parse_mode=types.ParseMode.HTML
                        ),
                        reply_markup=keyboard,
                        thumb_url=photo_url,
                        description=f"Цена: {price}"
                    )
                )
        except Exception as e:
            # Отправляем сообщение в случае ошибки
            await inline_query.answer(
                results=[],
                cache_time=1,
                switch_pm_text="Произошла ошибка при поиске, попробуйте позже.",
                switch_pm_parameter="start"
            )
            return

    # Обрезаем до 20 результатов для ответа
    results = results[:20]
    if current_state is not None:
        await state.set_state(current_state)
        await state.set_data(user_data)

    # Отправляем результаты пользователю
    await bot.answer_inline_query(inline_query.id, results=results, cache_time=1)


button_states = {}  # Ключ: (user_id, product_id), Значение: 'match' или 'nomatch'


async def update_clicks(user_id, product_id, product_name, product_url, click_type, callback_query):
    # Обновляем состояние кнопок в хранилище
    button_states[(user_id, product_id)] = click_type

    collection = db['product_clicks']
    user_field = f"{click_type}_users"
    await collection.update_one(
        {"product_id": product_id},
        {"$set": {"product_name": product_name, "product_url": product_url},
         "$inc": {f"{click_type}_clicks": 1},
         "$addToSet": {user_field: user_id}},
        upsert=True
    )
    doc = await collection.find_one({"product_id": product_id})
    if doc:
        message = f"Товар '{product_name}' ({product_id}) был отмечен как {'соответствует' if click_type == 'match' else 'не соответствует'}. Текущее количество кликов: {doc[click_type + '_clicks']}."
        await bot.send_message(ADMIN_CHAT_ID, message)
        await callback_query.message.copy_to(ADMIN_CHAT_ID)

    # Обновляем сообщение с кнопками
    await refresh_message_buttons(callback_query, product_id)


async def refresh_message_buttons(callback_query: types.CallbackQuery, product_id: str):
    user_id = callback_query.from_user.id
    state = button_states.get((user_id, product_id), None)

    # Настраиваем текст кнопок в зависимости от состояния
    match_button_text = "✅ Соответствует" if state == "match" else "Соответствует"
    nomatch_button_text = "✅ Не соответствует" if state == "nomatch" else "Не соответствует"

    markup = InlineKeyboardMarkup(row_width=2)
    match_button = InlineKeyboardButton(match_button_text, callback_data=f"match:{product_id}")
    nomatch_button = InlineKeyboardButton(nomatch_button_text, callback_data=f"nomatch:{product_id}")
    markup.add(match_button, nomatch_button)

    # Обновляем сообщение с новой разметкой кнопок
    await callback_query.message.edit_reply_markup(reply_markup=markup)


@router.callback_query_handler(lambda c: c.data.startswith("match:"), state=ProductSearch.viewing)
async def handle_match(callback_query: types.CallbackQuery, state: FSMContext):
    product_id = callback_query.data.split(':')[1]  # Извлекаем ID продукта
    # Здесь должен быть код для извлечения названия и ссылки продукта, пока используем заглушки
    product_name = "Product Name Placeholder"
    product_url = "http://example.com/placeholder"
    await update_clicks(callback_query.from_user.id, product_id, product_name, product_url, "match", callback_query)
    await callback_query.answer("Вы отметили товар как соответствующий.")


@router.callback_query_handler(lambda c: c.data.startswith('category:'), state='*')
async def process_category_selection(callback_query: types.CallbackQuery, state: FSMContext):
    # Парсим имя категории из callback_data
    category = callback_query.data.split(':')[1]
    await callback_query.answer()

    # Ищем товары в Арбузе
    arbuz_products = await arbuz_collection.find({'category': category}).to_list(None)

    # Используем category_mapping для поиска соответствующих категорий в Клевере и Каспий
    klever_categories = category_mapping.get(category, [])
    klever_products = []
    kaspi_products = []  # Инициализация списка товаров из Каспий
    for klever_category in klever_categories:
        klever_products.extend(await klever_collection.find({'category': klever_category}).to_list(None))
        # Допустим, что категории для Каспий те же, что и для Клевер. Если это не так, необходимо настроить соответствующее отображение
        kaspi_products.extend(await kaspi_collection.find({'category': klever_category}).to_list(None))

    # Проверяем, есть ли уже сравнения для данной категории в кэше
    if category not in matched_products_cache:
        # Теперь передаем все три списка товаров в функцию
        matched_products = await find_matching_products(arbuz_products, klever_products, kaspi_products,
                                                        category_mapping)
        matched_products_cache[category] = matched_products

    # Сохраняем сравненные товары в состояние
    await state.update_data(matched_products=matched_products_cache[category])

    if matched_products_cache[category]:
        await show_products(callback_query.message, state)
    else:
        await callback_query.message.edit_text("Соответствующие товары не найдены.")


@router.callback_query_handler(lambda c: c.data.startswith("nomatch:"), state=ProductSearch.viewing)
async def handle_nomatch(callback_query: types.CallbackQuery, state: FSMContext):
    product_id = callback_query.data.split(':')[1]  # Извлекаем ID продукта
    user_id = callback_query.from_user.id  # ID пользователя, который нажал кнопку

    # Извлечение информации о продукте (здесь используется заглушка)
    product_name = "Product Name Placeholder"
    product_url = "http://example.com/placeholder"

    # Обновляем информацию о кликах
    await update_clicks(callback_query.from_user.id, product_id, product_name, product_url, "nomatch", callback_query)

    # Извлекаем номер телефона и имя пользователя из базы данных
    user_contact = await db['user_contacts'].find_one({'user_id': user_id})
    if user_contact:
        phone_number = user_contact.get('phone_number', 'Номер не предоставлен')
        first_name = user_contact.get('first_name', 'Имя не предоставлено')
        last_name = user_contact.get('last_name', '')

        # Составляем сообщение администратору
        admin_message = (
            f"Пользователь: {first_name} {last_name}\n"
            f"ID: {user_id}\n"
            f"Телефон: {phone_number}\n"
            f"Отметил товар как 'Не соответствует':\n"
            f"{product_name}\n"
            f"{product_url}"
        )
        await bot.send_message(ADMIN_CHAT_ID, admin_message)
    else:
        await bot.send_message(ADMIN_CHAT_ID, f"Пользователь с ID {user_id} не найден в базе данных.")

    await callback_query.answer("Вы отметили товар как не соответствующий.")


page_storage = {}


# Обработчик пагинации
@router.callback_query_handler(lambda c: c.data.startswith("page:"), state='*')
async def navigate_page(callback_query: types.CallbackQuery, state: FSMContext):
    page = int(callback_query.data.split(':')[1])

    # Получаем и обновляем данные пользователя
    data = await state.get_data()
    last_message_ids = data.get('last_message_ids', [])
    # Здесь добавьте логику для обновления данных пользователя, если необходимо

    # Удаляем предыдущие сообщения
    for message_id in last_message_ids:
        try:
            await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=message_id)
        except Exception as e:
            logger.error(f"Не удалось удалить сообщение с ID {message_id}: {e}")

    # Очищаем список ID в состоянии
    await state.update_data(last_message_ids=[])

    # Переходим к отображению продуктов на новой странице
    await show_products(callback_query.message, state, page)
    await callback_query.answer()


def generate_hash(link):
    hash_object = hashlib.md5(link.encode())
    return hash_object.hexdigest()[:10]  # Берем первые 10 символов для уменьшения размера


def format_message(arbuz_product=None, klever_product=None, kaspi_product=None, base_url_arbuz="https://arbuz.kz",
                   base_url_klever="https://klever.kz", base_url_kaspi="https://kaspi.kz"):
    arbuz_text = ""
    klever_text = ""
    kaspi_text = ""  # Текст для "Каспий"
    image_url = None

    if arbuz_product:
        # Формируем информацию о продукте из Арбуза
        arbuz_text = (
            f"Арбуз:\n"
            f"Название: {arbuz_product.get('name', 'Название отсутствует')}\n"
            f"Цена: {arbuz_product.get('price', 'Цена отсутствует')}\n"
            f"Категория: {arbuz_product.get('category', 'Категория отсутствует')}\n"
            f"Актуально на: {arbuz_product.get('parsed_time', 'Время не указано')}\n"
            f"Ссылка: {base_url_arbuz + arbuz_product.get('link', '')}\n"
        )
        image_url = arbuz_product.get('image_url', None)
    else:
        arbuz_text = "Соответствий в Арбузе не найдено.\n"

    if klever_product:
        # Формируем информацию о продукте из Клевера
        klever_text = (
            f"Клевер:\n"
            f"Название: {klever_product.get('name', 'Название отсутствует')}\n"
            f"Цена: {klever_product.get('price', 'Цена отсутствует')}\n"
            f"Категория: {klever_product.get('category', 'Категория отсутствует')}\n"
            f"Актуально на: {klever_product.get('parsed_time', 'Время не указано')}\n"
            f"Ссылка: {klever_product.get('link', '')}\n"
        )
        # Изображение товара из Клевера используется, если нет изображения из Арбуза
        image_url = image_url or klever_product.get('image_url', None)
    else:
        klever_text = "Соответствий в Клевере не найдено.\n"

    if kaspi_product:
        # Формируем информацию о продукте из Каспий
        kaspi_text = (
            f"Каспий:\n"
            f"Название: {kaspi_product.get('name', 'Название отсутствует')}\n"
            f"Цена: {kaspi_product.get('price', 'Цена отсутствует')}\n"
            f"Категория: {kaspi_product.get('category', 'Категория отсутствует')}\n"
            f"Актуально на: {kaspi_product.get('parsed_time', 'Время не указано')}\n"
            f"Ссылка: {kaspi_product.get('product_url', '')}\n"
        )
        # Изображение товара из Каспий используется, если нет изображения из других магазинов
        image_url = image_url or kaspi_product.get('image_url', None)
    else:
        kaspi_text = "Соответствий в Каспии не найдено.\n"

    return arbuz_text, klever_text, kaspi_text, image_url


@router.callback_query_handler(lambda c: c.data.startswith('page:'), state='*')
async def handle_page_change(callback_query: types.CallbackQuery, state: FSMContext):
    # Получаем номер страницы из callback данных
    page_number = int(callback_query.data.split(':')[1])

    # Попытка удалить предыдущее сообщение бота
    try:
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id)
    except Exception as e:
        logger.error(f"Не удалось удалить сообщение: {e}")

    # Показываем продукты на новой странице
    await show_products(callback_query.message, state, page=page_number)


@router.message_handler(state=ProductSearch.waiting_for_search_query)
async def process_search_query(message: types.Message, state: FSMContext):
    search_query = message.text.strip()
    if not search_query:
        await message.answer("Поисковый запрос не может быть пустым. Пожалуйста, введите название товара.")
        return

    # Выполнение поиска в коллекциях Арбуз и Клевер
    arbuz_products = await arbuz_collection.find({'$text': {'$search': search_query}}).to_list(length=100)
    klever_products = await klever_collection.find({'$text': {'$search': search_query}}).to_list(length=100)
    kaspi_products = await kaspi_collection.find({'$text': {'$search': search_query}}).to_list(length=100)

    # Поиск совпадений между двумя коллекциями
    matched_products = await find_matching_products(arbuz_products, klever_products, kaspi_products)

    # Проверяем, есть ли совпадающие товары
    if not matched_products:
        await message.answer("Товары по запросу не найдены.")
        await state.finish()
        return

    # Выводим информацию о первом совпадении
    # (Для упрощения предполагаем, что совпадения уже отсортированы по релевантности)
    arbuz_product, klever_product, kaspi_product = matched_products[0]

    # Обновляем вызов format_message, чтобы он теперь принимал три продукта
    arbuz_text, klever_text, kaspi_text, image_url = format_message(arbuz_product, klever_product, kaspi_product)

    # Формируем текст сообщения, включающий информацию из всех трех источников
    text = f"{arbuz_text}\n{klever_text}\n{kaspi_text}"

    # Отправляем результаты пользователю
    if image_url:
        await message.answer_photo(photo=image_url, caption=text)
    else:
        await message.answer(text)
    # Завершаем сессию состояния
    await state.finish()

    # Показать пользователю кнопки для перехода по страницам, если есть более одного совпадения
    if len(matched_products) > 1:
        # Создаем клавиатуру для перехода по страницам
        pagination_markup = InlineKeyboardMarkup()
        pagination_markup.add(InlineKeyboardButton("➡️ Следующий товар", callback_data='next_product:1'))
        await message.answer("Перейти к следующему товару:", reply_markup=pagination_markup)

        # Сохраняем все совпадения и текущую страницу в состояние
        await state.update_data(matched_products=matched_products, current_page=0)


@router.callback_query_handler(lambda c: c.data == 'back_to_categories', state='*')
async def handle_back_to_categories(callback_query: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await cmd_start(callback_query.message, state)


@router.callback_query_handler(lambda c: c.data == 'search_by_name', state='*')
async def prompt_search_query(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите название товара для поиска:")
    await ProductSearch.waiting_for_search_query.set()
    await callback_query.answer()
