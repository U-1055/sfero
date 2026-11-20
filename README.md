# sfero


# Контракт

# API-контракт системы групповых закупок (v1)

## 1. Общие соглашения

| Параметр | Значение |
|---|---|
| **Base URL** | `/api/v1` |
| **Формат** | JSON, `Content-Type: application/json` |
| **Аутентификация** | `Authorization: Bearer <jwt>` |
| **Идемпотентность** | Заголовок `Idempotency-Key: <uuid>` для всех мутаций, влияющих на платежи/состояние группы |
| **Трассировка** | Клиент может передать `X-Request-ID`; если нет — сервер генерирует и возвращает в ответе |
| **Пагинация** | `?page=1&page_size=20` |
| **Время** | ISO-8601 с UTC (`2026-11-20T15:00:00Z`)|

---

## 2. Единый формат ответа

### Успех
```json
{
  "request_id": "req_a1b2c3d4e5f6",
  "data": { ... }
}
```

### Ошибка
```json
{
  "request_id": "req_a1b2c3d4e5f6",
  "error": {
    "code": "GROUP_DEADLINE_EXCEEDED",
    "message": "Срок закупки истёк в момент обработки платежа",
    "details": {
      "group_id": 101,
      "deadline": "2026-11-25T18:00:00Z"
    }
  }
}
```

---

## 3. Справочник `error_code`

Это стабильный контракт между бэкендом и фронтендом. Текст `message` можно менять/переводить — фронтенд реагирует на `code`.

### 3.1. Общие (4xx)

| HTTP | error_code | Ситуация | Действие фронтенда |
|---|---|---|---|
| 400 | `VALIDATION_ERROR` | Неверный формат полей | Показать валидацию у поля |
| 400 | `PRICE_MISMATCH` | Цена изменилась между экраном и оплатой | Обновить цену, запросить подтверждение |
| 401 | `UNAUTHORIZED` | Нет/протух токен | Редирект на логин |
| 403 | `FORBIDDEN` | Действие не для этой роли (не организатор) | Показать «нет доступа» |
| 404 | `NOT_FOUND` | Закупка/товар не найдены | 404-страница |
| 409 | `GROUP_ALREADY_FULL` | Группа только что набралась | «Группа заполнилась — создать свою?» |
| 409 | `GROUP_DEADLINE_EXCEEDED` | Дедлайн прошёл | «Время вышло, средства не списаны» |
| 409 | `ALREADY_PARTICIPANT` | Повторное вступление | Обновить UI |
| 409 | `IDEMPOTENCY_KEY_USED` | Дубликат запроса | Вернуть результат оригинала |
| 409 | `GROUP_ALREADY_SUCCESS` | Группа уже успешна, оплата невозможна | Показать статус «Успешна» |
| 409 | `GROUP_CANCELLED` | Закупка отменена | Показать причину отмены |
| 429 | `RATE_LIMIT_EXCEEDED` | Слишком много запросов | «Подождите несколько секунд» |
| 500 | `INTERNAL_ERROR` | Непредвиденная ошибка | «Сообщите код ошибки поддержке» |

### 3.2. Платежи

| HTTP | error_code | Ситуация | Действие фронтенда |
|---|---|---|---|
| 400 | `INSUFFICIENT_BALANCE` | Не хватает тестовых средств | «Пополните баланс» |
| 409 | `PAYMENT_ALREADY_EXISTS` | Платёж по этому участнику уже есть | Показать существующий платёж |
| 409 | `PAYMENT_REFUND_IN_PROGRESS` | Уже идёт возврат | «Возврат обрабатывается» |

---

## 4. Эндпоинты

### 4.1. Аутентификация

#### `POST /auth/register`
```json
// Request
{ "email": "user@mail.com", "phone": "+7...", "name": "Иван", "password": "..." }

// Response 201
{ "request_id": "...", "data": { "id": 1, "email": "user@mail.com", "name": "Иван", "balance": "0.00" } }
```

#### `POST /auth/login`
```json
// Request
{ "email": "user@mail.com", "password": "..." }

// Response 200
{ "request_id": "...", "data": { "access_token": "...", "refresh_token": "...", "expires_in": 3600 } }
```

