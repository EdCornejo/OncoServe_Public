## Risk Factor File Structure

The risk factor file, as used by OncoNet, assumes the following structure.

It is a dictionary of:
```
{ 'MRN_AS_PASSED_IN_METADATA': {
    'acessions': {
        'ACCESSION_OF_EXAM_AS_PASSED_IN_METADATA': {
            ... Exam specific risk factors, like age, weight, density ...
        }
    }
    ... patient specific risk factors like race, num births
}}
```

## Risk Factor Semantics

The semantics of each risk factor variable follows the Tyrer-Cuzick v8 model.  The ages attached to some risk factors, like `biopsy_LCIS_age` are to enable the model to ignore risk factors that happen in the future. The model will always make predictions based on what is known at the time of the exam (as marked by the exam age)


### Race Mapping
```
RACE_CODE_TO_NAME = {
    1: 'White',
    2: 'African American',
    3: 'American Indian, Eskimo, Aleut',
    4: 'Asian or Pacific Islander',
    5: 'Other Race',
    6: 'Caribbean/West Indian',
    7: 'Unknown',
    8: 'Hispanic',
    9: 'Chinese',
    10: 'Japanese',
    11: 'Filipino',
    12: 'Hawaiian',
    13: 'Other Asian'
}
```

## Questions?
Please reach out to adamyala@mit.edu or post an issue with any questions. We will continue to update this document based on your questions.


