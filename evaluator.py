from transformers import AutoModelForSeq2SeqLM, DataCollatorForSeq2Seq, Seq2SeqTrainingArguments, Seq2SeqTrainer
from transformers import AutoTokenizer, MBartTokenizer
from src.envs import build_env
import torch.nn.functional as F
import datasets
import random
import pandas as pd
from datasets import Dataset
import torch
import os
from datasets import load_dataset, load_metric
import io
import numpy as np
import sympy as sp
from src.utils import AttrDict 
from src.hf_utils import evaluation_function, create_dataset_test, postprocess_text
from enum import Enum
# Required Functions


def preprocess_function_new(examples):
    inputs = [prefix + ex[source_lang] for ex in examples["translation"]]
    targets = [ex[target_lang] for ex in examples["translation"]]
    model_inputs = tokenizer(
        inputs, max_length=max_input_length, truncation=True)

    # Setup the tokenizer for targets
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(
            targets, max_length=max_target_length, truncation=True)

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs


device = 'cuda' if torch.cuda.is_available() else 'cpu'

params = params = AttrDict({

    # environment parameters
    'env_name': 'char_sp',
    'int_base': 10,
    'balanced': False,
    'positive': True,
    'precision': 10,
    'n_variables': 1,
    'n_coefficients': 0,
    'leaf_probs': '0.75,0,0.25,0',
    'max_len': 512,
    'max_int': 5,
    'max_ops': 15,
    'max_ops_G': 15,
    'clean_prefix_expr': True,
    'rewrite_functions': '',
    'tasks': 'prim_fwd',
    'operators': 'add:10,sub:3,mul:10,div:5,sqrt:4,pow2:4,pow3:2,pow4:1,pow5:1,ln:4,exp:4,sin:4,cos:4,tan:4,asin:1,acos:1,atan:1,sinh:1,cosh:1,tanh:1,asinh:1,acosh:1,atanh:1',
})

language = 'ro' # SPECIFY LANGUAGE HERE.
env = build_env(params)

"""# Tokenizing the Data"""
Model_Type = 'mbart'
is_source_en = True

if Model_Type == 'mbart':
    model_checkpoint = "facebook/mbart-large-en-{}".format(language) # SPECIFY PRE-TRAINED MODEL HERE. 
    metric = load_metric("sacrebleu")
    tokenizer = MBartTokenizer.from_pretrained("facebook/mbart-large-en-ro", src_lang="en_XX", tgt_lang="ro_RO")
elif Model_Type == 'Marian':
    if is_source_en:
        model_checkpoint = "Helsinki-NLP/opus-mt-en-{}".format(language)
    else:
        model_checkpoint = "Helsinki-NLP/opus-mt-{}-en".format(language)
    metric = load_metric("sacrebleu")
    tokenizer = AutoTokenizer.from_pretrained(model_checkpoint, use_fast=False)



if model_checkpoint in ["t5-small", "t5-base", "t5-larg", "t5-3b", "t5-11b"]:
    prefix = "not important."
else:
    prefix = ""

"""# Create the Final Data Set"""


max_input_length = 1024 # Set to 512 if it is Marian-MT
max_target_length = 1024 # Set to 512 if it is Marian-MT
source_lang = "en"
target_lang = language


      
torch.cuda.empty_cache()
path = "data/test/prim_fwd_1k.test" # SPECIFY PATH OF TEST DATA HERE.
test_dataset = create_dataset_test(path=path, language= language)  
datasetM = {'test': test_dataset}
tokenized_datasets_test = datasetM['test'].map(preprocess_function_new, batched=True)
saved_path = 'models/mbart_prim_fwd_10k_en_ro'
model = torch.load(saved_path)  # SPECIFY LOADING PATH HERE.
evaluationType = Enum('evaluationType', 'Training Validation Test')
batch_size = 8
evaluation_function(1000, tokenized_datasets_test, evaluationType.Test, tokenizer, model, batch_size, env, num_beams= 1, language= language)
