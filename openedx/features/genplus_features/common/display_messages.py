class SuccessMessages:
    CHARACTER_SELECTED = 'Your character has been selected.'
    PASSWORD_CHANGED = 'Password changed successfully.'
    PASSWORD_CHANGED_BY_TEACHER = 'Password changed for {users} successfully.'
    PROFILE_IMAGE_UPDATED = 'Your profile image has been updated successfully.'
    CLASS_ADDED_TO_FAVORITES = '{class_name} has been added to your classes.'
    CLASS_REMOVED_FROM_FAVORITES = '{class_name} has been removed from your classes.'
    LESSON_UNLOCKED = 'Lesson unlocked successfully.'
    STUDENT_POST_CREATED = 'Your journal post has been added successfully.'
    TEACHER_FEEDBACK_ADDED = 'Your feedback has been added successfully.'
    STUDENT_POST_UPDATED = 'Your journal post has been updated successfully.'
    TEACHER_FEEDBACK_UPDATED = 'Your feedback has been updated successfully.'
    # genplus teach
    ARTICLE_ADDED_TO_FAVORITES = '{title} has been added to your favorite articles.'
    ARTICLE_REMOVED_FROM_FAVORITES = '{title} has been removed from your favorite articles.'
    ARTICLE_RATED = "Thanks for the rating."
    BADGE_AWARDED = 'Feedback/badges have been awarded successfully.'
    REFLECTION_ADDED = "Reflection Submitted."
    PORTFOLIO_ENTRY_ADDED = "Entry added to portfolio successfully."


class ErrorMessages:
    INTERNAL_SERVER = 'Some error occur on the server. The request can not be completed for now.'
    OLD_PASSWORD_ERROR = "Your old password was entered incorrectly. Please enter it again."
    NEW_SAME_AS_OLD_PASSWORD_ERROR = "Your new password cannot be the same as old one. Please enter a different one."
    ACTION_VALIDATION_ERROR = 'Action can only be add or remove'
    CLASS_ALREADY_ADDED = '{class_name} is already added in your classes.'
    LESSON_ALREADY_UNLOCKED = 'You cannot lock the lesson which is already unlocked.'
    STUDENT_POST_ENTRY_FAILED = 'Journal post could not be added.'
    TEACHER_FEEDBACK_ENTRY_FAILED = 'Your feedback could not be added to this journal.'
    STUDENT_POST_UPDATE_FAILED = 'Your journal post could not be updated.'
    TEACHER_FEEDBACK_UPDATE_FAILED = 'Your feedback could not be updated.'
    # genplus_teach messages
    ARTICLE_ALREADY_ADDED = 'This article is already added to your favorite.'
    ARTICLE_ALREADY_RATED = 'You have already rated this article.'
    MAX_FAVORITE = 'You can only favorite {max} articles at a time.'
    NOT_A_PART_OF_PROGRAMME = 'You are currently not a part of any programme.'