#### `GET /users/me`
```json
// Response 200
{
  "request_id": "...",
  "data": {
    "id": 1, "email": "user@mail.com", "name": "Иван", "balance": "150.00",
    "stats": { "organized_groups": 3, "participated_groups": 7 }
  }
}
```

---

### 4.2. Витрина товаров

#### `GET /products?page=1&page_size=20`
```json
// Response 200
{
  "request_id": "...",
  "data": {
    "items": [
      {
        "id": 10,
        "name": "Кофемашина X",
        "description": "...",
        "regular_price": "15000.00",
        "min_group_price": "10500.00",
        "max_discount_percent": "30.00",
        "pricing_tiers": [
          { "min_participants": 3, "group_price": "13500.00", "discount_percent": "10.00" },
          { "min_participants": 5, "group_price": "12000.00", "discount_percent": "20.00" },
          { "min_participants": 10, "group_price": "10500.00", "discount_percent": "30.00" }
        ]
      }
    ],
    "pagination": { "page": 1, "total": 42, "pages": 3 }
  }
}
```

#### `GET /products/{product_id}`
Детальная карточка + список активных закупок по этому товару (для UX «присоединиться к существующей»).

---

### 4.3. Групповые закупки (ядро)

#### `POST /group-buys` ⚠️ Идемпотентно
```json
// Headers: Idempotency-Key: 550e8400-...
// Request
{ "product_id": 10, "required_participants": 5, "deadline": "2026-11-25T18:00:00Z" }

// Response 201
{
  "request_id": "...",
  "data": {
    "id": 101, "product_id": 10, "organizer_id": 1,
    "invite_code": "GRP-ABC123",
    "invite_link": "https://app.t-shopping.ru/join/GRP-ABC123",
    "status": "active",
    "deadline": "2026-11-25T18:00:00Z",
    "current_participants": 1,
    "required_participants": 5,
    "current_price": "12000.00",
    "created_at": "2026-11-20T14:30:00Z"
  }
}
```
**Валидация:** `deadline` ≥ now + 1 час, `required_participants` ≥ 2.

#### `GET /group-buys/{group_id}`
```json
// Response 200
{
  "request_id": "...",
  "data": {
    "id": 101,
    "product": { "id": 10, "name": "Кофемашина X", "regular_price": "15000.00" },
    "organizer": { "id": 1, "name": "Иван" },
    "status": "active",
    "deadline": "2026-11-25T18:00:00Z",
    "current_participants": 3,
    "required_participants": 5,
    "current_price": "12000.00",
    "next_tier": { "min_participants": 5, "group_price": "12000.00", "participants_left": 2 },
    "participants_preview": [
      { "name": "Иван", "is_organizer": true, "paid": true },
      { "name": "Мария", "is_organizer": false, "paid": true },
      { "name": "Пётр", "is_organizer": false, "paid": false }
    ],
    "my_participation": null
  }
}
```

#### `POST /group-buys/{group_id}/join` ⚠️ Идемпотентно
```json
// Headers: Idempotency-Key: ...
// Response 200
{
  "request_id": "...",
  "data": {
    "participant_id": 501, "status": "joined",
    "current_price": "12000.00", "locked_price": null,
    "deadline": "2026-11-25T18:00:00Z"
  }
}
```
**Ошибки:** `409 GROUP_FULL`, `409 GROUP_DEADLINE_EXCEEDED`, `409 ALREADY_PARTICIPANT`.

#### `GET /group-buys?page=1&status=active&sort=deadline_asc`
Список закупок с фильтрацией.

---

### 4.4. Платежи (критично для жюри)

#### `POST /group-buys/{group_id}/pay` ⚠️ Идемпотентно + фиксирует цену
```json
// Headers: Idempotency-Key: ..., X-Client-Timestamp: 2026-11-20T15:00:00Z
// Request
{ "payment_method": "test_card", "amount": "12000.00" }

// Response 201
{
  "request_id": "...",
  "data": {
    "payment_id": 1001, "status": "success",
    "amount": "12000.00",
    "locked_price": "12000.00",
    "participant_status": "paid",
    "processed_at": "2026-11-20T15:00:01Z"
  }
}
```

