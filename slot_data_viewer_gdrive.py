import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.colors import ListedColormap
import os

st.set_page_config(page_title="スロットデータビューワー", layout="wide")
st.title("スロットデータビューワー（Google Drive対応版）")

# --- 日本語フォント設定（Google FontsのNoto Sans CJK JP） ---
font_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf"
font_path = "/tmp/NotoSansCJKjp-Regular.otf"

if not os.path.exists(font_path):
    import urllib.request
    urllib.request.urlretrieve(font_url, font_path)

fm.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'Noto Sans CJK JP'

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
    exclude_cols = ["日付", "機種名", "台番号", "店舗名"]
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

    # 全く異なる10色のカスタムカラーマップを定義
    custom_colors = [
        "#e41a1c",  # 赤
        "#377eb8",  # 青
        "#4daf4a",  # 緑
        "#984ea3",  # 紫
        "#ff7f00",  # オレンジ
        "#ffff33",  # 黄
        "#a65628",  # 茶
        "#f781bf",  # ピンク
        "#999999",  # グレー
        "#66c2a5"   # ティール
    ]
    
    custom_cmap = ListedColormap(custom_colors)

    # --- 機種ごとのヒートマップ（全く違う色で表示） ---
    st.subheader("台番号×日付のカスタムカラーマップ表示（持玉/差玉）")
    heatmap_col = "最大持玉" if store == "メッセ武蔵境" else "最大差玉"

    if heatmap_col in filtered_df.columns:
        pivot_df = filtered_df.pivot(index="台番号", columns="日付", values=heatmap_col)
        st.write(f"表示項目: {heatmap_col}")

        fig2, ax2 = plt.subplots(figsize=(12, 6))
        vmin = pivot_df.min().min()
        vmax = pivot_df.max().max()
        # カスタムカラーマップを使用
        c = ax2.imshow(pivot_df, aspect="auto", cmap=custom_cmap, interpolation='none', vmin=vmin, vmax=vmax)
        
        ax2.set_title(f"{model} の {heatmap_col} 表示（{store}）")
        ax2.set_xlabel("日付")
        ax2.set_ylabel("台番号")
        ax2.set_xticks(range(len(pivot_df.columns)))
        ax2.set_xticklabels([d.strftime('%m/%d') for d in pivot_df.columns], rotation=90, fontsize=8)
        ax2.set_yticks(range(len(pivot_df.index)))
        ax2.set_yticklabels(pivot_df.index, fontsize=8)
        
        cb = fig2.colorbar(c, ax=ax2)
        cb.set_label("持玉/差玉の値")
        
        st.pyplot(fig2)
    else:
        st.warning(f"この店舗では '{heatmap_col}' の列が見つかりませんでした。")
        
except Exception as e:
    st.error(f"CSVの読み込みまたは解析でエラーが発生しました: {e}")
