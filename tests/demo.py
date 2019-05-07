import json
import requests
import unittest
import pdb
import os, shutil
from os.path import dirname, realpath
import sys
sys.path.append(dirname(dirname(realpath(__file__))))
import oncoserve.aggregators.basic as aggregators

DOMAIN = "http://localhost:5000"

class Test_MIT_App(unittest.TestCase):

    def setUp(self):
        self.f1 = open("/home/yala/sample_dicoms/1.dcm", 'rb')
        self.f2 = open("/home/yala/sample_dicoms/2.dcm", 'rb')
        self.f3 = open("/home/yala/sample_dicoms/3.dcm", 'rb')
        self.f4 = open("/home/yala/sample_dicoms/4.dcm", 'rb')
        self.bad_f = open("/home/yala/sample_dicoms/bad.txt", 'rb')
        # Fake MRN
        self.MRN = '11111111'
        # Fake Accession
        self.ACCESSION = '2222222'
        self.METADATA = {'mrn':self.MRN, 'accession': self.ACCESSION}
        '''
            Example risk factors file in samples_data.
            Note, attaching risk_factors is only necessary for MIRAIv0.2 (i.e Hybril DL)
            Documentation explaining this file format is available at docs/RISK_FACTORS.md
        '''

        self.risk_factor_file = open('sample_data/risk_factors.json','r')



    def tearDown(self):
        try:
            self.f1.close()
            self.f2.close()
            self.f3.close()
            self.f4.close()
            self.risk_factor_file.close()
            self.bad_f.close()
        except Exception as e:
            pass

    def test_normal_request(self):
        '''
        Demo of how to use MIRAI. Note, this is applicable for all MIRAI applications.
        '''

        '''
         1. Load dicoms. Make sure to filter by view, MIRAI will not take responsibility for this.
        '''

        files = [('dicom',self.f1), ('dicom',self.f2), ('dicom',self.f3), ('dicom', self.f4)]
        '''
        1.5. Load risk factor metadata in case of models that also condition on
        traditional risk factor information like MIRAI v0.2 (i.e hybrid DL)
        '''
        files += [('risk_factors', self.risk_factor_file)]

        '''
        2. Send request to model at /serve with dicoms in files field, and any metadata in the data field.
        Note, files should contain a list of tuples:
         [ ('dicom': bytes), '(dicom': bytes)', ('dicom': bytes) ].
        Deviating from this may result in unexpected behavior.
        '''
        r = requests.post(os.path.join(DOMAIN,"serve"), files=files,
                          data=self.METADATA)
        '''
        3. Results will contain prediction, status, version info, all original metadata
        '''
        print(r.__dict__)
        self.assertEqual(r.status_code, 200)
        content = json.loads(r.content)
        self.assertEqual(content['metadata']['mrn'], self.MRN)
        self.assertEqual(content['metadata']['accession'], self.ACCESSION)

    def test_bad_dicom_request(self):
        # Example of failed request:
        '''
            1. Get faulty dicoms
        '''
        dicoms = [('dicom',self.f1), ('dicom', self.bad_f), ('dicom', self.f3), ('dicom', self.f4)]
        '''
            2. Send request to model at /serve with dicoms in files field, and any metadata in the data field
        '''
        r = requests.post( os.path.join(DOMAIN,"serve"), files=dicoms,
                          data=self.METADATA)
        '''
            3. Results will contain prediction == None, and an error code about
            which dicom couldn't convert
        '''
        print(r.__dict__)
        self.assertEqual(r.status_code, 500)
        content = json.loads(r.content)
        self.assertEqual(content['prediction'], None)
        self.assertEqual(content['metadata']['mrn'], self.MRN)
        self.assertEqual(content['metadata']['accession'], self.ACCESSION)


    def test_normal_request_flood(self):
        for _ in range(10):
            self.setUp()
            files = [('dicom',self.f1), ('dicom',self.f2), ('dicom',self.f3), ('dicom', self.f4), ('risk_factors', self.risk_factor_file)]
            r = requests.post(os.path.join(DOMAIN,"serve"), files=files,
                          data=self.METADATA)
            if not r.status_code == 200:
                print(r.__dict__)
            self.assertEqual(r.status_code, 200)
            content = json.loads(r.content)
            self.assertEqual(content['metadata']['mrn'], self.MRN)
            self.assertEqual(content['metadata']['accession'], self.ACCESSION)
            self.tearDown()




if __name__ == '__main__':
    unittest.main()
