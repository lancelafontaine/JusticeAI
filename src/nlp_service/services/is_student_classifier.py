# -*- coding: utf-8 -*-
from services.gram_classifier import GramClassifier
import os


class IsStudentClassifier(GramClassifier):
    inputFiles = ['true', 'false']

    """docstring for IsStudentClassifier"""

    def __init__(self, forceTrain=False):
        baseName = os.path.basename(__file__).split(".")[0]
        super().__init__(baseName,
                         IsStudentClassifier.inputFiles,
                         forceTrain)

    def classify(self, questionInput):
        output = super().classify(questionInput)
        return {'is_student': output}
