from TestModelAccuracy import TestProtectiveBarrierMitigationPrompt
from LLMCaller import OpenAILLM
from example_risk_assessments_exemplar import example_risk_assessments 

from ExamplesGenerator import RiskAssessmentExamplesGeneratorForMultiplePrompts

if __name__ == '__main__':

    examples_generator = RiskAssessmentExamplesGeneratorForMultiplePrompts(risk_assessments=example_risk_assessments,
                                                         ground_truth_parameter='mitigation_protected_clothing_expected_output',
                                                        method_to_get_prompt_input='get_mitigation_protective_barrier_input')
    
    examples = examples_generator.get_risk_assessment_and_expected_output_list()

    test_accuracy = TestProtectiveBarrierMitigationPrompt(
        test_description="""Testing mitigation input on protective barrier prompt in student Fluids Lab and TPS presentation Risk Assessment examples.
        
                            First time testing with hazard event and harm caused inputs.
                            
                            Added the word "physical" before barrier""",
                                      LLM=OpenAILLM(),
                                                LLM_name='gpt-3.5-turbo',
                                                list_of_risk_assessment_and_expected_outputs=examples,
                                                sheet_name='Combined Mitigation Protected Clothing')
    test_accuracy.run_test()