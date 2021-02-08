# -*- coding: utf-8 -*-

# Lista os arquivos no diretório
from os import listdir
# Dataframe
import pandas as pd
# Aliases
from typing import List

# A object used only to specify the type
DataFrames = List[pd.DataFrame]


def read_csv(sheetsDir: str) -> DataFrames:
    """
    Open a directory and read all csv files inside.
    This function clean some unusefull elements based on researches models.

    Args:
        sheetsDir: Directory to search for csv files.

    Returns:
        A list of pandas dataframes
    """
    # Get form's infos
    infos = []
    for file in listdir(sheetsDir):
        tmpDF = pd.read_csv(f"{sheetsDir}/{file}").fillna(0)
        # Remove two last lines
        tmpDF = tmpDF[:-2]
        # Renaming columns
        header = tmpDF.columns.to_list()
        header[0] = 'Periodo'
        header[1] = 'Sigla'
        header[2] = 'Nome da disciplina'
        header[-1] = 'Somatório'
        tmpDF.columns = header
        # Removing unecessary columns
        tmpDF.drop(['Periodo', 'Nome da disciplina',
                    'Somatório'], axis=1, inplace=True)
        # Turn initials into index
        tmpDF.set_index('Sigla', inplace=True)

        # Append this dataframe to info vec
        infos.append(tmpDF)

    # Return a list of dataframes
    return infos


def merge_data(dataframes: DataFrames) -> pd.DataFrame:
    """
    It performs the join of multiple dataframes objects into a single one,
    basing on a specified method.

    Args:
        dataframes: A list of dataframes to be merged.

    Returns:
        A single dataframe based on values passed through
    """
    # Juntando os arquivos num único dataframe
    out = pd.concat(dataframes)

    # Realizando a média
    out = out.groupby(out.index)
    out = out.mean()

    return out


# TODO: colocar a função de montar a grade com base nas competências aqui
