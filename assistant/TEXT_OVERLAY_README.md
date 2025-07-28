# Настройка текстового overlay

## Обзор

Текстовый overlay отображает ответы ассистента в реальном времени. Все настройки вынесены в конфигурационный файл `config.yaml`.

## Основные настройки

### Позиционирование

```yaml
TEXT_OVERLAY:
  position:
    bottom: 10vh    # Отступ снизу (или top: 10vh для верхней части)
    left: 50%       # Позиция по горизонтали
    transform: translateX(-50%)  # CSS transform (опционально)
```

### Размеры

```yaml
TEXT_OVERLAY:
  size:
    font_size: 2.5em      # Размер шрифта
    max_width: 90vw       # Максимальная ширина
    padding: 0.5em 1.5em  # Внутренние отступы
```

### Мобильные устройства

```yaml
TEXT_OVERLAY:
  mobile:
    font_size: 1.2em      # Размер шрифта для мобильных
    padding: 0.3em 0.7em  # Отступы для мобильных
```

### Поведение обновлений

```yaml
TEXT_OVERLAY:
  update_min_chars: 50        # Минимум символов для обновления
  update_on_punctuation: true # Обновлять при знаках препинания
  fade_duration_ms: 100       # Длительность анимации
```

## Примеры конфигураций

### Стандартная (по центру снизу)
```yaml
TEXT_OVERLAY:
  position:
    bottom: 10vh
    left: 50%
  size:
    font_size: 2.5em
    max_width: 90vw
    padding: 0.5em 1.5em
```

### Верхняя часть экрана
```yaml
TEXT_OVERLAY:
  position:
    top: 10vh
    left: 50%
  size:
    font_size: 2.5em
    max_width: 90vw
    padding: 0.5em 1.5em
```

### Левая часть экрана
```yaml
TEXT_OVERLAY:
  position:
    bottom: 10vh
    left: 10%
    transform: none
  size:
    font_size: 2em
    max_width: 40vw
    padding: 0.5em 1em
```

### Правая часть экрана
```yaml
TEXT_OVERLAY:
  position:
    bottom: 10vh
    left: 90%
    transform: translateX(-100%)
  size:
    font_size: 2em
    max_width: 40vw
    padding: 0.5em 1em
```

### Большой размер для больших экранов
```yaml
TEXT_OVERLAY:
  position:
    bottom: 15vh
    left: 50%
  size:
    font_size: 3.5em
    max_width: 80vw
    padding: 0.8em 2em
```

## Настройки производительности

### Быстрые обновления (больше нагрузка)
```yaml
TEXT_OVERLAY:
  update_min_chars: 20
  update_on_punctuation: true
  fade_duration_ms: 50
```

### Медленные обновления (меньше нагрузка)
```yaml
TEXT_OVERLAY:
  update_min_chars: 100
  update_on_punctuation: false
  fade_duration_ms: 200
```

## Тестирование

Для тестирования различных конфигураций используйте:
- `http://192.168.1.4:31991/test-text-overlay` - тестовая страница
- `http://192.168.1.4:31991/text` - текстовый overlay

## Доступные единицы измерения

- **vh** - высота viewport (10vh = 10% высоты экрана)
- **vw** - ширина viewport (90vw = 90% ширины экрана)
- **em** - размер шрифта (2.5em = 2.5 раза больше базового шрифта)
- **%** - проценты от родительского элемента
- **px** - пиксели

## CSS Transform

Доступные значения для `transform`:
- `translateX(-50%)` - центрирование по горизонтали
- `translateX(-100%)` - выравнивание по правому краю
- `none` - без трансформации
- `translateY(-50%)` - центрирование по вертикали
- `translate(-50%, -50%)` - центрирование по обеим осям 