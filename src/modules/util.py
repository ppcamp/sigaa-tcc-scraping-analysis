# -*- coding: utf-8 -*-

"""
A module containing some usefull functions that can be shared with another modules
"""

from __future__ import annotations
import unittest
from typing import Dict, List, Tuple, Union, overload
import logging as logger
import sys
import numpy as np
import pandas as pd
from modules.ahp import Ahp
from modules.ahp.Types import FormData, FormDataType


class MinimumLenghtError(Exception):
    """
    Exception raised when you didn't achieved the minimum numbers of elements.

    :Args:
        - `message`: The value to raise
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@overload
def average(args: List[float], roundp: int = 4) -> float:
    """
    Calculate the mean of a given amount of values.

    :Args:
        - `args`: A list of floats

    :Kwargs:
        - `roundp`: Number of decimal places used to round

    :Returns:
        The median of this vector

    :Example:
        .. code-block:: python
            :linenos:
            :caption: Using a list of float

            l = [1, 1, 1, 1, 1]
            average(l)
            # will be 1

    .. centered:: Equation that describes its behavior:
    .. math:: \\frac{\\sum_{i=0}^N\\text{arg}_i}{N}

    .. versionchanged:: 0.0.9
        Separated into two documentations
    """
    ...


@overload
def average(args: List[List[List[float]]], roundp: int = 4) -> np.ndarray:
    """
    Calculate the mean of a given amount of values.
    It can performs the mean over List[List[float]] or List[float].

    :Args:
        - `args`: A list of matrices

    :Kwargs:
        - `roundp`: Number of decimal places used to round

    :Returns:
        The matrix that corresponds to median for each position

    .. centered:: Equation that describes its behavior:
    .. math:: \\text{output} = \\frac{\\sum_{n=0}^N \\mathb{M}[n]_\\text{i x j}}{N}

    .. versionchanged:: 0.0.7
        Fixed the problem with multiples pointers to the same memory address.
    """
    ...


def average(args: ..., roundp: int = 4) -> ...:
    """
    Calculate the mean of a given amount of values.
    It can performs the mean over List[List[float]] or List[float].

    :Args:
        - `args`: A list of floats or a list of matrices

    :Kwargs:
        - `roundp`: Number of decimal places used to round

    :Example:
        .. code-block:: python
            :linenos:
            :caption: Using a list of float

            l = [1, 1, 1, 1, 1]
            average(l)
            # will be 1

        .. centered:: Equation that describes its behavior:
        .. math:: \\frac{\\sum_{i=0}^N\\text{arg}_i}{N}

        .. code-block:: python
            :linenos:
            :caption: Using a list of list of floats

            from copy import deepcopy

            a = [
                [1, 1, 1],
                [1, 1, 1],
            ]
            b = deepcopy(a)

            result = average([a,b])
            expected_result = deepcopy(a)

            # iterate and raise an error. P.S.: It won't throw any error
            for row in range(2):
                for col in range(3):
                    assert result[row][col] == expected_result[row][col]

        .. centered:: Equation that describes its behavior:
        .. math:: \\text{output}_\\text{(i,j)} = \\frac{\\sum_{n=0}^N \\text{Matrix}[n]_\\text{(i,j)}}{N} \\text{,     } \\forall \\text{ }0 \\leq i,j < N

    .. versionchanged:: 0.0.9
        Create two functions, splicing documentation according with param type.

    .. versionchanged:: 0.0.7
        Fixed the problem with multiples pointers to the same memory address.
    """
    from statistics import mean

    if type(args) != float and type(args) != list:
        raise TypeError(
            f"The elements must be a List[float] or List[List[List[float]]]. The type is {type(args)}")

    # must exist at least two elements
    if len(args) < 2:
        raise MinimumLenghtError(
            f"You should pass, at least, an array with 2 elements")

    # logger.debug(f'Average called.')
    # if passed a list of float, returns a single float element
    if type(args[0]) is not list:
        out: float = round(
            mean([scalar for scalar in args]), roundp)  # type:ignore
        # logger.debug(f"It's a list of floats: {args} --> Mean={out}")
        return out

    # otherwise, create a new matrix
    matrix_length = len(args[0])
    # output_matrix: List[List[float]] = [[0.0]*matrix_length] * matrix_length
    output_matrix: List[List[float]] = np.zeros((matrix_length, matrix_length))

    # calcula a média item a item
    for row in range(matrix_length):
        for col in range(matrix_length):
            current_elements = [m[row][col] for m in args]  # type: ignore
            current_mean = mean(current_elements)
            output_matrix[row][col] = round(current_mean, roundp)

            # logger.debug(
            #     f'Analysing for {row},{col} = {current_elements} --> Mean={current_mean}')
    # logger.debug(f'It\'s a matrix:Mean={output_matrix}')

    return output_matrix


def errprint(msg: str) -> None:
    """
    Print some error message, returning a different value from default (1).

    :Args:
        - `msg`: Message to be shown
    """
    sys.stderr.write('Error: ' + msg)


def get_competences_and_consistency(
        data: List[FormData],
        tt: FormDataType
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    It calculates the ahp for each *data*

    :Args:
        - `data`: A list of data that will be placed as rows in result dataframes
        - `tt`: Type of each list of *data*. See more on :class:`modules.ahp.Types.FormDataType`

    :Returns:
        A tuple that contains:
            - The mongo competences calculated and parsed to each competence
            - The mongo consistency for each matrix
    """
    t: str = tt.value

    # dataframe de consistência para cada resposta
    _dfconsist = [
        'type',
        'name',
        *Ahp.Mapping.MATRICES_IDENTIFIERS,
    ]
    mongo_competences_consistency: pd.DataFrame = pd.DataFrame(
        columns=_dfconsist)

    # cria um dataframe para armazenar a relação de respostas por competência
    mongo_competences: pd.DataFrame = pd.DataFrame(columns=[
        'type',
        'name',
        *Ahp.Mapping.COMPETENCES_MATRIX_ROOT,
        *Ahp.Mapping.COMPETENCES_MATRIX_FORM_Q1,
        *Ahp.Mapping.COMPETENCES_MATRIX_Q12,
        *Ahp.Mapping.COMPETENCES_MATRIX_Q13,
        *Ahp.Mapping.COMPETENCES_MATRIX_Q15,
        *Ahp.Mapping.COMPETENCES_MATRIX_Q2,
        *Ahp.Mapping.COMPETENCES_MATRIX_Q3,
    ])

    for response in data:
        _type: str = t
        _name: str = response.getName()

        _secoes = {}
        _matrices = response.getMatrices()
        _cline = {k: "" for k in _dfconsist}
        _cline['type'] = _type
        _cline['name'] = _name

        for k, v in _matrices.items():
            # verifica se é um escalar
            if k == "q15":
                priority_vec = Ahp.get_q15_value(v)  # type:ignore
                logger.debug(f"q15: {v} -> {priority_vec}")
            else:
                # caso seja uma matriz, calcula o ahp ...
                # ... NOTE que aceita AHP errados
                if v[0][0] != 0:
                    _cline[k], priority_vec = Ahp.calculate(v)  # type: ignore
                else:
                    _cline[k] = 0  # type: ignore
                    priority_vec = [0]*len(v)

            # adiciona as competências para cada matriz
            _secoes[k]: Union[float, List[float]
                              ] = priority_vec  # type: ignore

        mongo_competences_consistency = mongo_competences_consistency.append(
            _cline, ignore_index=True)
        # faz o mapping para essas competências
        # _n: Dict[str, float] = Ahp.mapping_competences(_secoes)
        _n: Dict[str, float] = Ahp.Mapping.to_competences(_secoes)
        _n['type'] = _type  # type:ignore
        _n['name'] = _name  # type:ignore
        # adiciona o dicionário de competências ao dataframe
        mongo_competences = mongo_competences.append(_n, ignore_index=True)

    return mongo_competences, mongo_competences_consistency


