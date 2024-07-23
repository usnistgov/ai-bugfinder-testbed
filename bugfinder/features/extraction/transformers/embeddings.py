from os import listdir, makedirs
from os.path import join, splitext, exists, dirname, abspath, split, normpath, sep

import numpy as np
import pandas as pd

import pickle
import torch
import networkx as nx
import glob
from transformers import AutoTokenizer

from torch_geometric.data import Data, Batch
from torch_geometric.loader import DataLoader

from abc import abstractmethod
from gensim.models import Word2Vec

from bugfinder.base.processing import AbstractProcessing
from bugfinder.settings import LOGGER


class TransformerEmbeddings(AbstractProcessing):
    def __init__(self, dataset):
        """Class initialization method."""
        super().__init__(dataset)


    def execute(self, **kwargs):
        folder_processing_list = []

        # TODO: For now, the dataset path being passed needs to include the 'cpgs' folder.
        # Need to think in a better logic to be able to parse the files in different folders.
        for test_case_folder in self.dataset.test_cases:
            for dot_folder in listdir(join(self.dataset.path, test_case_folder)):
                if splitext(dot_folder)[1] in [".dot"] and \
                test_case_folder not in folder_processing_list:
                    folder_processing_list.append(test_case_folder)
                    
        while len(folder_processing_list) != 0:
            dot_folder = folder_processing_list.pop(0)

            LOGGER.info(
                "Starting process to generate the embeddings in %s (%d items left)...",
                dot_folder,
                len(folder_processing_list),
            )

            self._process_file(join(self.dataset.path, dot_folder))


    def _process_file(self, dot_folder):
        """Processes the .dot representation, generates the embeddings and saves it
        in a pickle file

        Args:
            dot_folder (str): folder's path containing the .dot files to be processed
        """
        model_id = "microsoft/codebert-base"
        tokenizer = AutoTokenizer.from_pretrained(model_id)

        # Embeddings will be saved on 'cpgs' folder for now.
        complete_dot_file = ''
        complete_dot_file_ext = 'complete-cpg.dot'
        embeddings_folder = self.dataset.embeddings_dir

        dotfiles = glob.glob(dot_folder + '/' + '*.dot')

        if (len(dotfiles) == 0):
            LOGGER.info('No .dot files were found. Skipping this folder...')
            return
        
        LOGGER.debug ('%d .dot files found. Looking for the combined file', len(dotfiles))

        for dotfile in dotfiles:
            dirpath, filepath = split(dotfile)
            
            if (filepath == complete_dot_file_ext):
                complete_dot_file = dotfile
                LOGGER.debug('Combined .dot file found.')
                break
            
        if complete_dot_file == '':
            LOGGER.error('Combined .dot file not found. ' 
                        'Please execute the combine CPGs step again. Exiting...')
            return 

        cpg_embedding = self._tokenize_nx_graph(tokenizer, complete_dot_file)
        
        dirpath, filename = split(complete_dot_file)
        
        cpg_file_name = normpath(dirpath).split(sep)[-1]
        
        out_file = join(dirpath, (cpg_file_name + '.pkl'))
        
        try:
            with open(out_file, 'wb') as f:
                LOGGER.info('Saving .pkl file in %s', out_file)
                pickle.dump(cpg_embedding, f)
        except Exception as exc:
            LOGGER.error(exc)
            LOGGER.error('Error while saving the pickle file: %s', out_file)

    
    def _tokenize_nx_graph (self, tokenizer, dotfile):
        """Processes the graph in the .dot file to be used by the model

        Args:
            tokenizer (str): which tokenizer will be used to generate the embeddings
            dotfile (str): path to the dot file to be processed

        Returns:
            torch.Data: Data object containing the nodes/edges information to train
            the model
        """
        emb_length = 196

        edge_type_map = {
            "AST": 0,
            "CFG": 1,
            "DDG": 2,
            "CDG": 3
        }

        try:
            nodes = []
            edges = []
            edge_features = []
            edge_types = []

            label_node_map = {}
            label_code = dict()

            dot_graph = nx.drawing.nx_pydot.read_dot(dotfile)

            labels_dict = nx.get_node_attributes(dot_graph, 'label')

            for label, all_code in labels_dict.items():
                # TODO: check this processing step
                code = all_code[all_code.find("(") + 1:-14].split('\\n')[0]
                label_code[label] = code

            id = 0

            for label, code in label_code.items():
                label_node_map[int(label)] = id
                id += 1
                
                line_vec = self._tokenize_data(code, tokenizer, emb_length)
                
                max_length = 64
                
                sized_line_vec = [0] * max_length

                for i in range(0, min(len(line_vec), max_length) - 1):
                    sized_line_vec[i] = line_vec[i]

                nodes.append(sized_line_vec)

            for edge in dot_graph.edges(data=True):
                max_edge_length = 16
                
                sized_edge_vec = [0] * max_edge_length

                try:
                    edge_type_string = edge[2]["label"]
                    edge_vec = self._tokenize_data(edge_type_string, tokenizer, emb_length)

                    for i in range(0, min(len(edge_vec), max_edge_length) - 1):
                        sized_edge_vec[i] = edge_vec[i]
                except Exception as exc:
                    LOGGER.error(exc)
                    LOGGER.error("Error while generating the embeddings for the edge features!")
                
                edge_features.append(sized_edge_vec)

                edge_type = 0
                
                try:
                    edge_type_string = edge[2]["label"].replace("\"", "").split(":")[0]
                    edge_type = edge_type_map[edge_type_string]
                except Exception as exc:
                    LOGGER.error(exc)
                    LOGGER.error("Error while generating the embeddings for the edge type!")

                edge_types.append([edge_type])

                edges.append([label_node_map[int(edge[0])], label_node_map[int(edge[1])]])
            
            LOGGER.debug ('Generating embedding tensors...')

            data = Data(x=torch.tensor(nodes, dtype=torch.float),
                edge_index=torch.tensor(edges, dtype=torch.long).t().contiguous(),
                edge_attr=torch.tensor(edge_features, dtype=torch.float),
                edge_type=torch.tensor(edge_types, dtype=torch.long)
            )

            return data
        except Exception as exc:
            LOGGER.error(exc)

            return None


    def _tokenize_data(self, data, tokenizer, emb_length):
        """Tokenizes the data using a Transformer model

        Args:
            data (str): data to be processed
            tokenizer (str): which tokenizer will be used to generate the embeddings
            emb_length (_type_): length of the embedding to be generated

        Returns:
            str: generated embeddings
        """
        if(len(data) > emb_length):
            data = data[:emb_length]

        tokens = tokenizer.tokenize(data)

        return tokenizer.convert_tokens_to_ids(tokens)
