import logging
import pickle
import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import oncoserve.logger
import onconet.utils.parsing as parsing
from  onconet.transformers.basic import ComposeTrans
import  onconet.transformers.factory as transformer_factory
import oncoserve.aggregators.factory as aggregator_factory
import pdb

INIT_MESSAGE = "OncoNet- Initializing OncoNet Wrapper..."
TRANSF_MESSAGE = "OncoNet- Transfomers succesfully composed"
MODEL_MESSAGE = "OncoNet- Model successfully loaded from : {}"
AGGREGATOR_MESSAGE = "OncoNet- Aggregator [{}] succesfully loaded"
IMG_START_CLASSIF_MESSAGE = "OncoNet- Image classification start with tensor size {}"
IMG_FINISH_CLASSIF_MESSAGE = "OncoNet- Image classification produced {}"
EXAM_CLASSIF_MESSAGE = "OncoNet- Exam classification complete!"
ERR_MSG = "OncoNet- Fail to label exam. Exception: {}"

class OncoNetWrapper(object):
    def __init__(self, args, aggregator_name, logger):
        logger.info(INIT_MESSAGE)
        self.args = args
        args.cuda = args.cuda and torch.cuda.is_available()
        args.test_image_transformers = parsing.parse_transformers(args.test_image_transformers)
        args.test_tensor_transformers = parsing.parse_transformers(args.test_tensor_transformers)
        test_transformers = transformer_factory.get_transformers(
            args.test_image_transformers, args.test_tensor_transformers, args)


        self.transformer = ComposeTrans(test_transformers)
        logger.info(TRANSF_MESSAGE)
        self.model = torch.load(args.snapshot, map_location='cpu')
        # Unpack models taht were trained as data parallel
        if isinstance(self.model, nn.DataParallel):
            self.model = self.model.module
        # Add use precomputed hiddens for models trained before it was introduced. 
        # Assumes a resnet base backbone
        try:
            self.model._model.args.use_precomputed_hiddens = args.use_precomputed_hiddens
            self.model._model.args.cuda = args.cuda
        except Exception as e:
            pass
        # Load callibrator if desired 
        if args.callibrator_path is not None:
            self.callibrator = pickle.load(open(args.callibrator_path,'rb'))
        else:
            self.callibrator = None

        logger.info(MODEL_MESSAGE.format(args.snapshot))
        self.aggregator = aggregator_factory.get_exam_aggregator(aggregator_name)

        self.logger = logger


    def process_image(self, image, risk_factor_vector=None):
        try:
            ## Apply transformers
            x = self.transformer(image, self.args.additional)
            x = autograd.Variable(x.unsqueeze(0))
            risk_factors = autograd.Variable(risk_factor_vector.unsqueeze(0)) if risk_factor_vector is not None else None
            self.logger.info(IMG_START_CLASSIF_MESSAGE.format(x.size()))
            if self.args.cuda:
                x = x.cuda()
                self.model = self.model.cuda()
                if risk_factor_vector is not None:
                    risk_factors = risk_factors.cuda()
            else:
                self.model = self.model.cpu()
            ## Index 0 to toss batch dimension
            pred_y = F.softmax(self.model(x, risk_factors)[0])[0]
            pred_y = np.array(self.args.label_map( pred_y.cpu().data.numpy() ))
            if self.callibrator is not None:
                pred_y = self.callibrator.predict_proba(pred_y.reshape(-1,1))[0,1]
            self.logger.info(IMG_FINISH_CLASSIF_MESSAGE.format(pred_y))
            return pred_y
        except Exception as e:
            err_msg = ERR_MSG.format(e)
            raise Exception(err_msg)

    def process_exam(self, images, risk_factor_vector):
        preds = []
        for im in images:
            preds.append(self.process_image(im, risk_factor_vector))
        y = self.aggregator(preds)
        if isinstance(y, np.generic):
            y = y.item()
        self.logger.info(EXAM_CLASSIF_MESSAGE)
        return y
