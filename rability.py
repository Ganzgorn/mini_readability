import argparse
from urllib.error import HTTPError
import config
import os

from math import log
from lxml import html
from urllib.request import urlopen


class ElementsPool:
    """
    Хранит список всех потенциальных "контентов"
    """
    elements = set([])

    @classmethod
    def get_content(cls):
        """
        Происхоидт сортировка по весу элемента, первым элементом, после сортировки, должен быть необходмый контент
        """
        for el in cls.elements:
            el.calculate_cost()

        sorted_elements = list(sorted(ElementsPool.elements, key=lambda x: x.cost, reverse=True))
        if not sorted_elements:
            return None

        return sorted_elements[0]

    @classmethod
    def register(cls, el):
        """
        Регистрация элемента
        """
        element_metric = ElementMetrics(el)
        cls.elements.add(element_metric)
        return element_metric

    @classmethod
    def clear(cls):
        """
        Очистка пулла
        """
        cls.elements = set([])


class ElementMetrics(object):
    """
    Класс собирающий метрики для div элементов, также считает итоговую стоимость каждого элемента
    """
    element = None
    words = None
    avg_len_word = None
    chars = None
    dots = None
    commas = None
    tags = None
    source = None
    tags_size = None
    functions = None
    cost = None

    def __init__(self, el):
        self.element = el
        self.cost = 0

    def get_metrics(self):
        """
        Собираем различные метрики
        """
        text = self.get_text()
        word_list = text.split()
        children = self.element.getchildren()
        hypersize = len(list(filter(lambda el: el.tag == 'a', children))) or 1
        # Количество тэгов
        self.tags = len(list(filter(lambda child: child.tag not in config.CONST_TEXT_TAGS, children)))
        self.tags_size = self.get_tags_size(self.element)
        tags = self.tags_size or self.tags or 1
        # Количество символов в тексте, слов, средний вес слов
        self.chars = len(text)
        self.words = len(word_list)
        self.avg_len_word = sum([len(word) for word in word_list])/self.words if self.words else 0
        # Количество запятых и точек в тексте
        self.dots = len(list(filter(lambda ch: ch == '.', text)))
        self.commas = len(list(filter(lambda ch: ch == ',', text)))
        # Измеряем вес по формуле
        self.source = self.chars/tags * log(self.chars/hypersize) if self.chars else 0
        # Если много function в тексте, то скорее всего наткнулись на js. Или на статью по js :)
        self.functions = len(list(filter(lambda w: w == 'function', word_list)))

    def get_text(self):
        """
        Безопасно извлекаем текст из элементов (из которых извлекается)
        """
        result = ''
        if not isinstance(self.element, html.HtmlComment):
            result = self.element.text_content()
        return result

    def calculate_cost(self):
        """
        Подсчёт стоимости. Коффициенты по большей части собраны научным методом тыка
        """
        # Данный параметр можно брать из config, получен методом анализа нескольких текстов
        default_avg_len_word = 6.5  # Средняя длина слова (На основе анализа нескольких текстов)
        self.cost += self.source * 0.25  # Очки тэга. Высчитывается по формуле
        self.cost += self.words * 0.5  # Количество слов в div
        self.cost += self.chars * 0.1  # Количество символов в div. Обычно в блоке с информацией символов больше всего
        self.cost += self.commas * 10  # количество запятых
        self.cost += self.dots * 10  # Количество точек
        self.cost -= self.functions * 500  # Если в блоке имеются js функциии, стоимость блока существенно уменьшается
        self.cost -= abs(default_avg_len_word - self.avg_len_word) * 100  # Разница между предполагаемой средней длиной слов и средней длиной слов блока

    def get_tags_size(self, tag):
        """
        Метод получающий вес тегов из всех вложенных, считается из хороших и плохих тегов
        """
        children = tag.getchildren()
        total_tags_size = sum([self.get_tags_size(el) for el in children])
        good_tags = len(list(filter(lambda child: child.tag in config.CONST_TEXT_TAGS, children))) or 1
        bad_tags = len(list(filter(lambda child: child.tag not in config.CONST_TEXT_TAGS, children)))

        return (bad_tags + total_tags_size)/good_tags


class TagElement(object):
    """
    Тэг элемент для дальнейшего форматирования в тексте
    """
    pattern = config.tags_pattern
    element = None

    def __init__(self, el):
        self.element = el

    def text(self):
        text = self.element.text_content() or ''
        return ' '.join(text.split())

    def tail(self):
        tail = self.element.tail or ''
        return ' '.join(tail.split())

    @property
    def format_dict(self):
        """
        возвращает словарь, используемый в итоговой строке
        """
        return {self.element.tag: self.text()}

    @property
    def replace_str(self):
        """
        Заменяемая строка
        """
        find_str = self.text()+self.tail() if self.element.tag in self.pattern.keys() else ''
        return find_str if find_str.split() else ''

    @property
    def result_str(self):
        """
        Итоговая строка
        """
        return self.pattern.get(self.element.tag, '').format(**self.format_dict) + self.tail() if self.replace_str else ''

    def __repr__(self):
        return self.replace_str