def calc_mean_matrix(data: List[FormData]) -> Dict[str, Union[float, List[List[float]]]]:
    """
    It calculates the mean matrix that corresponds to the mean of all *data*.

    .. attention::

        - It ignores matrices fullfilled with 0 for the mean calculation.
        - It also ignores matrices where the *ahp wasn't valid*

    :Args:
        - `data`: The list of data obtained from :meth:`modules.ahp.Database.AhpForm.findByType`

    :Returns:
        A dictionary mapping each matrix to its equivalent mean matrix.
    """
    # dicionário de matrizes (que irão conter a média das matrizes )
    matrices: Dict[str, Union[List[List[float]], float]] = {}

    # obtém as possiveis keys do questionário (ids das matrizes)
    matrices_ids: List[str] = list(data[0].getMatrices().keys())
    # logger.debug(f'Matrix ids {matrices_ids}')

    # calcula a média ponderada das matrizes
    for matrix in matrices_ids:
        # logger.debug(f'Calculating the equivalent matrix for {matrix}')
        all_matrices = []

        # anda sobre uma determinada "matrix" sobre todas as respostas
        for response in data:
            # logger.debug(f'\tCurrent person {response.getName()}')
            # obtêm a matriz
            current: Union[float, List[List[float]]] = response.getMatrices()[
                matrix]

            # verifica se é uma matriz com base na chave (q15 é um escalar)
            if matrix != 'q15':
                cr = 1E9
                # verifica se a matriz atual foi preenchida ...
                # ... se foi, adiciona essa matriz válida ...
                # ... dessa forma, futuramente, ela será incluída no cálculo da média
                if current[0][0] != 0:
                    # logger.debug(
                    # f'\t\tThe matrix for this respondent was fullfilled')
                    cr, _ = Ahp.calculate(current)
                # também verifica se é um ahp válido
                if cr <= 0.1:
                    # logger.debug(
                    # f'\t\tThe CI for this matrix was valid so, we added it in mean: {current}')
                    all_matrices.append(current)
            # caso contrário, se trata de um escalar e, portanto, deverá ...
            # ... ser encontrado o seu equivalente
            else:
                # ... IGNORA MATRIZES QUE NÃO HOUVERAM RESPOSTAS
                if current != 0:
                    all_matrices.append(
                        Ahp.get_q15_value(current))  # type:ignore

        # logger.debug(f'All matrices: {all_matrices}')

        # calcula a média ponderada para cada matriz válida
        mean = average(all_matrices)
        # logger.debug(f'Mean for:\n{all_matrices}\nis: {mean}')
        matrices[matrix] = mean  # type:ignore

    return matrices


