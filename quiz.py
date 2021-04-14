import asyncio
import random
import re
import unidecode
import os
import numpy as np

#todo: probably need to remove punctuation from answers



class Quiz:
    
    def __init__(self, win_limit=np.inf, question_time=np.inf, hint_time=np.inf):
        #initialises the quiz
        self.__running = False
        self.current_question = None
        self._win_limit = win_limit
        self._question_time = question_time
        self._hint_time = hint_time
        self._questions = []
        self._asked = []
        self.scores = {}
        self._cancel_callback = True
        self.current_successes = {}
       
        
        #load in some questions
        folder = 'weare'
        datafiles = os.listdir(folder)
        for df in datafiles:
            filepath = folder + os.path.sep + df
            self._load_questions(filepath)
            print('Loaded: ' + filepath)
        print('Quiz data loading complete.\n')
        
    
    
    def _load_questions(self, question_file):
        # loads in the questions for the quiz
        with open(question_file, encoding='utf-8',errors='replace') as qfile:
            lines = qfile.readlines()
            
        question = None
        category = None
        answer = None      
        regex = None
        score = 10
        allow_multiple_attempts = False
        allow_multiple_successes = True
        position = 0
        
        while position < len(lines):
            if lines[position].strip().startswith('#'):
                #skip
                position += 1
                continue
            if lines[position].strip() == '': #blank line
                #add question
                if question is not None and answer is not None:
                    q = Question(question=question, answer=answer, score=score,
                                 allow_multiple_successes=allow_multiple_successes, allow_multiple_attempts=allow_multiple_attempts,
                                 category=category, regex=regex) 
                    # print("appeeend", q.question, "\n\n")
                    self._questions.append(q)
                    
                #reset everything
                question = None
                category = None
                answer = None
                regex = None
                score = 10
                allow_multiple_attempts = False
                allow_multiple_successes = True
                position += 1
                continue
                
            if lines[position].strip().lower().startswith('category'):
                category = lines[position].strip()[lines[position].find(':') + 1:].strip()
            elif lines[position].strip().lower().startswith('question'):
                question = lines[position].strip()[lines[position].find(':') + 1:].strip()
            elif lines[position].strip().lower().startswith('answer'):
                answer = lines[position].strip()[lines[position].find(':') + 1:].strip()
            elif lines[position].strip().lower().startswith('regexp'):
                regex = lines[position].strip()[lines[position].find(':') + 1:].strip()
            elif lines[position].strip().lower().startswith('score'):
                score = int(lines[position].strip()[lines[position].find(':') + 1:].strip())
            elif lines[position].strip().lower().startswith('first'):
                allow_multiple_successes = (lines[position].strip()[lines[position].find(':') + 1:].strip()).lower() in ["true", "vrai", "t", "v"]            
            elif lines[position].strip().lower().startswith('multiple'):
                allow_multiple_attempts = (lines[position].strip()[lines[position].find(':') + 1:].strip()).lower() in ["true", "vrai", "t", "v"]
            #else ignore
            position += 1
                
    
    def started(self):
        #finds out whether a quiz is running
        return self.__running
    
    
    def question_in_progress(self):
        #finds out whether a question is currently in progress
        return self.__current_question is not None
    
    
    async def _timeout(self, ctx, timed_question):
        #stops the question when time is out
        if self.__running and self.current_question is not None:
            await asyncio.sleep(self._question_time)
            if (self.current_question == timed_question 
                 and self._cancel_callback == False):                
                await ctx.send('Le temps est écoulé.')
                await self.conclude_question(ctx)

    async def _hint(self, ctx, hint_question, hint_number):
        #offers a hint to the user
        if self.__running and self.current_question is not None:
            await asyncio.sleep(self._hint_time)
            if (self.current_question == hint_question 
                 and self._cancel_callback == False):
                if (hint_number >= 5):
                    await self.conclude_question(ctx)
                
                hint = self.current_question.get_hint(hint_number)
                await ctx.send('Hint {}: {}'.format(hint_number, hint))
                if hint_number < 5:
                    await self._hint(ctx, hint_question, hint_number + 1) 
    
    
    async def start(self, ctx):
        #starts the quiz in the channel.
        if self.__running:
            #don't start again
            await ctx.send( 
             'Un quiz est en cours, vous pouvez l\'arrêter avec !stop')
        else:
            await self.reset()
            # await ctx.send('@here Quiz starting in 10 seconds...')
            # await asyncio.sleep(10)
            self.__running = True
            await self.ask_question(ctx)
            
            
    async def reset(self):
        if self.__running:
            #stop
            await self.stop()
        
        #reset the scores
        self.current_question = None
        self._cancel_callback = True
        self.__running = False
        self._questions.extend(self._asked)
        self._asked = []
        self.scores = {}
            
            
    async def stop(self, ctx):
        #stops the quiz from running
        if self.__running:
            #print results
            #stop quiz
            await ctx.send('Fin du quiz')
            if(self.current_question is not None):
                await ctx.send(
                     'La réponse était : {}'.format(self.current_question.get_answer()))
            await self.print_scores(ctx)
            self.current_question = None
            self._cancel_callback = True
            self.__running = False            
    
    async def ask_question(self, ctx):
        #asks a question in the quiz
        if self.__running:
            self.current_successes = {}
            if len(self._questions) > 0:
                self.current_question = self._questions[0]
                self._questions.remove(self.current_question)
                self._asked.append(self.current_question)
                await ctx.send("_______________")
                await ctx.send( 
                 'Question ' + str(len(self._asked)) + " pour " + str(self.current_question.score) + ' points : ' + self.current_question.ask_question())
                self._cancel_callback = False
                await self._timeout(ctx, self.current_question)
                await self._hint(ctx, self.current_question, 1)
            else:
                await self.stop(ctx)
            
            
    async def next_question(self, ctx):
        if self.current_question is not None:
            await self.conclude_question(ctx)
        await self.ask_question(ctx)
            
            
    async def skip_question(self, ctx):
        #skip this question
        if self.__running:
            await ctx.send(
                     'La réponse était : {}. Passons à la prochaine question !'.format(self.current_question.get_answer()))
            self.current_question = None
            self._cancel_callback = True
            await self.ask_question(ctx)
            
            
            
    async def answer_question(self, ctx):
        #checks the answer to a question
        if self.__running and self.current_question is not None:
            if self.current_question.allow_multiple_attempts or ctx.message.author not in self.current_successes.keys():
                if self.current_question.answer_correct(ctx.message.content):
                    #record success
                    self.current_successes[ctx.message.author] = True
                    if not self.current_question.allow_multiple_successes:
                        self._cancel_callback = True
                        await self.conclude_question(ctx)
                #record attempt
                elif ctx.message.author not in self.current_successes.keys():
                        self.current_successes[ctx.message.author] = False

    async def conclude_question(self, ctx):

        if self.__running and self.current_question is not None:

            question_winners = []
            quiz_winners = []
            for player in self.current_successes.keys():
                score = int(self.current_successes[player] * self.current_question.score)
                if player in self.scores.keys():
                    self.scores[player] += score
                else:
                    self.scores[player] = score
                if self.current_successes[player]:
                    question_winners.append('<@!{}> '.format(player.id))
                    if self.scores[player] > self._win_limit:
                        quiz_winners.append('<@!{}> '.format(player.id))
            if len(question_winners) > 0:
                message = 'Bien joué {} ! '.format(' '.join(question_winners))
            else:
                message = "Eh bien.. vous n'avez pas trouvé ? "
            message += 'La bonne réponse était : {}'.format(self.current_question.get_answer())
            await ctx.send(message)
            self.current_question = None
            
            #check win
            if len(quiz_winners) > 0:
                await self.print_scores(ctx)
                await ctx.send('Le quiz est remporté par {} ! Félicitations.'.format(' '.join(quiz_winners)))
                self._questions.extend(self._asked)
                self._asked = []
                self.__running = False                    
            
            # #print totals?
            # elif len(self._asked) % 5 == 0:
            #     await self.print_scores(ctx)                    
        
            
        

                
    async def print_scores(self, ctx):
        #prints out a table of scores.
        if self.__running:
            await ctx.send('Voici les scores:')
        else:
            await ctx.send('Voici les scores:')
            
        highest = 0
        for player in self.scores.keys():
            await ctx.send('<@!{}>:\t{}'.format(player.id, self.scores[player]))
            if self.scores[player] > highest:
                highest = self.scores[player]
                
        if len(self.scores) == 0:
            await ctx.send('Pas de résultats à afficher.')
                
        leaders = []
        for player in self.scores.keys():
            if self.scores[player] == highest:
                leaders.append(player)
                
        if len(leaders) > 0:
            leader_string = 'En tête : '
            for leader in leaders:
                leader_string += f'<@!{leader.id}> '
            await ctx.send(leader_string)    

    async def edit_score(self, ctx, user, new_score):
        self.scores[user] = int(new_score)
        await ctx.send(
             '<@!{}> a maintenant {} points.'.format(user.id, self.scores[user]))
    
    