class TagAElement(TagElement):
    """
    Элемент ссылка
    """
    pattern = config.url_pattern

    @property
    def format_dict(self):
        """
        Пробрасываем дополнительный параметр
        """
        return {self.element.tag: self.text(), 'url': self.element.attrib.get('href', 'example.com')}


class ReadabilityParser(object):
    """
    Парсер
    """
    max_len = None
    url = None
    body = None
    div_blocks = None
    title = None

    def __init__(self, url):
        self.url = url
        self.div_blocks = {}
        self.max_len = config.file_format.get('max_length', 80)

    def _parse(self):
        """
        Получение данных из урла и распарсивание библиотекой lxml.
        Дальше работаем только с элементами lxml
        Сразу разбирает body и title, остально не нужно
        """
        try:
            url_result = urlopen(self.url)
            text = url_result.read()
        except HTTPError as exc:
            if exc.code != 200:
                print('url недоступен: {} - {}'.format(exc.msg, exc.code))
                exit()
        except:
            print('Некорректный url')
            exit()

        try:
            text = text.decode('utf-8')
        except UnicodeDecodeError:
            # Текст не нуждается в декодировании
            pass

        parsed = html.document_fromstring(text)

        self.body = parsed.body
        title = parsed.head.xpath('//title')

        self.title = title[0].text_content() if title else ''

    def parsed_metrics(self, parsed_element):
        """
        Все тэги div потенциальные блоки с нужной информацией, поэтому все div собираются в пулл
        """
        children = parsed_element.getchildren()
        for el in children:
            if el.tag == 'script':
                el.drop_tree()
                continue

            self.parsed_metrics(el)
            if el.tag == 'div':
                el.drop_tree()
                el_metric = ElementsPool.register(el)
                el_metric.get_metrics()

    def get_content(self):
        """
        Получение контента
        """
        self._parse()
        self.parsed_metrics(self.body)
        content_element = ElementsPool.get_content()
        content = self.format_content(content_element.element)
        ElementsPool.clear()
        return '\n\n'.join([self.title, content])

    def format_content(self, element):
        """
        Форматирование итогового текста.
        Приводим к необходимому виду тэги и длину строк
        """
        children = element.getchildren()
        format_tags = [TagElement(el) for el in filter(lambda el: el.tag in config.tags_pattern.keys(), children)]
        format_tags.extend([TagAElement(el) for el in filter(lambda el: el.tag in config.url_pattern.keys(), children)])
        content = element.text_content()
        content = ' '.join(content.split())

        for format_tag in format_tags:
            content = content.replace(format_tag.replace_str, format_tag.result_str, 1)
        content_lines = []
        for line in content.split('\n'):
            content_lines.append(self.format_line(line))

        return '\n'.join(content_lines)

    def format_line(self, line):
        """
        Рекурсивная корректировка длины строки
        """
        if len(line) > self.max_len:
            sep_num = line[:self.max_len].rfind(' ')
            result = '\n'.join([line[:sep_num], self.format_line(line[sep_num:].strip())])
        else:
            result = line

        return result


def save_file(file_path, content):
    """
    Сохранение контента в файл
    """
    current = os.path.dirname(os.path.abspath(__file__))
    if not file_path.startswith(current):
        file_path = os.path.join(current, file_path)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(content)
        f.close()
        print('Файл {} сохранён'.format(file_path))


def url_to_file():
    """
    Запись urls в файл
    """
    try:
        space = parser.parse_args()
    except SystemExit:
        print('Ожидается url в качестве параметра')
        exit()

    urls = space.url
    replace_list = config.file_format.get('replace_list', [])
    format_file = config.file_format.get('format_file', 'txt')
    for url in urls:
        path = url[:url.rfind('.')] if any([url.endswith(rplc) for rplc in replace_list]) else url
        path = os.path.join(*[p for p in path.split('/')[1:] if p])
        path = '.'.join([path, format_file])
        content = ReadabilityParser(url).get_content()
        save_file(path, content)


parser = argparse.ArgumentParser()
parser.add_argument('url', type=str, nargs='+', help='Ссылка на статью')

url_to_file()


# if __name__ == '__main__':
#     url = 'https://habrahabr.ru/post/220983/'
#     url = 'https://habrahabr.ru/post/194852/'
#     url = 'https://habrahabr.ru/company/mailru/blog/200394/'
#     url = 'http://www.thetimes.co.uk/tto/news/'
#     url = 'http://lenta.ru/news/2016/03/08/knifemother/'
#     url = 'http://lenta.ru/articles/2016/03/08/sharapova/'
#     url = 'http://lenta.ru/articles/2016/03/06/gerodot/'
#     url = 'http://htmlbook.ru/html/nobr'
#     url = 'http://www.gazeta.ru/social/2016/03/08/8113169.shtml'
#     url = 'http://www.gazeta.ru/politics/2016/03/09_a_8114321.shtml'
#     url = 'http://developer.alexanderklimov.ru/android/sqlite/android-sqlite.php'
#     url = 'http://metanit.com/java/android/9.1.php'
#     url = 'http://example.com/'
#     url = 'http://tensor.ru/'
#     url = 'https://sbis.ru/'
#     parser = ReadabilityParser(url)
#     print(parser.get_content())
