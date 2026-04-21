import pytest
import pandas as pd
import numpy as np
from src.pipeline.clean import drop_duplicates, normalize_text, handle_missing, flag_length_outliers

def test_drop_duplicates():
    df = pd.DataFrame({
        'input': ['Hello', 'hello ', 'World'],
        'categorie': ['A', 'A', 'B']
    })
    # 'hello ' normalized should match 'Hello' normalized
    df_clean = drop_duplicates(df)
    assert len(df_clean) == 2

def test_normalize_text():
    df = pd.DataFrame({
        'input': ['  Hello   World  ', '“Test”'],
    })
    df_clean = normalize_text(df)
    assert df_clean['input'].iloc[0] == 'Hello World'
    assert df_clean['input'].iloc[1] == '"Test"'
    assert 'input_raw' in df_clean.columns

def test_handle_missing():
    df = pd.DataFrame({
        'input': ['Ok', '', None],
        'reponse_suggeree': ['Cool', None, 'Wait']
    })
    df_clean = handle_missing(df)
    assert len(df_clean) == 1
    assert df_clean['reponse_suggeree'].iloc[0] == 'Cool'
    
    # Test imputation
    df2 = pd.DataFrame({
        'input': ['Valid'],
        'reponse_suggeree': [None]
    })
    df2_clean = handle_missing(df2)
    assert df2_clean['reponse_suggeree'].iloc[0] == "Réponse en attente de traitement."

def test_flag_length_outliers():
    # Create a distribution where one is far away
    # Use many values to make the std small enough for Z=3
    data = ['a' * 10] * 50 + ['a' * 500] 
    df = pd.DataFrame({'input': data})
    df_flagged = flag_length_outliers(df)
    assert df_flagged['is_outlier'].iloc[-1] == True
    assert df_flagged['is_outlier'].iloc[0] == False
