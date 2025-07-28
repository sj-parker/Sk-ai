# VRM Models Directory

Поместите ваши VRM модели в эту папку.

## Требования к VRM модели

### Рекомендуемые morph targets для эмоций:
- `A` - открытие рта (для липсинка)
- `happy` - счастливое выражение
- `sad` - грустное выражение
- `angry` - злое выражение
- `surprised` - удивленное выражение

### Рекомендуемые кости для анимаций:
- `Head` - голова (для анимаций головы)
- `LeftUpperArm`, `RightUpperArm` - руки (для жестов)

## Настройка

1. Поместите вашу VRM модель в эту папку
2. Обновите путь в `config.yaml`:
   ```yaml
   VRM_OVERLAY:
     model_path: '/static/models/your_model.vrm'
   ```

## Примеры VRM моделей

Вы можете найти бесплатные VRM модели на:
- [VRoid Studio](https://vroid.com/en/studio) - создание моделей
- [VRM Hub](https://hub.vroid.com/) - готовые модели
- [Booth.pm](https://booth.pm/) - японский маркетплейс

## Тестирование

После добавления модели:
1. Запустите веб-сервер: `python web_overlay/web_server.py`
2. Откройте: `http://localhost:5000/test-vrm`
3. Протестируйте оверлей: `http://localhost:5000/vrm` или `http://localhost:5000/vrm-advanced` 