import streamlit as st
from transformers import pipeline
import torch

#MZ to handel caching ...
@st.cache_resource
def loadGpt2Model(device, model, tokenizer):
    return pipeline('text-generation', model=model,tokenizer=tokenizer, device=device)
# pipeline('text-generation', model='./gpt2-spider-sql', tokenizer='./gpt2-spider-sql', device=0)


# ---- GPT2 generation settings  ----
maxLength = 250
temperature = 0.1 #less better 
topK = 30   #less is better  
topP = 0.8 #less is better
repetitionPenalty = 1.5 #higher is better
numReturnSequences = 1
fineTunedModels = './trainedGPT2/gpt2-spider-sql-{}'

class IntelligentReportingAgentApp:
    def __init__(self):
        self.modelName = None
        self.accHW = None
        self.generator = None
        self.question = ''
    
    def run(self):
        self._renderHeader()
        self._sidebar()
        self._handleModelSelection()
        self._mainContent()

    def _renderHeader(self):
        st.title('👋 Intelligent Reporting Agent ')

    def _sidebar(self):
        st.sidebar.title('Choose Model')
        self.modelName = st.sidebar.selectbox(
            'Select a model:',
            ('GPT2', 'GPT2-Tunned 1K', 'GPT2-Tunned 3K', 'GPT2-Tunned 6K', 'GPT2-Tunned 7K','GPT2-Tunned 10K','GPT2-Tunned 281K'))

        self.accHW = st.sidebar.selectbox(
        'Select compute device:',
        ('GPU', 'CPU'))
        
    def _handleModelSelection(self):
        device = 0 if self.accHW == 'GPU' and torch.cuda.is_available() else -1
        if self.modelName == 'GPT2':
            self.generator = loadGpt2Model(device,'gpt2','gpt2')
        elif self.modelName == 'GPT2-Tunned 1K':
            self.model = fineTunedModels.format(1000)
            self.tok = fineTunedModels.format(1000)
            self.generator = loadGpt2Model(device,self.model,self.tok)
        elif self.modelName == 'GPT2-Tunned 3K':
            self.model = fineTunedModels.format(3000)
            self.tok = fineTunedModels.format(3000)
            self.generator = loadGpt2Model(device,self.model,self.tok)
        elif self.modelName == 'GPT2-Tunned 6K':
            self.model = fineTunedModels.format(6000)
            self.tok = fineTunedModels.format(6000)
            self.generator = loadGpt2Model(device,self.model,self.tok)
        elif self.modelName == 'GPT2-Tunned 7K':
            self.model = fineTunedModels.format(7000)
            self.tok = fineTunedModels.format(7000)
            self.generator = loadGpt2Model(device,self.model,self.tok)
        elif self.modelName == 'GPT2-Tunned 10K':
            self.model = fineTunedModels.format(10000)
            self.tok = fineTunedModels.format(10000)
            self.generator = loadGpt2Model(device,self.model,self.tok) 
        elif self.modelName == 'GPT2-Tunned 281K':
            self.model = fineTunedModels.format(281124)
            self.tok = fineTunedModels.format(281124)
            self.generator = loadGpt2Model(device,self.model,self.tok) 
        else:
            st.warning('Not available !!')

    def _mainContent(self):
        self.question = st.text_input('Ask your question to GPT-2:')

        if st.button('Generate report | GPT-2'):
            if self.generator and self.question:
                fullPrompt = self.question
                output = self.generator(fullPrompt, max_length=maxLength, temperature=temperature,
                                        top_k=topK, top_p=topP, repetition_penalty=repetitionPenalty,
                                        num_return_sequences=numReturnSequences)
                generatedText = output[0]['generated_text']
                st.write('GPT-2 says:')
                st.write(generatedText)
            else:
                st.write('Please enter a question or check if the model is loaded.')

# Run the app
if __name__ == '__main__':
    app = IntelligentReportingAgentApp()
    app.run()
