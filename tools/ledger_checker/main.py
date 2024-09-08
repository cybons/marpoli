import streamlit as st
from spreadsheet_data import get_all_sheets_data, load_sheets_config
from xml_data import parse_xml

# Initialize session state for managing the progress of each step
if "step_1_done" not in st.session_state:
    st.session_state["step_1_done"] = False
if "step_2_done" not in st.session_state:
    st.session_state["step_2_done"] = False
if "step_3_done" not in st.session_state:
    st.session_state["step_3_done"] = False
if "step_4_done" not in st.session_state:
    st.session_state["step_4_done"] = False


# Function to reset steps
def reset_steps():
    st.session_state["step_1_done"] = False
    st.session_state["step_2_done"] = False
    st.session_state["step_3_done"] = False
    st.session_state["step_4_done"] = False


# Step 1: ファイルを読み込み
def step_1():
    reset_steps()
    # ファイル読み込み処理（仮）
    st.write("ファイルを読み込みました。")
    st.session_state["step_1_done"] = True
    # ファイルを読み込み直したら、すべてのステップをリセット


# Step 2: パースする
def step_2():
    reset_steps()
    # パース処理（仮）
    st.write("データをパースしました。")
    st.session_state["step_2_done"] = True


# Step 3: スプシのデータを読み込む
def step_3():
    reset_steps()
    # スプシからデータを読み込む処理（仮）
    st.write("スプシのデータを読み込みました。")
    st.session_state["step_3_done"] = True


# Step 4: マッチングする
def step_4():
    reset_steps()
    # マッチング処理（仮）
    st.write("データをマッチングしました。")
    st.session_state["step_4_done"] = True


# Step 5: スプシにデータを書き戻す
def step_5():
    reset_steps()
    # スプシにデータを書き戻す処理（仮）
    st.write("スプシにデータを書き戻しました。")
    # 最後のステップが完了したらリセットするかどうかを選べます。
    # st.session_state.clear() # 必要に応じてコメントを解除


def main():
    st.title("ファイル選択と条件確認")

    # ファイルのアップロード
    uploaded_files = st.file_uploader(
        "XMLファイルを選択してください", type="xml", accept_multiple_files=True
    )

    st.write(f"{str(len(uploaded_files) )}件選択されました")

    if not uploaded_files:
        st.warning("少なくとも1つのファイルを選択してください。")

    if st.button("ファイルを読み込み"):
        # state, conditions = check_file_conditions(uploaded_files)
        # if not selected_files:
        #     st.warning("少なくとも1つのファイルを選択してください。")
        # elif check_file_conditions(selected_files):
        #     st.success("全ての条件が満たされました。次の処理に進みます。")
        #     step_1()
        # else:
        #     st.error("条件に一致するファイルが不足しています。")
        step_1()
        with st.expander("読み込みデータ", expanded=True):
            ":star:" * 5
            st.subheader("それぞれの件数です")
            st.write({"kye": 1, "ddd": 3})

    if st.button("パースする", disabled=not st.session_state["step_1_done"]):
        xml_files = {file.name: parse_xml() for file in uploaded_files}
        with st.expander("パース結果", expanded=True):
            ":star:" * 5
            st.subheader("それぞれの件数です")
            st.write(xml_files)
        step_2()

    if st.button(
        "スプシのデータを読み込む", disabled=not st.session_state["step_2_done"]
    ):
        handle_button_click()
        step_3()

    if st.button("マッチングする", disabled=not st.session_state["step_3_done"]):
        step_4()

    if st.button(
        "スプシにデータを書き戻す", disabled=not st.session_state["step_4_done"]
    ):
        step_5()


def handle_button_click():
    load_sheets_config()
    # JSONファイルから設定を読み込む
    sheets_config = load_sheets_config("sheets_config.json")
    sheets_df = get_all_sheets_data(sheets_config)
    print(sheets_df)


if __name__ == "__main__":
    main()
