import torch
from net import BiLSTM_CRF, BERT_CRF
from flair.embeddings import BertEmbeddings
from flair.data import Sentence
import pickle
import os
import re

DIR = os.path.dirname(os.path.abspath(__file__))
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

EMBEDDING_DIM = 256
HIDDEN_DIM = 256
num_words = 3000

START_TAG = "<START>"
STOP_TAG = "<STOP>"

tag_to_ix = {
    START_TAG: 0,
    STOP_TAG: 1,
    'B': 2, 'M': 3, 'E': 4,
    'S': 5
}

ix_to_tag = {tag_to_ix[ix]: ix for ix in tag_to_ix}

with open(DIR + '/data/word_index.pkl', 'rb') as f:
    word_index = pickle.load(f)


def test(dir_model, feature='LSTM'):
    if feature == 'BERT':
        model = BERT_CRF(tag_to_ix=tag_to_ix)
        checkpoint = torch.load(dir_model)
        model.load_state_dict(checkpoint)
        model = model.to(device)

        # 导入BERT预训练模型
        embedding = BertEmbeddings('bert-base-chinese', '-1', 'mean')
        while True:
            print('输入文本,结束输入"quit":\n')
            text = input()
            if text != 'quit':
                with torch.no_grad():
                    # 文本转编码
                    x_test = Sentence(' '.join(text.replace(' ', '|')))
                    embedding.embed(x_test)
                    x_test = torch.Tensor(([token.embedding.numpy() for token in x_test])).to(device)
                    # 输出标注结果
                    score, test_tag = model(x_test.view([-1, 768]))
                    tag = [ix_to_tag[ix] for ix in test_tag]
                    print(tag)
                    result = re.finditer("S|BM*E", ''.join(tag))
                    # 定位实体,即"词语"
                    result = [[m.start(), m.end()] for m in result]
                    text_cut = ''
                    for i in result:
                        text_cut += ('/' + text[i[0]:i[1]])

                    print('\n分词结果: ', text_cut, '\n')
            else:
                break
    else:
        # 导入训练好的模型
        model = BiLSTM_CRF(vocab_size=num_words + 2,
                           tag_to_ix=tag_to_ix,
                           embedding_dim=EMBEDDING_DIM,
                           hidden_dim=HIDDEN_DIM)
        checkpoint = torch.load(dir_model)
        model.load_state_dict(checkpoint)
        model = model.to(device)
        while True:
            print('输入文本,结束输入"quit":\n')
            text = input()
            if text != 'quit':
                with torch.no_grad():
                    # 文本转编码
                    x_test = [word_index.get(char, num_words + 1) for char in text]
                    x_test = torch.LongTensor(x_test).to(device)
                    # 输出标注结果
                    score, test_tag = model(x_test)
                    tag = [ix_to_tag[ix] for ix in test_tag]
                    result = re.finditer("S|BM*E", ''.join(tag))
                    # 定位实体,即"词语"
                    result = [[m.start(), m.end()] for m in result]
                    text_cut = ''
                    for i in result:
                        text_cut += (' ', text[i[0]:i[1]], ' ')

                    print('\n分词结果: ', text_cut, '\n')
            else:
                break


if __name__ == '__main__':
    # _dir_model = DIR + '/model/LSTM_003.pth'
    # test(_dir_model, 'LSTM')

    _dir_model = DIR + '/model/BERT_002.pth'
    test(_dir_model, 'BERT')