class Question:
    # A question in a quiz
    def __init__(self, question, answer, score, allow_multiple_attempts, allow_multiple_successes, category=None, author=None, regex=None):
        self.question = question
        self.answer = answer
        self.score = score
        self.allow_multiple_attempts = allow_multiple_attempts
        self.allow_multiple_successes = allow_multiple_successes
        self.author = author
        self.regex = regex
        self.category = category
        self._hints = 0
        
        
    def ask_question(self):
        # gets a pretty formatted version of the question.
        question_text = ''
        if self.category is not None:
            question_text+='({}) '.format(self.category)
        # else:
        #     question_text+='(Général) '
        if self.author is not None:
            question_text+='Posée par {}. '.format(self.author)
        question_text += self.question.replace(r'\n', '\n').replace(r'\t', '\t')
        return question_text
    
    
    def answer_correct(self, answer):
        #checks if an answer is correct or not.

        if answer.lower().startswith('!answer'):
            answer = answer[7:]
        elif answer.lower().startswith('!a'):
            answer = answer[2:]

        #should check regex
        if self.regex is not None:
            match = re.fullmatch(unidecode.unidecode(self.regex.lower()).strip(), unidecode.unidecode(answer.lower()).strip())
            print(re.sub('.* ','', answer), self.regex, match)
            return match is not None
            
        #else just string match
        return self.answer.lower().strip() in answer.lower().strip()
        # return  answer.lower().strip() == self.answer.lower().strip()
    
    
    def get_hint(self, hint_number):
        # gets a formatted hint for the question
        hint = []
        for i in range(len(self.answer)):
            if i % 5 < hint_number:
                hint = hint + list(self.answer[i])
            else:
                if self.answer[i] == ' ':
                    hint += ' '
                else:
                    hint += '-'
                    
        return ''.join(hint)
        
    
    def get_answer(self):
        # gets the expected answer
        return self.answer
    
    
    
    
    
    
    
    
