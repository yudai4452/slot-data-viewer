import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="スロットデータビューワー", layout="wide")
st.title("スロットデータビューワー（Google Drive対応版）")

# 店舗ごとのGoogle DriveファイルID
store_files = {
    "メッセ武蔵境": "1Anw7miFIJYE6_lveWUqx74xLS99Fkb-G",
    "プレゴ立川": "1wUJX8Uz-LP6VGzB9vsypBQFuf_bufsWJ"
}

# 店舗選択
store = st.selectbox("店舗を選択", list(store_files.keys()))
file_id = store_files[store]
url = f"https://drive.google.com/uc?id={file_id}"

try:
    df = pd.read_csv(url, encoding="utf-8")
    df["日付"] = pd.to_datetime(df["日付"])

    # 機種名選択
    model = st.selectbox("機種を選択", sorted(df["機種名"].unique()))

    # 該当機種の台番号一覧
    filtered_df = df[df["機種名"] == model]
    machine = st.selectbox("台番号を選択", sorted(filtered_df["台番号"].unique()))

    # 表示する項目を選択
    exclude_cols = ["日付", "機種名", "台番号"]
    value_col = st.selectbox("表示項目を選択", [col for col in df.columns if col not in exclude_cols])

    # 該当データでグラフ描画
    target_df = filtered_df[filtered_df["台番号"] == machine].sort_values("日付")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(target_df["日付"], target_df[value_col], marker="o")
    ax.set_title(f"{store} - {model} 台{machine} の {value_col} 推移")
    ax.set_xlabel("日付")
    ax.set_ylabel(value_col)
    ax.grid(True)
    st.pyplot(fig)

except Exception as e:
    st.error(f"CSVの読み込みまたは解析でエラーが発生しました: {e}")
