TOTAL_PROBLEM_SCORE = 5
MAX_SKILLS_SCORE = 15
INTRO_RATING_ASSESSMENT_RESPONSE = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
OUTRO_RATING_ASSESSMENT_RESPONSE = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

class ProblemTypes:
    JOURNAL = 'journal_responses'
    SKILL_ASSESSMENT = 'skill_assessment'
    SINGLE_CHOICE  = 'single_choice'
    MULTIPLE_CHOICE = 'multiple_choice'
    SHORT_ANSWER = 'short_answers'

    __ALL__ = (JOURNAL, SKILL_ASSESSMENT, SINGLE_CHOICE, MULTIPLE_CHOICE, SHORT_ANSWER,)
    STRING_TYPE_PROBLEMS = (JOURNAL, SHORT_ANSWER,)
    CHOICE_TYPE_PROBLEMS = (SINGLE_CHOICE, MULTIPLE_CHOICE,)
    SHOW_IN_STUDENT_ANSWERS_PROBLEMS = (SINGLE_CHOICE, MULTIPLE_CHOICE, SHORT_ANSWER,)

class SkillAssessmentTypes:

    """
    Skill Assessment choices for the classes
    """
    SINGLE_CHOICE = 'single_choice'
    MULTIPLE_CHOICE = 'multiple_choice'
    RATING = 'rating'

    __ALL__ = (SINGLE_CHOICE, MULTIPLE_CHOICE, RATING)
    __MODEL_CHOICES__ = (
        (skill_assessment_type, skill_assessment_type) for skill_assessment_type in __ALL__
    )

class SkillAssessmentResponseTime:

    """
    Skill Assessment choices for the classes
    """
    START_OF_YEAR = 'start_of_year'
    END_OF_YEAR = 'end_of_year'

    __ALL__ = (START_OF_YEAR, END_OF_YEAR)
    __MODEL_CHOICES__ = (
        (response_time, response_time) for response_time in __ALL__
    )

JOURNAL_STYLE = '''{{"blocks":[{{"key":"540nn","text":"{0}","type":"unstyled","depth":0,"inlineStyleRanges":[],"entityRanges":[],"data":{{}}}}],"entityMap":{{}}}}'''
