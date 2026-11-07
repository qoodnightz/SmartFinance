"""Interactive Gemini coach; network requests never run on Tk's UI thread."""
import queue
import threading
import tkinter as tk
from tkinter import scrolledtext
from neuroverse.services.gemini_agent import ask_gemini, build_context, model_ready, offline_reply, GeminiUnavailable
from neuroverse.ui import theme as T
from neuroverse.ui.widgets import Screen, panel, label, button

PROMPTS=['Why might my balance drop?', 'Help me prepare for an unexpected expense', 'Explain this in simpler words', 'What is one small step I can take?']

class Coach(Screen):
    def __init__(self,parent,store,bus,navigate):
        super().__init__(parent,store,bus,navigate,'Talk to your future-self guide ✦',
                         'Ask about your fictional financial futures. You choose what to do next.')
        main=panel(self,'✦  Your personalised AI financial coach')
        main.pack(fill='both',expand=True)
        self.status=label(main,'',10,True,color=T.MUTED)
        self.status.pack(anchor='w',pady=(0,8))
        self.history=scrolledtext.ScrolledText(main,height=14,wrap='word',font=(T.FONT,11),bg='#f8f7ff',fg=T.TEXT,
                                               relief='flat',padx=16,pady=14,state='disabled')
        self.history.pack(fill='both',expand=True)
        self.history.tag_configure('user',foreground=T.PRIMARY,spacing1=12,font=(T.FONT,11,'bold'))
        self.history.tag_configure('assistant',foreground=T.TEXT,spacing1=12)
        suggestions=tk.Frame(main,bg=T.SURFACE)
        suggestions.pack(fill='x',pady=(12,8))
        for i,p in enumerate(PROMPTS):
            b=tk.Button(suggestions,text=p,command=lambda x=p:self.ask(x),bg=T.PRIMARY_LIGHT,fg=T.PRIMARY,
                        bd=0,padx=9,pady=8,font=(T.FONT,9),cursor='hand2',wraplength=160)
            b.grid(row=i//2,column=i%2,sticky='ew',padx=4,pady=3)
        for i in range(2): suggestions.columnconfigure(i,weight=1)
        bottom=tk.Frame(main,bg=T.SURFACE)
        bottom.pack(fill='x',pady=(8,0))
        self.question=tk.StringVar()
        entry=tk.Entry(bottom,textvariable=self.question,font=(T.FONT,12),relief='solid',bd=1)
        entry.pack(side='left',fill='x',expand=True,ipady=8,padx=(0,10))
        entry.bind('<Return>',lambda _:self.submit())
        self.send=button(bottom,'Ask Gemini  →',self.submit)
        self.send.pack(side='right')
        self.results=queue.Queue()
        self.pending=False
        self.after(100,self.poll)
        self._append('assistant','Welcome! I can explain your simulated finances and help explore options. No real bank account is connected.')
        self.refresh()

    def refresh(self):
        self.status.config(text=('● GEMINI READY · Online requests' if model_ready() else '○ OFFLINE MODE · Add GEMINI_API_KEY to enable AI'),
                           fg=T.GOOD if model_ready() else T.MUTED)

    def _append(self,tag,text):
        self.history.config(state='normal')
        self.history.insert('end', ('YOU  ·  ' if tag=='user' else 'NEUROVERSE  ·  ')+text+'\n\n',tag)
        self.history.see('end')
        self.history.config(state='disabled')

    def submit(self):
        self.ask(self.question.get())
        self.question.set('')

    def ask(self,question):
        question=question.strip()
        if self.pending or not question: return
        self._append('user',question)
        if not model_ready():
            self._append('assistant',offline_reply(question,self.store))
            return
        context=build_context(self.store)  # capture snapshot on Tk main thread
        self.pending=True
        self.send.config(state='disabled',text='Thinking…')
        def work():
            try: self.results.put(('ok',ask_gemini(question,context)))
            except GeminiUnavailable as exc: self.results.put(('error',str(exc)))
            except Exception: self.results.put(('error','Unexpected AI service error. Please try again.'))
        threading.Thread(target=work,daemon=True).start()

    def poll(self):
        try:
            while True:
                status,result=self.results.get_nowait()
                self.pending=False
                self.send.config(state='normal',text='Ask Gemini  →')
                if status=='ok': self._append('assistant',result+'\n\nThese are scenario-based educational ideas, not guaranteed outcomes.')
                else: self._append('assistant',result+'\n\n'+offline_reply('',self.store))
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100,self.poll)
