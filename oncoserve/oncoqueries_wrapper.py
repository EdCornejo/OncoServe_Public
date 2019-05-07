import os
import uuid
import oncoserve.logger
from onconet.utils.risk_factors import RiskFactorVectorizer
import json
import subprocess
import pdb


FAIL_TO_SAVE_METADATA_MESSAGE = 'OncoQueries- Fail to save metadata json for ssn: {}, accession: {}. Caused Exception {} with args: {}'
FAIL_TO_SAVE_RISK_METADATA_MESSAGE = 'OncoQueries- Fail to save risk_metadata json for ssn: {}, accession: {}. Caused Exception {} with args: {}'
FAIL_TO_GET_RISK_VECTOR_MESSAGE = 'OncoQueries- Fail to get risk_factor_vector given metadatas for ssn: {}, accession: {}. Caused Exception {} with args: {}'
SUCCESS_RISK_VEC_MESSAGE = 'OncoQueries- Succesffuly obtained risk_factor_vector for ssn: {}, accession: {} with args: {}'


def delete_jsons(args):
    for path in [args.metadata_path, args.risk_factor_metadata_path]:
        if os.path.exists(path):
            os.remove(path)

def get_risk_factors(args, ssn, exam, risk_metadata_json, json_dir, logger):
    '''
    args:
        - args:
        - ssn:
        - exam:
        - json_dir:
        - logger:
    returns:
        - risk_factor_vector:
    '''
    try:
        os.makedirs(json_dir)
    except Exception as e:
        pass
    args.metadata_path = "{}.json".format(os.path.join(json_dir, str(uuid.uuid4())))
    args.risk_factor_metadata_path = "{}.json".format(os.path.join(json_dir, str(uuid.uuid4())))

    # Write current request to a file to use as a metadata path
    prior_hist = risk_metadata_json[ssn]['any_breast_cancer'] == 1
    metadata_json = [{'ssn':ssn, 'accessions':[
                                        {'accession':exam,
                                        'prior_hist': prior_hist}]}]


    try:
        json.dump(metadata_json, open(args.metadata_path,'w'))
        json.dump(risk_metadata_json, open(args.risk_factor_metadata_path,'w'))
    except Exception as e:
        delete_jsons(args)
        err_msg = FAIL_TO_SAVE_METADATA_MESSAGE.format(ssn, exam, e, args)
        logger.error(err_msg)
        raise Exception(err_msg)

    # Load risk factor vector from metadata file and del metadata json
    try:
        risk_factor_vectorizer = RiskFactorVectorizer(args)
        sample = {'ssn': ssn, 'exam': exam}
        risk_factor_vector = risk_factor_vectorizer.get_risk_factors_for_sample(sample)
        logger.info(SUCCESS_RISK_VEC_MESSAGE.format(ssn, exam, args))
        delete_jsons(args)
        return risk_factor_vector
    except Exception as e:
        delete_jsons(args)
        err_msg = FAIL_TO_GET_RISK_VECTOR_MESSAGE.format(ssn, exam, e, args)
        logger.error(err_msg)
        raise Exception(err_msg)



