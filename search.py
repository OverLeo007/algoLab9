"""
Файл с реализацией нечеткого поиска методом N-грамм
"""

from copy import deepcopy
import re
import threading
from functools import reduce
from typing import List, Tuple, Dict, Union


class Search:
    """
    Класс реализации
    """

    def __init__(self, text: str, cs: bool = False, n: int = 4, k: int = 1) -> None:
        """
        Инициализация экземпляра
        :param text: исходный текст, в котором производится поиск
        :param cs: чувствительность к регистру
        :param n: длина n-граммы
        :param k: сколько таблиц справа и слева будут проверяться для каждой n-граммы
        """
        self.text = text
        self.words = text.split()
        self.cs = cs
        self.n, self.k = n, k

    def make_ngram_tables(self, word: str) -> List[Tuple[int, Dict[str, set]]]:
        """
        Метод создания таблиц по выбранному слову
        :param word: слово
        :return: список с кортежами, где в кортежах 1 элемент -
        положение нграммы в слове, 2 элемент словарь с n-граммами
        которые мы будем проверять на текущей позиции словарями
        """
        splitted = self.split_word(word)
        n_gram_table = []
        for i, ngram in enumerate(splitted):
            n_gram_table.append({
                ngram: set()
            })
        table_size = len(n_gram_table)
        tables = []
        for i in range(table_size):
            l_idx, r_idx = self.get_indexes(table_size, i)
            tables.append((i, reduce(lambda x, y: {**x, **y},
                                     deepcopy(n_gram_table[l_idx: r_idx]))))
        return tables

    def get_indexes(self, list_size: int, index: int) -> \
            Tuple[Union[int, bool], Union[int, bool]]:
        """
        Метод полученя левых и правых индексов n-грамм которые будут проверяться
        :param list_size: размер списка
        :param index: индекс
        :return: словарь из двух чисел (левая и правая границы) или False, False
        если текущая n-грамма не должна быть рассмтрена
        """
        left_idx = index - self.k
        if left_idx < 0:
            left_idx = 0
        elif left_idx > list_size - 1:
            return False, False
        right_idx = index + self.k
        if right_idx > list_size - 1:
            right_idx = list_size
        return left_idx, right_idx + 1

    def split_word(self, word: str) -> List[str]:
        """
        Метод разделения слова на n-граммы
        :param word: слово для разделения
        :return: список n-грамм
        """
        return [
            word[i:i + self.n] if self.cs else word[i:i + self.n].lower()
            for i in range(len(word) - self.n + 1)
        ]

    def worker(self, index: int, table: Dict[str, set]):
        """
        Метод используемый тредами для поиска подходящих слов по определенной
        таблице и смещению в слове
        :param index:
        :param table:
        """
        for i, word in enumerate(self.words):
            splitted = self.split_word(word)
            if len(splitted) < index + 1:
                continue
            if table.get(splitted[index], False) is not False:
                table[splitted[index]].add((i, word))

    def find(self, word: str) -> Dict[str, Tuple[int]]:
        """
        Метод поиска слова в тексте
        :param word: слово для поиска
        :return: словарь с найденными подстроками и их индексами
        """
        tables = self.make_ngram_tables(word)
        threads = []
        for table in tables:
            thread = threading.Thread(target=self.worker,
                                      args=table)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        substrs = set()
        for _, table in tables:
            for vals in table.values():
                substrs.update(vals)
        substrs = set(map(lambda y: y[1], substrs))
        indexes = {
            substr: tuple(
                match.start() for match in re.finditer(re.escape(substr), self.text)
            ) for substr in substrs
        }
        return indexes


# if __name__ == '__main__':
#     searcher = Search(file_to_str("test.txt"))
#     print(searcher.find("работа"))
#     print(searcher.find("сократ"))
