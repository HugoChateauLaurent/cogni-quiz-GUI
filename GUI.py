from tkinter import *


class Quiz:

	def __init__(self):

		self.window = Tk()
		self.window.title("Cogni'Quiz")
		self.window.attributes("-fullscreen", True)
		self.window['bg'] = 'white'

		self.label = Label(self.window, text="Ceci est une question ?", font=("Arial Bold", 50))
		self.label.place(relx=.5, rely=.2, anchor="center")
		self.label['bg'] = 'white'

		self.btn = Button(self.window, text="Click Me", command=self.change_txt)
		self.btn['bg'] = 'blue'
		self.btn['fg'] = 'white'

		self.btn.grid(column=1, row=0)


		self.window.mainloop()

	def change_txt(self):
		self.label['text'] = 'Nouvelle question ?'

quiz = Quiz()



