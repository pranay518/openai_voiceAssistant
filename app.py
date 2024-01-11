import os
import azure.cognitiveservices.speech as speechsdk
import openai
from dotenv import load_dotenv

import streamlit as st
from streamlit_lottie import st_lottie
import json
import openai

# Load environment variables from .env file
load_dotenv()

# openai.api_type = "azure"
# openai.api_base = os.getenv("OPENAI_API_ENDPOINT")
# openai.api_version = os.getenv("OPENAI_API_VERSION")
# openai.api_key = os.getenv("OPENAI_API_KEY")
# deployment_name=os.getenv("OPENAI_GPT_DEPLOYMENT_NAME"),
# temperature=0,
# openai_api_version="2023-08-01-preview",
# openai_api_type="azure",
# openai_api_base=os.getenv("OPENAI_API_BASE"),
# openai_api_key=os.getenv('OPENAI_API_KEY')
client = openai.AzureOpenAI(
    azure_deployment=os.getenv("OPENAI_GPT_DEPLOYMENT_NAME"),
    api_version="2023-08-01-preview",
    azure_endpoint=os.getenv("OPENAI_API_BASE"),
    api_key=os.getenv('OPENAI_API_KEY')
    #request_timeout=REQUEST_TIMEOUT,
    #max_tokens=4090
         )

# This example requires environment variables named "SPEECH_KEY" and "SPEECH_REGION"
speech_config = speechsdk.SpeechConfig(subscription=os.getenv('SPEECH_KEY'),region=os.getenv("SPEECH_REGION"))
audio_output_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# Should be the locale for the speaker's language.
speech_config.speech_recognition_language="en-US"
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# The language of the voice that responds on behalf of Azure OpenAI.
speech_config.speech_synthesis_voice_name='en-US-JennyMultilingualNeural'
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_output_config)

# tts sentence end mark
tts_sentence_end = [ ".", "!", "?", ";", "。", "！", "？", "；", "\n",]

def ask_and_reply(prompt, message_box):
    message_text = [
        {"role":"system","content":"You are an AI assistant that helps people find information. You need to be able to understand and answer questions about the world. Try to answer in one or two sentences. Be concise."},
        {"role":"user","content":prompt},
    ]

    #completion = client.chat.completions.create(
    #completion = openai.chat.completions.create(
    completion = client.chat.completions.create(
        model=os.getenv("OPENAI_GPT_DEPLOYMENT_NAME"),
        messages = message_text,
        temperature=0.7,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stream=True
    )

    print("OpenAI Request sent. Now waiting for response...")


    collected_messages = []
    for chunk in completion:
        # print(chunk)
        if len(chunk.choices) > 0:
            #print("reach1")
            #if "content" in chunk.choices[0].delta:
            if chunk.choices[0].delta.content is not None:
                print("Chunk:", chunk.choices[0].delta.content)#["content"])
                chunk_message = chunk.choices[0].delta.content  # extract the chunk message from openai output
                collected_messages.append(chunk_message)  # aggregate the message
                

                if chunk_message[0] in tts_sentence_end: # sentence end found
                    text = ''.join(collected_messages).strip() # join the recieved message together to build a sentence
                    if text != '': # if sentence only have \n or space, we could skip
                        #streaming audio output
                        print("Now playing: {}".format(text))
                        message_box.write(f'ChatGPT: {text}')
                        result = speech_synthesizer.speak_text_async(text).get()
                        collected_messages.clear()

def record_voice():
    # Get audio from the microphone and then send it to the TTS service.
    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized speech: {}".format(speech_recognition_result.text))
        st.session_state.prompt_text = speech_recognition_result.text
        st.session_state.voice_recognized = True

    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))

    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))


# Function to load JSON from file
def load_json_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        data = json.load(file)
    return data

# Load the Lottie animation from JSON file
lottie_anim = load_json_from_file('./lottie.json')

#path = r"C:\Users\INPUNPRAP\OneDrive - Sandvik\Desktop\classify_SMG\chatgpt-azure-speech-master\chatgpt-azure-speech-master\app.py", encoding="utf-8"


# Initialize session state
if "prompt_text" not in st.session_state:
    st.session_state.prompt_text = None
if "voice_recognized" not in st.session_state:
    st.session_state.voice_recognized = False

lottie_anim = load_json_from_file('./lottie.json')

st.set_page_config(page_title="ChatGPT Voice", page_icon='', layout='centered')

with st.container():
    left, right = st.columns([2, 3])
    with left:
        st_lottie(lottie_anim, speed=0.5, height=300, key="coding")
    with right:
        st.subheader('ChatGPT Voice Assistant')
        st.write('Press Record to start recording your voice.')

        rec_button = st.button(
            label="Record", type='primary',
            on_click=record_voice)

        message_box = st.empty()
        if st.session_state.voice_recognized:
            message_box.write(f'You: {st.session_state.prompt_text}')

            # Send the prompt to OpenAI
            ask_and_reply(st.session_state.prompt_text, message_box)



    



