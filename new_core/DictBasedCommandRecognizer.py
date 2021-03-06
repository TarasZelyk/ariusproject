from AbstractCommandRecognizer import AbstractCommandRecognizer

import sys
sys.path.append("../")
from logger import Logger
from config import config
logger = Logger("Core[CommandRecognizer]")


class DictBasedCommandRecognizer(AbstractCommandRecognizer):
    """
    This is a recognizer of commands which works with
    command dictionaries. It should be inited
    with a dict like {"COM1": [synonym_list]}.

    It will return on of the keys from
    the command dictionary.
    """
    def __init__(self, commands, finder):
        if type(commands) != dict:
            raise ValueError

        self._commands = commands
        self.__match_finder = finder
        self._min_confidence = config['core_command_recog_confidence']

    def setCommandsDict(self, commands_dict):
        if type(commands_dict) == dict:
            self._commands = commands_dict
            return
        raise ValueError('Argument must be a dictionary')

    def setBehavior(self, finder):
        self.__match_finder = finder

    def __get_confidence_of_match(self, string1, string2):
        return self.__match_finder.getMatch(string1, string2)

    def recognize_command(self, command):
        """
        This function is used to recognize commands in given text.
        It has two modes:
        1) Reconize command and return its type.
        2) Check if given command is in the input.

        First of all, assume that we have initialized FuzzyRecognizer
        object and named it rec. Now, let`s see how both types work:

        1) To detect any command you can just call this method with
        text you want to analyze, like here:

        print rec.recognize_command('some text inputed here')
        >>> 'COMMAND_A'
        And if FuzzyRecognizer will detect one or some commands
        it will return the command, with the highest probability
        level. In case, if command will not be recognized or
        recognizer`s confidence will be too low it will
        return None value.

        2) To check if the given text contains some specific
        command. To do it call method like in following example:

        >>> print rec.recognize_command(some_text, 'COMMAND_A')

        If probability level of given command is high enough True
        will be returned, if not - False.
        """
        logger.debug('COMMAND RECOGNIZING BEGAN')

        command_probability = {key: 0 for key in self._commands.keys()}

        for command_key in self._commands.keys():
            for case in self._commands[command_key]:
                N = len(case.split())

                pre_grams = command.split()
                grams = [' '.join(pre_grams[i:i + N])
                         for i in range(len(pre_grams) - N + 1)]

                for gram in grams:
                    confidence = self.__get_confidence_of_match(case, gram)
                    if confidence >= command_probability[command_key]:
                        command_probability[command_key] = confidence

        result = [key for key in command_probability.keys() if command_probability[key] == max(
            command_probability.values()) and command_probability[key] > self._min_confidence]

        logger.debug('The list of all available commands is: {}'.format(self._commands.keys()))
        logger.debug('The list of probabilities of each command is: {}'.format(command_probability))
        logger.debug('The list of found matching commands '
                     '(better if there`s only one item) is: {}'.format(result))

        if result:
            logger.info('Recognized command is {} and confidence for it is {}'
                        .format(result[0], command_probability[result[0]]))
            logger.debug('COMMAND RECOGNIZING FINISHED')
            return result[0]
        logger.info('Command was not recognized')
        logger.debug('COMMAND RECOGNIZING FINISHED')
        return None

    def check_for_command(self, data, command):
        if command not in self._commands.keys():
            logger.debug('Given wrong command: there`s no such command in the dictionary. Exiting')
            raise ValueError('Wrong command')
        for command in self._commands[command]:
            probability = self.__get_confidence_of_match(command, data)
            logger.debug('Probability of command {} for command case {} is {}'.format(
                command, command, probability))
            if probability >= self._min_confidence:
                logger.debug('Matching command found.')
                return True
        logger.info('Start phrase was not recognized')
        logger.debug('COMMAND RECOGNIZING FINISHED')
        return False

    def remove_command(self, input_str, command):
        """
        This method is used to remove command`s keywords from
        given text and return updated input.

        Here is an example of using this method:

        Let`s assume that when creating recognizer object you passed it such
        commands dictionary:
        command_dictionary = {'START': ['ok arius']}

        >>> rec.remove_command('ok auris could you tell me about enlarging the GDP', 'START')
        'could you tell me about enlarging the GDP'

        As you could see, method returns a string without a command.
        """
        logger.debug('STARTED CLEARING INPUT')
        if command is None:
            return input_str
        if command not in self._commands.keys():
            logger.info(
                'Given wrong command: there`s no such command in the dictionary. Exiting')
            raise ValueError('Wrong command')
        # indicator if smth was changed. Used for debug purposes only.
        replaced = False
        for case in self._commands[command]:
            logger.debug('Clearing for {} and string is "{}"'.format(case, input_str))
            N = len(case.split())

            pre_grams = input_str.split()
            grams = [' '.join(pre_grams[i:i + N])
                     for i in range(len(pre_grams) - N)]

            for gram in grams:
                confidence = self.__get_confidence_of_match(case, gram)
                if confidence >= self._min_confidence:
                    logger.debug('Confidence for {} is {}'.format(gram, confidence))
                    input_str = input_str.replace(gram, '')
                    input_str = input_str.strip()
                    logger.debug('String is "{}"'.format(input_str))
                    replaced = True
        if not replaced:
            logger.info('Nothing to replace')
            logger.info('String with removed command phrase is: "{}"'.format(input_str))
            logger.debug('FINISHED CLEARING INPUT')
        # as we can have a string like 'test   test word' lets replace
        # all multiple whitespaces with one. The easiest way to achive
        # this and avoid RE is to use splitting string to a list and then
        # joining it with one whitespace. All multiple whitespaces won`t be
        # in the list as they are not treated as separate tokens while
        # splitting.
        return ' '.join(input_str.split())
