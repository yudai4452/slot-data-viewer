import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.colors import ListedColormap
import os

# --- フォント設定 ---
font_url = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf"
font_path = "/tmp/NotoSansCJKjp-Regular.otf"

if not os.path.exists(font_path):
    import urllib.request
    urllib.request.urlretrieve(font_url, font_path)

fm.fontManager.addfont(font_path)
plt.rcParams['font.family'] = 'Noto Sans CJK JP'

# --- Streamlitページ設定 ---
st.set_page_config(page_title="スロットデータビューワー", layout="wide")
st.title("スロットデータビューワー（Google Drive対応版）")

# --- Google Drive ファイルID ---
store_files = {
    "メッセ武蔵境": "1Anw7miFIJYE6_lveWUqx74xLS99Fkb-G",
    "プレゴ立川": "1wUJX8Uz-LP6VGzB9vsypBQFuf_bufsWJ"
}

# --- 店舗・ファイル読込 ---
store = st.selectbox("店舗を選択", list(store_files.keys()))
file_id = store_files[store]
url = f"https://drive.google.com/uc?id={file_id}"

try:
    df = pd.read_csv(url, encoding="utf-8")
    df["日付"] = pd.to_datetime(df["日付"])

    # --- 機種・台番号選択 ---
    model = st.selectbox("機種を選択", sorted(df["機種名"].unique()))
    filtered_df = df[df["機種名"] == model]
    machine = st.selectbox("台番号を選択", sorted(filtered_df["台番号"].unique()))
    target_df = filtered_df[filtered_df["台番号"] == machine].sort_values("日付")

    # --- 移動平均付き推移グラフ ---
    st.subheader("移動平均線を重ねた推移グラフ")
    exclude_cols = ["日付", "機種名", "台番号", "店舗名"]
    ma_col = st.selectbox("表示項目を選択", [col for col in df.columns if col not in exclude_cols], key="ma_col")

    ma_df = target_df.copy()
    ma_df["MA7"] = ma_df[ma_col].rolling(window=7).mean()
    ma_df["MA14"] = ma_df[ma_col].rolling(window=14).mean()

    fig1, ax1 = plt.subplots(figsize=(10, 4))
    ax1.plot(ma_df["日付"], ma_df[ma_col], label="実データ", marker="o", color="#4e79a7")
    ax1.plot(ma_df["日付"], ma_df["MA7"], label="7日移動平均", linestyle="--", color="#59a14f")
    ax1.plot(ma_df["日付"], ma_df["MA14"], label="14日移動平均", linestyle=":", color="#edc948")
    ax1.set_title(f"{store} - {model} 台{machine} の {ma_col} 推移（移動平均線付き）")
    ax1.set_xlabel("日付")
    ax1.set_ylabel(ma_col)
    ax1.grid(True)
    ax1.legend()
    st.pyplot(fig1)

    # --- 表示形式の切り替え ---
    st.subheader("台番号×日付の表示形式を選択（持玉/差玉）")
    visualization_type = st.selectbox(
        "表示形式を選択",
        ["ヒートマップ", "スパークライン"],
        index=0
    )

    heatmap_col = "最大持玉" if store == "メッセ武蔵境" else "最大差玉"

    if heatmap_col in filtered_df.columns:
        pivot_df = filtered_df.pivot(index="台番号", columns="日付", values=heatmap_col)

        if visualization_type == "ヒートマップ":
            fig2, ax2 = plt.subplots(figsize=(12, 6))
            custom_colors = [
                "#4e79a7", "#59a14f", "#edc948", "#b07aa1", "#76b7b2",
                "#ff9da7", "#9c755f", "#bab0ac", "#17becf", "#bcbd22"
            ]
            custom_cmap = ListedColormap(custom_colors)
            vmin = pivot_df.min().min()
            vmax = pivot_df.max().max()
            c = ax2.imshow(pivot_df, aspect="auto", cmap=custom_cmap, interpolation='none', vmin=vmin, vmax=vmax)
            ax2.set_title(f"{store} - {model} の {heatmap_col} 表示（ヒートマップ）")
            ax2.set_xlabel("日付")
            ax2.set_ylabel("台番号")
            ax2.set_xticks(range(len(pivot_df.columns)))
            ax2.set_xticklabels([d.strftime('%m/%d') for d in pivot_df.columns], rotation=90, fontsize=8)
            ax2.set_yticks(range(len(pivot_df.index)))
            ax2.set_yticklabels(pivot_df.index, fontsize=8)
            cb = fig2.colorbar(c, ax=ax2)
            cb.set_label("持玉/差玉の値")
            st.pyplot(fig2)

        elif visualization_type == "スパークライン":
            import math
            machine_ids = sorted(filtered_df["台番号"].unique())
            n_cols = 4
            n_rows = math.ceil(len(machine_ids) / n_cols)
            fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 3, n_rows * 2), sharex=True)
            axes = axes.flatten()

            for i, machine_id in enumerate(machine_ids):
                data = filtered_df[filtered_df["台番号"] == machine_id].sort_values("日付")
                axes[i].plot(data["日付"], data[heatmap_col], color="#4e79a7", linewidth=1, label="実データ")

                # --- 移動平均線の追加 ---
                ma7 = data[heatmap_col].rolling(window=7).mean()
                ma14 = data[heatmap_col].rolling(window=14).mean()
                axes[i].plot(data["日付"], ma7, color="#59a14f", linestyle="--", linewidth=1, label="MA7")
                axes[i].plot(data["日付"], ma14, color="#edc948", linestyle=":", linewidth=1, label="MA14")

                axes[i].set_title(f"台{machine_id}", fontsize=8)
                axes[i].tick_params(axis='x', labelsize=6, rotation=45)
                axes[i].tick_params(axis='y', labelsize=6)

            for j in range(i+1, len(axes)):
                fig.delaxes(axes[j])

            fig.tight_layout()
            st.pyplot(fig)


    else:
        st.warning(f"この店舗では '{heatmap_col}' の列が見つかりませんでした。")

except Exception as e:
    st.error(f"CSVの読み込みまたは解析でエラーが発生しました: {e}")