def calc_ahp_for_new_mat(
    matrices: Dict[str, Union[List[List[float]], float]]
) -> Dict[str, Union[List[float], float]]:
    """
    This function are only used to calculate AHP for each `matrices`

    :Args:
        - `matrices`: A dictionary mapping a matrix to a matrix or a float

    :Returns:
        A dictionary containing the *priority vector* of each matrix.

    .. important::

        This method only calculate AHP again. It *doesn't check if AHP are valid or not*
    """
    secoes: Dict[str, Union[List[float], float]] = {}
    logger.debug('Calculating ahp for new matrices')

    for matrix in matrices:
        logger.debug(f'Calculating for matrix: {matrix}')
        logger.info(matrices[matrix])
        cr, priorityVec = 0, matrices[matrix]  # type: ignore

        # se for uma matriz, calcula o ahp. Senão, mantém o valor do q15
        if matrix != 'q15':
            cr, priorityVec = Ahp.calculate(matrices[matrix])  # type: ignore
            logger.debug(f'Cr calculated: {cr}')
            logger.debug(f'PriorityVec: {priorityVec}')
            # arredonda o vetor de saída (resultante) para 2 casas decimais
            priorityVec: List[float] = list(np.round(priorityVec, 2))

        # adiciona este dado no vetor de competências do mercado
        secoes[matrix] = priorityVec
    logger.debug('\n\n')
    return secoes


class TestUtil(unittest.TestCase):
    def test_average_to_floats(self):
        v = [3.0, 56.0, 1.0, 41.0]
        test = round(sum(v)/len(v), 3)
        result = average(v, roundp=3)
        self.assertEqual(test, result, "Values didn't match")

    def test_average_to_matrices(self):
        from copy import deepcopy

        a: List[List[float]] = [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]
        b: List[List[float]] = deepcopy(a)

        result = average([a, b])
        expected_result: List[List[float]] = deepcopy(a)

        # iterate and raise an error. P.S.: It won't throw any error
        for row in range(2):
            for col in range(2):
                self.assertEqual(
                    result[row][col],
                    expected_result[row][col],
                    f"result[{row}][{col}] = {result[row][col]}")


if __name__ == '__main__':
    unittest.main()
