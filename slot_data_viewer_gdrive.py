import streamlit as st
st.set_page_config(page_title="スロットデータビューワー", layout="wide")

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.colors import ListedColormap
import os
import math
import urllib.request
import logging

# ---------- ログ設定 ----------
logging.basicConfig(level=logging.INFO)

# ---------- 定数設定 ----------
FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf"
FONT_PATH = "/tmp/NotoSansCJKjp-Regular.otf"
CUSTOM_COLORS = [
    "#4e79a7", "#59a14f", "#edc948", "#b07aa1", "#76b7b2",
    "#ff9da7", "#9c755f", "#bab0ac", "#17becf", "#bcbd22"
]

# ---------- カラム名の定数 ----------
DATE_COL = "日付"
MODEL_COL = "機種名"
MACHINE_COL = "台番号"
STORE_COL = "店舗名"

# ---------- フォントの読み込み（キャッシュ付き） ----------
@st.cache_resource
def load_font(font_url: str, font_path: str) -> None:
    """
    指定URLから日本語フォントをダウンロードし、Matplotlibに登録します。
    """
    try:
        if not os.path.exists(font_path):
            logging.info("フォントをダウンロード中...")
            urllib.request.urlretrieve(font_url, font_path)
        fm.fontManager.addfont(font_path)
        plt.rcParams['font.family'] = 'Noto Sans CJK JP'
        logging.info("フォントの読み込みに成功しました。")
    except Exception as e:
        logging.exception("フォントの読み込みに失敗しました。")
        raise e

# ---------- CSVデータの読み込み（キャッシュ付き） ----------
@st.cache_data
def load_data(url: str) -> pd.DataFrame:
    """
    指定URLからCSVデータを読み込み、日付列をdatetime型に変換して返します。
    
    Parameters:
        url (str): CSVデータのURL
    Returns:
        pd.DataFrame: 読み込んだデータフレーム
    """
    try:
        logging.info("CSVデータを読み込み中...")
        df = pd.read_csv(url, encoding="utf-8")
        df[DATE_COL] = pd.to_datetime(df[DATE_COL])
        logging.info("CSVデータの読み込みに成功しました。")
        return df
    except Exception as e:
        logging.exception("CSVデータの読み込みでエラーが発生しました。")
        raise e

