# C1 — опубликованное соединение рычага с валом

Дата сверки: 2026-10-04. Рабочая ветка: `feature/qulay-prototype-20261002`.

Комплект C1 уже сохранён обычными файлами Git в коммите `1efd7f91b27130aefe04aaba4bcc40d3f5e481eb`. Настоящее обновление связывает его с главным README, разделом механики и пояснением отдельного tilt-канала. Модели не перегенерированы, геометрия и код измерений не изменены; новые аппаратные или программные испытания этим обновлением не заявляются.

## Что теперь определено

C1 заменяет историческую пару `A-xx / PS-xx` R1: цельный фланцевый вал Ø8/Ø24, два штифта Ø3 с заданной селективной посадкой и два прижимных винта M3. Передача момента не рассчитывается за счёт трения. Полные размеры, допуски, карта отверстий, требования к материалам, совместной обработке и стендовому контролю находятся в [описании C1](../mechanical/coupling_c1/README.md).

Фраза «окончательное соединение рычага с валом ещё не разработано» в исторических документах R1 заменяется для текущего узла следующим статусом: **конструкция определена, изготовление и физические испытания не выполнены**. Старые PDF и исходники R1 сохранены; их не следует трактовать как актуальные рабочие чертежи соединения.

## Прямые ссылки на файлы

| Назначение | Файл |
|---|---|
| Пояснение и три листа A3 | [Qulay_C1_Lever_Shaft_Coupling.pdf](../mechanical/coupling_c1/generated/Qulay_C1_Lever_Shaft_Coupling.pdf) |
| Только чертежи | [C1-drawings.pdf](../mechanical/coupling_c1/generated/C1-drawings.pdf) |
| Только пояснение | [C1-note.pdf](../mechanical/coupling_c1/generated/C1-note.pdf) |
| Сборка соединения | [C1-coupling.step](../mechanical/coupling_c1/generated/C1-coupling.step) |
| Разнесённая сборка | [C1-exploded.step](../mechanical/coupling_c1/generated/C1-exploded.step) |
| Цельный фланцевый вал | [C1-SHAFT.step](../mechanical/coupling_c1/generated/C1-SHAFT.step) |
| Полный рычаг | [C1-ARM.step](../mechanical/coupling_c1/generated/C1-ARM.step) |
| Контур и отверстия рычага | [C1-arm-finished-face.dxf](../mechanical/coupling_c1/generated/C1-arm-finished-face.dxf) |
| Карта отверстий фланца | [C1-flange-hole-map.dxf](../mechanical/coupling_c1/generated/C1-flange-hole-map.dxf) |
| Тележка, обычное положение | [Qulay-C1-crossing.step](../mechanical/coupling_c1/generated/Qulay-C1-crossing.step) |
| Тележка, вдоль бордюра | [Qulay-C1-along-curb.step](../mechanical/coupling_c1/generated/Qulay-C1-along-curb.step) |
| Тележка, направляющие | [Qulay-C1-datum-rail.step](../mechanical/coupling_c1/generated/Qulay-C1-datum-rail.step) |
| Состав соединения | [BOM.csv](../mechanical/coupling_c1/generated/BOM.csv) |
| Расчёт | [calculations.json](../mechanical/coupling_c1/generated/calculations.json) |
| Проверка пересечений | [verification.json](../mechanical/coupling_c1/generated/verification.json) |
| Контрольные суммы опубликованных файлов | [SHA256SUMS](../mechanical/coupling_c1/generated/SHA256SUMS) |

Штифты, винты, изображения, проверка документа и исходный commit также находятся в [каталоге generated](../mechanical/coupling_c1/generated). На момент сверки каталог содержит 26 файлов. Исходники — [build.py](../mechanical/coupling_c1/build.py) и [document.py](../mechanical/coupling_c1/document.py).

## Границы замены

Не смешивать головку старого рычага с новым фланцем. Магнит, плата и ось сохраняют монтажные положения R1; из-за нового фланца номинальный зазор до соседней платы составляет 1.0 мм, а не 2.0 мм. Бюджет отклонений и расчётный остаточный зазор приведены в отчёте C1; они не являются результатом измерения собранного экземпляра.

Осевая фиксация всего вала в корпусе, окончательное крепление магнита, пружина и остальные незавершённые узлы не входят в эту замену. Документация C1 не снимает блокировку приёмки и не превращает весь проект в готовое серийное средство измерений.

## Проверенная связь с выданным комплектом

В выданном архиве `Qulay_C1_CAD_and_Drawings.zip` и опубликованной версии совпадают байты исходников C1, README конструкции, `calculations.json` и `verification.json`. Экспорты STEP/DXF/PDF выполнены в разных средах сборки и не объявляются побайтово идентичными. Канонический набор для GitHub — сохранённые файлы указанного коммита и его `SHA256SUMS`; повторная загрузка дубликатов или архива вместо дерева файлов не требуется.

Данное обновление изменяет только навигацию и описание статуса. История сохранена, `main` не изменяется, force-push не используется.
