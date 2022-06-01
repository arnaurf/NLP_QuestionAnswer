# -*- coding: utf-8 -*-
"""nlp_pointer_generator_assignment_192961_205702_205203.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZmvktoVtUSJLD8Kq-2-KPk35rogGRAxP

**Intro to NLP - Final Assignment:** Pointer Generator on SQuAD dataset

Arnau Ruiz (192961), Simone Gigante (205702), Enrique Torres (205203)

#**Drive Mount and Imports**
"""

# drive mount

from google.colab import drive
drive.mount('/content/drive')

# set your working and data paths as '/content/drive/...'

work_path = '/content/drive/Shareddrives/Intro_to_NLP/nlp_final_assignment_192961_205702_205203/'

data_path = '/content/drive/Shareddrives/Intro_to_NLP/nlp_final_assignment_192961_205702_205203/SQuAD dataset/'

# Commented out IPython magic to ensure Python compatibility.
# %cd '/content/drive/Shareddrives/Intro_to_NLP/nlp_final_assignment_192961_205702_205203/'

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import json
import re
import numpy as np

nltk.download('punkt')

! pip install OpenNMT-py

! git clone https://github.com/OpenNMT/OpenNMT-py

"""#**Creating data sources for Pointer Generator model**

Following the ted_train.yml specifications, we need to build:

*   **src-train.txt**: "QUESTION"+"PARAGRAPH" concatenated strings in a one line with tokens separated by space.
*   **tgt-train.txt**: answer sentences, i.e. the sentence to which each question answer belongs.

* **src-val.txt**: smaller subset of "QUESTION"+"PARAGRAPH" concatenated strings for validation purposes.

* **tgt-val.txt**: smaller subset of answer sentences.

Aditionally, in order to test the model, we will need:

* **src-test.txt**

* **tgt-test.txt**

"""

f = open(data_path + 'dev-v2.0.json',)

dev_data = json.load(f)
f.close()

f = open(data_path + 'train-v2.0.json')

train_data = json.load(f)
f.close()

train_data['data'][0]['paragraphs'][0].keys()

"""**IMPORTANT:** remove sample files from before saving our created ones"""

# Commented out IPython magic to ensure Python compatibility.
# %ls

# Commented out IPython magic to ensure Python compatibility.
# %cd 'OpenNMT-py/data/'

! rm src-train.txt src-val.txt tgt-train.txt tgt-val.txt src-test.txt

def answerable_ones(data,tidx,pidx):
  # returns the set of answerable question-answering objects (dictionaries) and its order
  answerable_ones = [(data['data'][tidx]['paragraphs'][pidx]['qas'][qidx], qidx) for qidx in range(len(data['data'][tidx]['paragraphs'][pidx]['qas'])) if(data['data'][tidx]['paragraphs'][pidx]['qas'][qidx]['is_impossible']==False)]
  return answerable_ones

def get_answer_start(data, text_idx, prgph_idx, q_idx):
  # return the "earliest" position of the answer in paragraph's text
  q = data['data'][text_idx]['paragraphs'][prgph_idx]['qas'][q_idx]
  start_idxs = set({})
  # iterates along the list of answer dictionaries and add the answer start index to a set  
  for ans in q['answers']:
    start_idxs.add(ans['answer_start']) 
  return min(start_idxs)

def get_answer_sentence(data, text_idx, prgph_idx, q_idx):
  # returns the sentence to which an answer belongs
  answer_start = get_answer_start(data, text_idx, prgph_idx, q_idx)
  text = data['data'][text_idx]['paragraphs'][prgph_idx]['context']
  sentences = sent_tokenize(text)
  pointer = len(sentences[0]) - 1
  idx = 0
  
  while(pointer < answer_start and idx < len(sentences)-1):
    idx +=1
    pointer += len(sentences[idx])

  return sentences[idx]

def write_samples_to_file(filename,text_preprocess,content,idx_start,idx_end):

  if text_preprocess:
    filename = filename + '-clean.txt'
  else:
    filename = filename + '.txt'

  with open(filename,'w') as writer:
    for i in range(idx_start,idx_end):
      writer.writelines(content[i]+'\n')

