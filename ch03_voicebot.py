##### 기본 정보 입력 #####
import streamlit as st
from audiorecorder import audiorecorder
import openai # 패키지는 그대로 유지
from openai import OpenAI # 클라이언트 객체 사용을 위해 추가
import os
from datetime import datetime
from gtts import gTTS
import base64

##### 기능 구현 함수 #####
# client 객체를 인자로 받도록 수정
def STT(audio, client):
    filename='input.mp3'
    audio.export(filename, format="mp3")
    audio_file = open(filename, "rb")
    
    # 최신 문법으로 변경: client.audio.transcriptions.create[cite: 3]
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    audio_file.close()
    os.remove(filename)
    return transcript.text # 딕셔너리가 아닌 속성값(.text)으로 접근[cite: 3]

# client 객체를 인자로 받도록 수정[cite: 3]
def ask_gpt(prompt, model, client):
    # 최신 문법으로 변경: client.chat.completions.create[cite: 3]
    response = client.chat.completions.create(model=model, messages=prompt)
    return response.choices[0].message.content # .content 속성으로 접근[cite: 3]

def TTS(response):
    filename = "output.mp3"
    tts = gTTS(text=response, lang="ko")
    tts.save(filename)

    with open(filename, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    os.remove(filename)

##### 메인 함수 #####
def main():
    st.set_page_config(page_title="음성 비서 프로그램", layout="wide")

    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]

    if "check_reset" not in st.session_state:
        st.session_state["check_reset"] = False

    st.header("학현이의 음성 비서 프로그램")
    st.markdown("---")

    with st.expander("음성비서 프로그램에 관하여", expanded=True):
        st.write("- OpenAI v1.0+ 최신 문법이 적용된 버전입니다.")

    with st.sidebar:
        # API 키 입력
        api_key = st.text_input(label="OPENAI API 키", placeholder="Enter Your API Key", type="password")
        st.markdown("---")
        model = st.radio(label="GPT 모델", options=["gpt-4", "gpt-3.5-turbo"])
        st.markdown("---")
        if st.button(label="초기화"):
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korea"}]
            st.session_state["check_reset"] = True
            
    # API 키가 입력되었을 때만 클라이언트 생성 및 기능 작동
    if api_key:
        client = OpenAI(api_key=api_key) # OpenAI 클라이언트 초기화[cite: 3]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("질문하기")
            audio = audiorecorder("클릭하여 녹음하기", "녹음중...")
            if (audio.duration_seconds > 0) and (st.session_state["check_reset"] == False):
                st.audio(audio.export().read())
                # STT 함수에 client 전달
                question = STT(audio, client)

                now = datetime.now().strftime("%H:%M")
                st.session_state["chat"].append(("user", now, question))
                st.session_state["messages"].append({"role": "user", "content": question})

        with col2:
            st.subheader("질문/답변")
            if (audio.duration_seconds > 0) and (st.session_state["check_reset"] == False):
                # ask_gpt 함수에 client 전달
                response = ask_gpt(st.session_state["messages"], model, client)

                st.session_state["messages"].append({"role": "assistant", "content": response})
                now = datetime.now().strftime("%H:%M")
                st.session_state["chat"].append(("bot", now, response))

                for sender, time, message in st.session_state["chat"]:
                    if sender == "user":
                        st.write(f'<div style="display:flex;align-items:center;"><div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                    else:
                        st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>', unsafe_allow_html=True)
                
                TTS(response)
            else:
                st.session_state["check_reset"] = False
    else:
        st.warning("사이드바에서 OpenAI API Key를 입력해 주세요.")

if __name__=="__main__":
    main()
