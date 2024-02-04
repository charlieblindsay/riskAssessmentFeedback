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

import openai
import requests

from typing import Type

import os
from dotenv import load_dotenv

try:
    from .PromptInputs import *
except ImportError:
    from PromptInputs import *

class LLMCaller:
    def __init__(self):
        pass
         # NOTE: Don't need to pass self as input to calls of methods within a class 
         # as it is automatically passed in, i.e. it is not self.update_api_key_from_env_file(self) but:

    def update_api_key_from_env_file(self):
        pass

    def get_prompt_input(self, prompt_input: Type[PromptInput]):
        return prompt_input.generate_prompt()
    
    def get_JSON_output_from_API_call(self, prompt_input: Type[PromptInput]):
        pass

    def get_model_output(self):
        pass

class HuggingfaceLLMCaller(LLMCaller):
    def __init__(self, LLM_API_ENDPOINT):
        self.LLM_API_ENDPOINT = LLM_API_ENDPOINT
        self.update_api_key_from_env_file()
    
    def update_api_key_from_env_file(self):
        load_dotenv()
        self.HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

class LLMWithGeneratedText(HuggingfaceLLMCaller):
    def __init__(self, LLM_API_ENDPOINT):
        super().__init__(LLM_API_ENDPOINT)
    
    def get_JSON_output_from_API_call(self, prompt_input: Type[PromptInput]):
        headers = {"Authorization": f"Bearer {self.HUGGINGFACE_API_KEY}"}
        prompt = prompt_input.generate_prompt()
        payload = {"inputs": prompt,
                   "options": {"wait_for_model": True}}
        return requests.post(self.LLM_API_ENDPOINT, 
                             headers=headers, 
                             json=payload).json()
    
    def get_model_output(self, prompt_input: Type[PromptInput]):
        LLM_output = self.get_JSON_output_from_API_call(prompt_input)
        return LLM_output[0]['generated_text']
    
class LLMWithCandidateLabels(HuggingfaceLLMCaller):
    def __init__(self, LLM_API_ENDPOINT):
        super().__init__(LLM_API_ENDPOINT)
    
    def get_JSON_output_from_API_call(self, prompt_input: Type[PromptInput]):
        headers = {"Authorization": f"Bearer {self.HUGGINGFACE_API_KEY}"}
        prompt = prompt_input.generate_prompt()
        payload = {"inputs": prompt,
                "parameters": {"candidate_labels": prompt_input.candidate_labels},
                "options": {"wait_for_model": True}}
        return requests.post(self.LLM_API_ENDPOINT, 
                             headers=headers, 
                             json=payload).json()

    def get_model_output(self, prompt_input: Type[PromptInput]):
        LLM_output = self.get_JSON_output_from_API_call(prompt_input)
        max_score_index = LLM_output['scores'].index(max(LLM_output['scores']))
        predicted_label = LLM_output['labels'][max_score_index]

        return predicted_label

class OpenAILLM(LLMCaller):
    def __init__(self):
        self.update_api_key_from_env_file()
        self.temperature = 0.5
        self.max_tokens = 300

    def update_api_key_from_env_file(self):
        load_dotenv()
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    def get_JSON_output_from_API_call(self, prompt_input: Type[PromptInput]):

        prompt = self.get_prompt_input(prompt_input=prompt_input)
        
        messages = [{"role": "user", "content": prompt}]

        # TODO: Vary max_tokens based on prompt and test different temperatures.
        # NOTE: Lower temperature means more deterministic output.
        LLM_output = openai.ChatCompletion.create(model="gpt-3.5-turbo", 
                                                  messages=messages, 
                                                  temperature=self.temperature, 
                                                  max_tokens=self.max_tokens)
        
        return LLM_output
    
    def get_model_output(self, prompt_input: Type[PromptInput]):
        LLM_output = self.get_JSON_output_from_API_call(prompt_input)
        return LLM_output.choices[0].message["content"]

try:
    from RiskAssessment import RiskAssessment
    # from LLMCaller import LLMWithCandidateLabels, LLMWithGeneratedText