def get_pg_data_samples(mode,text_preprocess):

  if mode=="train":
    data = train_data
  else:
    data = dev_data  
  
  total_data_samples = 0
  
  tgt_ans_sents = []
  training_sents = []

  for tidx in range(len(data['data'])):
    for pidx in range(len(data['data'][tidx]['paragraphs'])):
      answerables = answerable_ones(data,tidx,pidx)
      if(len(answerables)!=0):
        #for answerable_idx in range(len(answerables)): avoids repeated contexts in training data
        total_data_samples += 1

        question = answerables[0][0]['question']
        qidx = answerables[0][1]
          
        # get the sentence to which the answer belongs
        answer_sentence = get_answer_sentence(data,tidx,pidx,qidx)
        if text_preprocess:
          answer_sentence = re.sub("[^a-zA-Z0-9?' ']",'',answer_sentence) #preprocess
        tgt_ans_sents.append(' '.join(word_tokenize(answer_sentence)))

        # write pointer generator source training data as question + ' ' + paragraph 
        paragraph = data['data'][tidx]['paragraphs'][pidx]['context']
        input_string = question + ' ' + paragraph
        if text_preprocess:
          input_string = re.sub("[^a-zA-Z0-9?' ']",'',input_string) #preprocess
        data_sample = ' '.join(word_tokenize(input_string))
        training_sents.append(data_sample)

  if mode == "train": 
    training_amount = int(np.floor(0.75*total_data_samples))
    validation_amount = int(np.floor(0.25*total_data_samples))

    write_samples_to_file('src-train',text_preprocess,training_sents,idx_start=0,idx_end=training_amount)
    write_samples_to_file('tgt-train',text_preprocess,tgt_ans_sents,idx_start=0,idx_end=training_amount)

    write_samples_to_file('src-val',text_preprocess,training_sents,idx_start=training_amount,idx_end=training_amount+validation_amount)
    write_samples_to_file('tgt-val',text_preprocess,tgt_ans_sents,idx_start=training_amount,idx_end=training_amount+validation_amount)

  else:
    test_amount = int(np.floor(0.4*total_data_samples))
    
    write_samples_to_file('src-test',text_preprocess,training_sents,idx_start=0,idx_end=test_amount)
    write_samples_to_file('tgt-test',text_preprocess,tgt_ans_sents,idx_start=0,idx_end=test_amount)
  

  return total_data_samples

# Commented out IPython magic to ensure Python compatibility.
# %pwd

#!ls

# writing files

# src-train, tgt-train, src-val, tgt-val
amount_train_samples = get_pg_data_samples(mode="train",text_preprocess=False)
amount_clean_train_samples = get_pg_data_samples(mode="train",text_preprocess=True)

# src-test, tgt-test 
amount_test_samples = get_pg_data_samples(mode="test",text_preprocess=False)
amount_clean_test_samples = get_pg_data_samples(mode="test",text_preprocess=True)

"""Already written"""

!ls

"""#**Testing Pointer Generator**

Requires

1) A configuration file, .yaml in this case, located in the OpenNMT-py path.

2) Building the source vocabulary

3) Training from text files defined in config file

4) Test the model with test text file
"""

# Commented out IPython magic to ensure Python compatibility.
# %cd '/content/drive/Shareddrives/Intro_to_NLP/nlp_final_assignment_192961_205702_205203/OpenNMT-py/'

!ls

"""Raw text"""

! onmt_build_vocab -config ted_train.yaml -n_sample 10000

! onmt_train -config ted_train.yaml

! onmt_translate -model data/run/model_step_1000.pt -src data/src-test.txt -output data/pred_1000.txt -gpu 0 -verbose

"""Preprocessed text"""

! onmt_build_vocab -config ted_train_clean.yaml -n_sample 10000

! onmt_train -config ted_train_clean.yaml

! onmt_translate -model data/run/preprocessed_model_step_1000.pt -src data/src-test-clean.txt -output data/clean_pred_1000.txt -gpu 0 -verbose