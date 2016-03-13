Запускается так:
python rability.py http://www.gazeta.ru/business/news/2016/03/11/n_8357951.shtml http://lenta.ru/articles/2016/03/10/chucknorris/

Среда выполнения:
Работает под windows, linux (проверялось)
Python 3.4
requirements.txt содержит зависимости (lxml)


Формулировка задачи

Большинство веб-страниц сейчас перегружено всевозможной рекламой... Наша задача «вытащить»
из веб-страницы только полезную информацию, отбросив весь «мусор» (навигацию, рекламу и тд).
Полученный текст нужно отформатировать для максимально комфортного чтения в любом
текстовом редакторе. Правила форматирования: ширина строки не больше 80 символов (если
больше, переносим по словам), абзацы и заголовки отбиваются пустой строкой. Если в тексте
встречаются ссылки, то URL вставить в текст в квадратных скобках. Остальные правила на ваше
усмотрение.

Программа оформляется в виде утилиты командной строки, которой в качестве параметра
указывается произвольный URL. Она извлекает по этому URL страницу, обрабатывает ее и
формирует текстовый файл с текстом статьи, представленной на данной странице.
В качестве примера можно взять любую статью на lenta.ru, gazeta.ru и тд
Алгоритм должен быть максимально универсальным, то есть работать на большинстве сайтов.

Усложнение задачи 1: Имя выходного файла должно формироваться автоматически по URL.
Примерно так:
http://lenta.ru/news/2013/03/dtp/index.html => [CUR_DIR]/lenta.ru/news/2013/03/dtp/index.txt
Усложнение задачи 2: Программа должна поддаваться настройке – в отдельном файле/файлах
задаются шаблоны обработки страниц.

Требования к выполнению задачи
1. Задача выполняется на С++|Python с использованием классов. Не должно использоваться
сторонних библиотек, впрямую решающих задачу.
2. Предпочтительная среда выполнения – MS Windows.
3. Решение должно состоять из документа, описывающего алгоритм, исходных кодов
программы, исполняемого модуля.
4. Приложите список URL, на которых вы проверяли свое решение. И результаты проверки.
5. Желательно указать направление дальнейшего улучшения/развития программы.


Алгоритм получения контента:
1) Парсим информацию по урлу с помощью lxml
2) Из body достаем все тэги div добавляем в сисок подозреваемых
3) Каждому элементу из списка считаем метрики (количество слов, символов, знаков пунктуации, вложенных тегов и т.д.)
4) Производим расчёт стоимости каждого элемента
5) Сортируем список подозреваемых по стоимости элемента, по убыванию.
6) Выбираем первый элемент, получаем его текст и все вложенные теги
7) Все вложенные теги в тексте форматируем согласно конфигурации
8) Форматируем текст согласно конфигурации (длина строк)
9) Возвращаем отформатированный текст

Алгоритм программы:
1) Получаем список url в качестве аргументов программы
2) Для каждого url получаем контент
3) Форматируем имя, путь к файлу
4) Создаём файл, записываем контент в файл

Для проверки использовалось несколько url, некоторые из них:
http://photo.novokreshenova.ru/schweinfurt/
https://habrahabr.ru/company/mailru/blog/200394/
http://www.gazeta.ru/business/news/2016/03/11/n_8357951.shtml
http://lenta.ru/articles/2016/03/10/chucknorris/

Дальнейшее развитие зависит от области применения.
Но в общем можно выделить несколько доработок. В частности:
1) Написание тестов, чтобы дальнейшие доработки не нарушали правильную работу
2) Поддержка других тегов, типа 'code', 'article', 'q', 'img'
3) Доработка и оптимизация алгоритма
4) Вывод в html формат с подстановкой "своих" тэгов