# ---------- ヒートマップ作成関数 ----------
def plot_heatmap(pivot_df: pd.DataFrame, store: str, model: str, heatmap_col: str) -> plt.Figure:
    """
    ピボットテーブルからヒートマップを生成します。
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    custom_cmap = ListedColormap(CUSTOM_COLORS)
    vmin = pivot_df.min().min()
    vmax = pivot_df.max().max()
    im = ax.imshow(pivot_df, aspect="auto", cmap=custom_cmap, interpolation='none', vmin=vmin, vmax=vmax)
    ax.set_title(f"{store} - {model} の {heatmap_col} 表示（ヒートマップ）")
    ax.set_xlabel("日付")
    ax.set_ylabel("台番号")
    ax.set_xticks(range(len(pivot_df.columns)))
    ax.set_xticklabels([d.strftime('%m/%d') for d in pivot_df.columns], rotation=90, fontsize=8)
    ax.set_yticks(range(len(pivot_df.index)))
    ax.set_yticklabels(pivot_df.index, fontsize=8)
    cb = fig.colorbar(im, ax=ax)
    cb.set_label("持玉/差玉の値")
    return fig

# ---------- スパークライン作成関数 ----------
def plot_sparklines(filtered_df: pd.DataFrame, heatmap_col: str) -> plt.Figure:
    """
    各台のスパークライン（小型折れ線グラフ）を生成します。
    """
    machine_ids = sorted(filtered_df[MACHINE_COL].unique())
    n_cols = 4
    n_rows = math.ceil(len(machine_ids) / n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(n_cols * 3, n_rows * 2), sharex=True)
    axes = axes.flatten()

    for i, machine_id in enumerate(machine_ids):
        data = filtered_df[filtered_df[MACHINE_COL] == machine_id].sort_values(DATE_COL)
        axes[i].plot(data[DATE_COL], data[heatmap_col], color=CUSTOM_COLORS[0], linewidth=1)
        axes[i].set_title(f"台{machine_id}", fontsize=8)
        axes[i].tick_params(axis='x', labelsize=6, rotation=45)
        axes[i].tick_params(axis='y', labelsize=6)

    # 不要な軸は削除
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
    fig.tight_layout()
    return fig

# ---------- 移動平均グラフ作成関数 ----------
def plot_moving_average(target_df: pd.DataFrame, col_ma: str, store: str, model: str, machine: str) -> plt.Figure:
    """
    特定の台のデータに対して、7日・14日の移動平均線を重ねた推移グラフを生成します。
    """
    ma_df = target_df.copy().sort_values(DATE_COL)
    ma_df["MA7"] = ma_df[col_ma].rolling(window=7, min_periods=1).mean()
    ma_df["MA14"] = ma_df[col_ma].rolling(window=14, min_periods=1).mean()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(ma_df[DATE_COL], ma_df[col_ma], label="実データ", marker="o", color=CUSTOM_COLORS[0])
    ax.plot(ma_df[DATE_COL], ma_df["MA7"], label="7日移動平均", linestyle="--", color=CUSTOM_COLORS[1])
    ax.plot(ma_df[DATE_COL], ma_df["MA14"], label="14日移動平均", linestyle=":", color=CUSTOM_COLORS[2])
    ax.set_title(f"{store} - {model} 台{machine} の {col_ma} 推移（移動平均線付き）")
    ax.set_xlabel("日付")
    ax.set_ylabel(col_ma)
    ax.grid(True)
    ax.legend()
    return fig

def setup_page():
    """Streamlitのページ設定を行います。"""
    st.title("スロットデータビューワー（Google Drive対応版）")

def main():
    # フォント読み込み（キャッシュ済み）
    load_font(FONT_URL, FONT_PATH)

    # Streamlitページ設定
    setup_page()

    # サイドバーに設定項目を集約
    st.sidebar.header("設定")
    store_files = {
        "メッセ武蔵境": "1Anw7miFIJYE6_lveWUqx74xLS99Fkb-G",
        "プレゴ立川": "1wUJX8Uz-LP6VGzB9vsypBQFuf_bufsWJ"
    }
    store = st.sidebar.selectbox("店舗を選択", list(store_files.keys()))
    file_id = store_files[store]
    url = f"https://drive.google.com/uc?id={file_id}"

    # CSVデータ読み込み（ローディング表示＆エラーハンドリング）
    with st.spinner("データ読み込み中..."):
        try:
            df = load_data(url)
        except Exception as e:
            st.error(f"CSVの読み込みまたは解析でエラーが発生しました: {e}")
            st.stop()

    # 必要な列が存在するか検証
    required_columns = [DATE_COL, MODEL_COL, MACHINE_COL]
    for col in required_columns:
        if col not in df.columns:
            st.error(f"必要な列 '{col}' がCSVに存在しません。")
            st.stop()

    # サイドバーでその他の選択項目
    model = st.sidebar.selectbox("機種を選択", sorted(df[MODEL_COL].unique()))
    filtered_df = df[df[MODEL_COL] == model]
    if filtered_df.empty:
        st.error("選択された機種のデータが存在しません。")
        st.stop()

    # ---------- セクション①：台番号×日付の表示形式 ----------
    with st.expander("① 台番号×日付の表示形式（ヒートマップ/スパークライン）", expanded=True):
        st.subheader("台番号×日付の表示形式（持玉/差玉）")
        visualization_type = st.radio("表示形式を選択", ["ヒートマップ", "スパークライン"])
        
        # 店舗により使用する列を切り替え
        heatmap_col = "最大持玉" if store == "メッセ武蔵境" else "最大差玉"
        if heatmap_col in filtered_df.columns:
            pivot_df = filtered_df.pivot(index=MACHINE_COL, columns=DATE_COL, values=heatmap_col)
            if visualization_type == "ヒートマップ":
                fig_heatmap = plot_heatmap(pivot_df, store, model, heatmap_col)
                st.pyplot(fig_heatmap)
                plt.close(fig_heatmap)
            else:
                fig_spark = plot_sparklines(filtered_df, heatmap_col)
                st.pyplot(fig_spark)
                plt.close(fig_spark)
        else:
            st.warning(f"この店舗では '{heatmap_col}' の列が見つかりませんでした。")
    
    # ---------- セクション②：特定の台の移動平均グラフ ----------
    with st.expander("② 特定の台の移動平均線付き推移グラフ", expanded=True):
        st.subheader("移動平均線を重ねた推移グラフ")
        machine = st.selectbox("台番号を選択", sorted(filtered_df[MACHINE_COL].unique()))
        target_df = filtered_df[filtered_df[MACHINE_COL] == machine].sort_values(DATE_COL)
        if target_df.empty:
            st.error("選択された台番号のデータが存在しません。")
        else:
            exclude_cols = [DATE_COL, MODEL_COL, MACHINE_COL, STORE_COL]
            col_options = [col for col in df.columns if col not in exclude_cols]
            if not col_options:
                st.error("表示項目の候補がありません。")
            else:
                col_ma = st.selectbox("表示項目を選択", col_options, key="ma_col")
                fig_ma = plot_moving_average(target_df, col_ma, store, model, machine)
                st.pyplot(fig_ma)
                plt.close(fig_ma)

if __name__ == "__main__":
    main()
