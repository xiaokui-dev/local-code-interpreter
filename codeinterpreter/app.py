import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
import streamlit as st
import pandas as pd

from codeinterpreter.code_interpreter import CodeInterpreter, File
from codeinterpreter.db_manager import DBManager

ci = CodeInterpreter()
db = DBManager()

file_path = os.path.join(os.environ.get('HOME'), "Desktop/codeinterpreter/jupyter_files")


def main():
    st.title("Code Interpreter")
    st.session_state.current_chat = None

    st.session_state.chat_title_list = db.get_chats()

    with st.sidebar:
        chat_title = st.text_input("标题", placeholder="请输入标题")
        new_chat_button = st.button("New Chat")
        if new_chat_button and chat_title == '':
            st.warning('请输入标题')
            new_chat_button = False
        if new_chat_button:
            chat_id = db.save_chat(chat_title)
            st.session_state.current_chat = db.get_chat(chat_id)
            st.session_state.chat_title_list = db.get_chats()
        st.session_state.current_chat = st.radio("历史记录", st.session_state.chat_title_list,
                                                 format_func=lambda x: x[1])
        if len(st.session_state.chat_title_list) != 0:
            st.warning("点击上方的 'New Chat' 开启新聊天")
    if st.session_state.current_chat is None:
        st.warning("点击左侧的 'New Chat' 开启新聊天")
    else:
        st.session_state.current_chat_messages = []

        chat_container = st.container()
        form_container = st.container()
        chat_id = st.session_state.current_chat[0]
        st.session_state.chat_messages = db.get_message_by_chat_id(chat_id)

        with chat_container:
            for chat_message in st.session_state.chat_messages:
                category = chat_message[1]
                content = chat_message[2]
                file_urls = chat_message[3]
                if category == 'user':
                    with st.chat_message("user"):
                        st.write(content)
                else:
                    with st.chat_message("assistant"):
                        st.write(content)
                        if file_urls is not None and file_urls != "":
                            for url in file_urls.split("####"):
                                file_show(url)
        with form_container:
            upload_file = st.file_uploader(label="上传文件:", accept_multiple_files=False)
            with st.form(key="my_form", clear_on_submit=True):
                text_input_value = st.text_area(label="输入文本:", placeholder="输入文本")
                submitted = st.form_submit_button('执行', use_container_width=True)
                if submitted and text_input_value == '':
                    st.warning('请输入文本')
                    submitted = False
                if submitted:
                    with chat_container:
                        st.chat_message("user").write(text_input_value)
                        with st.spinner():
                            file_url_list = []
                            if upload_file is None:
                                response = ci.generate_response(text_input_value, None)
                            else:
                                file = File(name=upload_file.name, content=upload_file.read())
                                response = ci.generate_response(text_input_value, file)
                                file_url = "{file_path}/{file_name}".format(file_path=file_path,
                                                                            file_name=upload_file.name)
                                file_url_list.append(file_url)
                            if response.content != '':
                                save_user_result = db.save_chat_messages(chat_id, "user", text_input_value,
                                                                         file_url_list)
                                st.session_state.chat_messages.append(db.get_message_by_id(save_user_result))
                                save_ai_result = db.save_chat_messages(chat_id, "assistant", response.content, [])
                                st.session_state.chat_messages.append(db.get_message_by_id(save_ai_result))
                                with chat_container:
                                    st.chat_message("assistant").write(response.content)
                                    file_url_list = []
                                    for _file in response.files:
                                        file_url = "{file_path}/{file_name}".format(file_path=file_path,
                                                                                    file_name=_file.name)
                                        file_url_list.append(file_url)
                                        file_show(file_url)
                                    if len(file_url_list) != 0:
                                        db.update_file_url(file_url_list, save_ai_result)


def file_show(url):
    try:
        file_extension = url.split(".")[-1]
        if file_extension == 'csv':
            data = pd.read_csv(url)
            top_10_rows = data.head(10)
            st.dataframe(top_10_rows)
        elif file_extension in ['xls', 'xlsx']:
            data = pd.read_excel(url)
            top_10_rows = data.head(10)
            st.dataframe(top_10_rows)
        elif file_extension == 'mp4':
            st.video(url)
        elif file_extension == 'jpeg' or file_extension == 'gif' or file_extension == 'png':
            st.image(url, use_column_width=True)
        elif file_extension == 'md':
            with open(url, "r") as file:
                file_content = file.read()
            st.markdown(file_content)
        elif file_extension == 'text' or file_extension == 'txt':
            with open(url, "r") as file:
                file_content = file.read()
            st.code(file_content, language="markdown")
        else:
            st.error(file_extension + "格式的文件类型不支持展示")
    except Exception as error:
        st.error(error)
        pass


if __name__ == "__main__":
    main()