**Ключевые проверки бэкенда (пограничные случаи из ТЗ):**
1. Дедлайн истёк во время обработки → `409 GROUP_DEADLINE_EXCEEDED`, деньги не списаны
2. Группа уже набрана → `409 GROUP_ALREADY_FULL`
3. `amount` ≠ текущей цене → `400 PRICE_MISMATCH` с актуальной ценой в `details`
4. Повторный `Idempotency-Key` → `409 IDEMPOTENCY_KEY_USED`, возвращается оригинальный платёж (200)
5. Параллельные оплаты → `SELECT ... FOR UPDATE` на группу, только один проходит

#### `POST /payments/{payment_id}/refund`
Админский/автоматический возврат. Для MVP используется внутренним cron-процессом при отмене группы.

---

### 4.5. Личный кабинет

#### `GET /users/me/groups?role=all&status=success`
```json
// Response 200
{
  "request_id": "...",
  "data": {
    "items": [
      {
        "group_id": 101, "role": "organizer",
        "product": { "id": 10, "name": "Кофемашина X" },
        "status": "success",
        "my_locked_price": "12000.00",
        "participants_count": 5,
        "reward": { "type": "cashback", "amount": "12000.00", "status": "credited" },
        "deadline": "2026-11-25T18:00:00Z",
        "completed_at": "2026-11-24T10:00:00Z"
      }
    ],
    "pagination": { ... }
  }
}
```

#### `GET /users/me/payments`
История платежей и возвратов.

---

### 4.6. WebSocket (доп. фича для баллов)

#### `WS /ws/group-buys/{group_id}`
Real-time обновления страницы закупки.

**Сервер → клиент:**
```json
{ "event": "participant_joined", "data": { "count": 4, "new_price": "12000.00" } }
{ "event": "price_tier_changed", "data": { "new_price": "10500.00", "discount": "30%" } }
{ "event": "group_status_changed", "data": { "status": "success" } }
{ "event": "group_expired", "data": { "status": "cancelled", "refund_initiated": true } }
{ "event": "deadline_approaching", "data": { "seconds_left": 300 } }
```

---

### 4.7. Наблюдаемость (для Backend-жюри)

#### `GET /health`
```json
{ "status": "ok", "db": "ok", "redis": "ok", "version": "1.2.3" }
```

#### `GET /admin/metrics` (Prometheus-совместимый)
```json
{
  "active_groups": 42,
  "successful_groups_24h": 18,
  "cancelled_groups_24h": 7,
  "total_payments_volume_24h": "245000.00",
  "avg_group_fill_rate": 0.78,
  "p95_join_latency_ms": 120
}
```

---

## 5. Полный Happy Path (для демонстрации жюри)

1. `GET /products` → пользователь видит товар с двумя ценами
2. `POST /group-buys` → создаёт закупку, получает `invite_link`
3. Другой пользователь: `POST /group-buys/{id}/join` → присоединяется
4. `POST /group-buys/{id}/pay` с `Idempotency-Key` → оплачивает, цена фиксируется в `locked_price`
5. `WS /ws/group-buys/{id}` → все видят обновление прогресса в реальном времени
6. При достижении `required_participants` → бэкенд меняет статус на `success`, начисляет вознаграждение организатору
7. `GET /users/me/groups` → все видят статус «Успешна» в истории
8. **Демонстрация пограничного случая:** параллельно отправляем два `POST /pay` с разными `Idempotency-Key` → только один проходит, второй получает `409 GROUP_ALREADY_FULL`

---

## 6. Что этот контракт даёт по критериям жюри

| Критерий | Как закрывается |
|---|---|
| **Архитектура и готовность к релизу** (Backend) | Единый контракт, идемпотентность, обработка конкурентных операций через 409 + разные `error_code` |
| **Наблюдаемость и диагностика** (Backend) | `request_id` во всех ответах + `/admin/metrics` для Grafana |
| **Техническая оригинальность** (Backend) | WebSocket real-time + атомарные операции с `SELECT FOR UPDATE` |
| **Интерфейс стабилен и согласован с бекендом** (Frontend) | Фронтенд реагирует на `error_code`, а не парсит текст |
| **Проработанность бизнес-сценариев** (Продакт) | Все пограничные случаи из ТЗ закрыты конкретными кодами ошибок |
| **Минимальный набор MVP** (штраф -30%) | Все 6 критериев готовности явно покрыты эндпоинтами |

Готов детализировать любой раздел (например, схему БД под этот контракт, примеры middleware для `request_id` и идемпотентности, или OpenAPI-спецификацию в YAML).
