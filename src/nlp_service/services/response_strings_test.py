import unittest

from services.response_strings import Responses


class TestResponse(unittest.TestCase):
    def setUp(self):
        self.responseInstance = Responses()

    def test_fact_responses(self):
        question = Responses.fact_question("apartment_dirty")
        self.assertTrue(question in self.responseInstance.fact_questions["apartment_dirty"])

    def test_fact_responses_empty(self):
        question = Responses.fact_question("does_not_exist")
        self.assertTrue(question in self.responseInstance.fact_questions["missing_response"])

    def test_faq_statement_common(self):
        statement_landlord = Responses.faq_statement("faq_rlq_noisy_tenant", "LANDLORD")
        statement_tenant = Responses.faq_statement("faq_rlq_noisy_tenant", "TENANT")

        self.assertTrue(statement_landlord in Responses.static_claim_responses["faq_rlq_noisy_tenant"]["LANDLORD"])
        self.assertTrue(statement_tenant in Responses.static_claim_responses["faq_rlq_noisy_tenant"]["TENANT"])

    def test_faq_statement_single(self):
        statement_tenant = Responses.faq_statement("faq_likehome_landlord-harass", "TENANT")
        self.assertTrue(statement_tenant in Responses.static_claim_responses["faq_likehome_landlord-harass"]["TENANT"])

    def test_faq_statement_missing(self):
        statement_landlord = Responses.faq_statement("faq_likehome_landlord-harass", "LANDLORD")
        self.assertTrue(statement_landlord in Responses.static_claim_responses["missing_response"])

    def test_responses_prediction(self):
        prediction = Responses.prediction_statement({"orders_resiliation": 1}, [])
        self.assertTrue(prediction in self.responseInstance.prediction["orders_resiliation"][True])

    def test_responses_prediction_false(self):
        prediction = Responses.prediction_statement({"orders_resiliation": 0}, [])
        self.assertTrue(prediction in self.responseInstance.prediction["orders_resiliation"][False])

    def test_responses_prediction_empty(self):
        question_empty_predictions = Responses.prediction_statement({}, [])
        self.assertTrue(question_empty_predictions in self.responseInstance.prediction["cant_predict"])

    def test_responses_prediction_precedent(self):
        question = Responses.prediction_statement({"orders_resiliation": 1}, [
            {
                "precedent": "AZ-11111",
                "distance": 1.5
            }
        ])
        self.assertIn("AZ-11111", question)

    def test_responses_prompt_additional(self):
        prompt = Responses.prompt_additional_questions(5)
        self.assertIsNotNone(prompt)

    def test_responses_prompt_reset_flow(self):
        prompt1 = Responses.prompt_reset_flow("landlord")
        prompt2 = Responses.prompt_reset_flow("landlord", separate_message=True)
        self.assertIsNotNone(prompt1)
        self.assertIsNotNone(prompt2)
