# Low hanging fruit:
# TODO: Improve few shot prompting examples so they don't parrot back input prompt
# TODO: Try using chain of thought prompt engineering for the mitigation prompt
# TODO: Try using Llama inference endpoint
# TODO: Try using Llama inference API but specify the number of tokens you want to receive
# TODO: Update question description in lambda feedback making it clear that 
# only one mitigation, one prevention and one 'how it harms' is specified

# Add option in RiskAssessment to specify whether prevention is misclassified as mitigation, 
# is not a suitable prevention, or mitigation is misclassified as prevention, or is not a suitable mitigation

from typing import Any, TypedDict
import numpy as np

try:
    from .RiskAssessment import RiskAssessment
    from .LLMCaller import LLMWithCandidateLabels, LLMWithGeneratedText, OpenAILLM
except:
    from RiskAssessment import RiskAssessment
    from LLMCaller import LLMWithCandidateLabels, LLMWithGeneratedText

class Params(TypedDict):
    pass

class Result(TypedDict):
    is_correct: bool
    feedback: str

def evaluation_function(response: Any, answer: Any, params: Params) -> Result:
    """
    Function used to evaluate a student response.
    ---
    The handler function passes three arguments to evaluation_function():

    - `response` which are the answers provided by the student.
    - `answer` which are the correct answers to compare against.
    - `params` which are any extra parameters that may be useful,
        e.g., error tolerances.

    The output of this function is what is returned as the API response
    and therefore must be JSON-encodable. It must also conform to the
    response schema.

    Any standard python library may be used, as well as any package
    available on pip (provided it is added to requirements.txt).

    The way you wish to structure you code (all in this function, or
    split into many) is entirely up to you. All that matters are the
    return types and that evaluation_function() is the main function used
    to output the evaluation response.
    """

    activity, hazard, who_it_harms, how_it_harms, uncontrolled_likelihood, uncontrolled_severity, uncontrolled_risk, prevention, mitigation, controlled_likelihood, controlled_severity, controlled_risk = np.array(response).flatten()

    RA = RiskAssessment(activity=activity, hazard=hazard, who_it_harms=who_it_harms, how_it_harms=how_it_harms,
                        uncontrolled_likelihood=uncontrolled_likelihood, uncontrolled_severity=uncontrolled_severity,
                        uncontrolled_risk=uncontrolled_risk, prevention=prevention, mitigation=mitigation,
                        controlled_likelihood=controlled_likelihood, controlled_severity=controlled_severity, controlled_risk=controlled_risk,
                        prevention_prompt_expected_output='prevention', mitigation_prompt_expected_output='mitigation')
    
    if RA.get_input_check_feedback_message() != '':
        return Result(is_correct=False, feedback= RA.get_input_check_feedback_message())
    
    else:
        LLM = OpenAILLM()

        question_titles = RA.get_list_of_question_titles()
        questions = RA.get_list_of_questions()
        prompts = RA.get_list_of_prompts()
        prompt_outputs = RA.get_list_of_prompt_outputs(LLM)
        regex_matches = RA.get_list_of_regex_matches(prompt_outputs)
        shortform_feedbacks = RA.get_list_of_shortform_feedback_from_regex_matches(regex_matches)
        is_everything_correct = RA.are_all_prompt_outputs_correct(prompt_outputs) and RA.are_all_multiplications_correct()
        booleans_indicating_which_prompts_need_feedback = RA.get_booleans_indicating_which_prompts_need_feedback(regex_matches)

        feedback = f'''
        ------ FEEDBACK ------\n\n
        '''

        for i in range(len(prompts)):
            question_title = question_titles[i]
            prompt_output = prompt_outputs[i]
            shortform_feedback = shortform_feedbacks[i]

            feedback += f'--- Q{i + 1}: {question_title} ---\n\n'
            feedback += f'Feedback {i + 1}: {shortform_feedback}\n\n'
            if booleans_indicating_which_prompts_need_feedback[i] == True:
                feedback += f'Explanation {i + 1}: {prompt_output}\n\n\n'

        feedback += f'--- Controlled risk multiplication is: {RA.check_controlled_risk()} ---\n\n'
        feedback += f'--- Uncontrolled risk multiplication is: {RA.check_uncontrolled_risk()} ---\n\n'

        return Result(is_correct=is_everything_correct, feedback=feedback)