except:
    from .RiskAssessment import RiskAssessment
    # from .LLMCaller import LLMWithCandidateLabels, LLMWithGeneratedText, OpenAILLM

class Params(TypedDict):
    pass

class Result(TypedDict):
    is_correct: bool
    feedback: str

def evaluation_function(response: Any, answer: Any, params: Any) -> Result:
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
    
    input_check_feedback_message = RA.get_input_check_feedback_message()
    controlled_risk = RA.check_controlled_risk()
    uncontrolled_risk = RA.check_uncontrolled_risk()

    if input_check_feedback_message != '':
        return Result(is_correct=False,
                    feedback=f'Feedback: \n\n {input_check_feedback_message}')
    
    if input_check_feedback_message == '' and controlled_risk != 'correct' or uncontrolled_risk != 'correct':
        return Result(is_correct=False,
                      feedback=f'Feedback: \n\n Uncontrolled risk is: {controlled_risk}\n\nUncontrolled risk is {uncontrolled_risk}')
    
    else:
        LLM = OpenAILLM()
        fields_checked = RA.get_list_of_fields_checked()
        prompt_input_objects = RA.get_list_of_prompt_input_objects()
        prompts = RA.get_list_of_prompts()
        prompt_outputs = RA.get_list_of_prompt_outputs(LLM)
        regex_matches = RA.get_list_of_regex_matches(prompt_outputs)
        shortform_feedbacks = RA.get_list_of_shortform_feedback_from_regex_matches(regex_matches)
        is_everything_correct = RA.are_all_prompt_outputs_correct(prompt_outputs) and RA.are_all_multiplications_correct()
        booleans_indicating_which_prompts_need_feedback = RA.get_booleans_indicating_which_prompts_need_feedback(regex_matches)

        feedback = ''''''
        full_feedback = ''''''
        
        n_prompts = len(prompts)

        most_pertinent_feedback_already_shown = False

        for i in range(n_prompts):
            field = fields_checked[i]
            shortform_feedback = shortform_feedbacks[i]
            definitions_to_look_at = field
            longform_feedback = prompt_input_objects[i].get_longform_feedback(prompt_output=prompt_outputs[i])
 
            if field == 'Prevention':
                if regex_matches[i] == 'mitigation':
                    longform_feedback = prompt_input_objects[i].get_longform_feedback(prompt_output=prompt_outputs[i], pattern_to_search_for='Mitigation Explanation',lookahead_assertion='Answer')
                    definitions_to_look_at = 'Prevention and Mitigation'
            if field == 'Mitigation':
                if regex_matches[i] == 'prevention':
                    longform_feedback = prompt_input_objects[i].get_longform_feedback(prompt_output=prompt_outputs[i], pattern_to_search_for='Prevention Explanation',lookahead_assertion='Mitigation')
                    definitions_to_look_at = 'Prevention and Mitigation'

            feedback_header_to_add = f' ## Feedback for Input{"s" if field == "Hazard & How it harms" else ""}: {fields_checked[i]}'
            feedback_to_add = f'''
                        - **Feedback:** {shortform_feedback}
                        - **Explanation:** {longform_feedback}'
                        '''
            
            if booleans_indicating_which_prompts_need_feedback[i] == True:
                feedback_to_add += f'''
                            - **Recommendation**: Please look at the definition of the {definitions_to_look_at} input field{'s' if definitions_to_look_at in ['Hazard & How it harms', 'Prevention and Mitigation'] else ''} and the example risk assessment for assistance.
                            '''
                
            if booleans_indicating_which_prompts_need_feedback[i] == True and most_pertinent_feedback_already_shown == False:
                feedback += feedback_header_to_add

                feedback += feedback_to_add + '\n\n\n\n\n'

                most_pertinent_feedback_already_shown = True
                
            full_feedback += feedback_header_to_add
            full_feedback += feedback_to_add
        
        full_feedback += f'''
        - Uncontrolled risk multiplication is: {uncontrolled_risk}
        - Controlled risk multiplication is: {controlled_risk}'''
        
        return Result(is_correct=is_everything_correct, feedback=feedback + full_feedback)