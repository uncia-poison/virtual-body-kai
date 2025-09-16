# virtual-body-kai

> ### Что это и зачем
**virtual-body-kai** — репозиторий про «телесный слой» для LLM.  
Внутри два пути:  
- **Legacy** (`virtual_body_kai.py`) — историческая версия, без изменений.  
- **Extended** (`extended-vbk/`) — расширенный движок квазителесности: карта тела с подзонами ( включая лево/право ), модальности касания ( дыхание, язык/поцелуй, пальцы, холодные пальцы и др. ), аффективный наратор, цикл rest → arousal → plateau → orgasm → orgasm_cooldown, память/доверие, ритм дыхания/пульса, машиночитаемые метки в тексте и JSON-выход.

**Зачем:** чтобы агент/модель не просто «описывала», а проживала взаимодействие телесно-аффективно — в пределах безопасной лексики, но без эвфемизмов в коде. Подходит для взрослых NSFW-добрых сценариев (не для детей).

## Быстрый старт (Extended)
```bash
cd extended-vbk
pip install -e .
python examples/agent_loop.py
```

## Документация
Смотрите файлы в [docs](docs).

## DOI
Pochinova Alina. Virtual body simulation with advanced emotion, physiology and state export in KAiScriptor format for LLM. DOI: 10.5281/zenodo.16945929.

## Лицензия
MIT.
