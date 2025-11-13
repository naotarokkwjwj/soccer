#=============================
# ⚽ 各チーム × シュートで終わる全攻撃IDのアニメーション生成
#==============================================
#google colab でこのコードを書く＋各試合のplaycsv,とtracking.csvのファイルを入れる
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import numpy as np
import os

# === 1. ファイル読み込み ===
play_path = 'play.csv'#play.csv を入れる
tracking_path = 'tracking.csv'#tracking.csvを入れる

df_play = pd.read_csv(play_path)
df_tracking = pd.read_csv(tracking_path)
print("✅ ファイル読み込み完了")

# === 2. ピッチ描画関数 ===
def draw_pitch(ax=None):
    pitch_length = 105
    pitch_width = 68
    pa_len, pa_wid = 16.5, 40.32
    ga_len, ga_wid = 5.5, 18.32
    goal_width = 7.32
    if ax is None:
        fig, ax = plt.subplots(figsize=(7, 10))

    ax.add_patch(patches.Rectangle((-pitch_width/2, 0), pitch_width, pitch_length, fill=False, lw=2, color='black'))
    ax.axhspan(52.5, 105, facecolor='lightcoral', alpha=0.15)
    ax.plot([-pitch_width/2, pitch_width/2], [52.5, 52.5], color='black', lw=1.5, ls='--')
    ax.add_patch(plt.Circle((0, 52.5), 9.15, fill=False, color='black', lw=1.5))
    ax.add_patch(patches.Rectangle((-pa_wid/2, 0), pa_wid, pa_len, fill=False, color='black'))
    ax.add_patch(patches.Rectangle((-pa_wid/2, pitch_length - pa_len), pa_wid, pa_len, fill=False, color='black'))
    ax.add_patch(patches.Rectangle((-ga_wid/2, 0), ga_wid, ga_len, fill=False, color='black'))
    ax.add_patch(patches.Rectangle((-ga_wid/2, pitch_length - ga_len), ga_wid, ga_len, fill=False, color='black'))
    ax.add_patch(patches.Rectangle((-goal_width/2, -2.44), goal_width, 2.44, fill=True, color='gray'))
    ax.add_patch(patches.Rectangle((-goal_width/2, pitch_length), goal_width, 2.44, fill=True, color='gray'))

    ax.set_xlim(-pitch_width/2 - 3, pitch_width/2 + 3)
    ax.set_ylim(-3, pitch_length + 3)
    ax.set_aspect('equal')
    return ax

# === 3. tracking 座標変換（左右反転） ===
scale = 100.0
df_tracking["X_m"] = df_tracking["X"] / scale + 52.5
df_tracking["Y_m"] = -df_tracking["Y"] / scale

# === 4. 各チーム取り出し ===
teams = df_play["チームID"].dropna().unique()

for team_id in teams:
    team_folder = f"/content/animations_team_{int(team_id)}"
    os.makedirs(team_folder, exist_ok=True)
    
    # シュートした攻撃だけ抽出
    shoot_attacks = df_play[(df_play["チームID"] == team_id) & (df_play["F_シュート"] == 1)]["攻撃履歴No"].unique()

    if len(shoot_attacks) == 0:
        print(f"⚠️ チームID {team_id} はシュートで終わる攻撃なし")
        continue

    print(f"\n==========================")
    print(f"🎽 チームID {team_id} の攻撃数: {len(shoot_attacks)}")
    print("==========================")

    # === 攻撃IDごとに動画を作成 ===
    for attack_id in shoot_attacks:

        print(f"▶ 攻撃ID {attack_id} 動画作成中…")

        attack_df = df_play[df_play["攻撃履歴No"] == attack_id]

        start_frame = int(attack_df["フレーム番号"].min())
        end_frame = int(attack_df["フレーム番号"].max())

        df_seg = df_tracking[(df_tracking["Frame"] >= start_frame) & (df_tracking["Frame"] <= end_frame)]
        frames_list = sorted(df_seg["Frame"].unique())

        # 描画設定
        fig, ax = plt.subplots(figsize=(7, 10))
        draw_pitch(ax)

        home_scatter = ax.scatter([], [], color='blue', s=70, label='Home')
        away_scatter = ax.scatter([], [], color='red', s=70, label='Away')
        action_star, = ax.plot([], [], marker='*', color='gold', markersize=15, markeredgecolor='black')

        text_objs = []

        def init():
            home_scatter.set_offsets(np.empty((0, 2)))
            away_scatter.set_offsets(np.empty((0, 2)))
            action_star.set_data([], [])
            return [home_scatter, away_scatter, action_star]

        def update(frame):
            frame_data = df_seg[df_seg["Frame"] == frame]
            home = frame_data[frame_data["HA"] == 1]
            away = frame_data[frame_data["HA"] == 2]

            home_scatter.set_offsets(home[["Y_m", "X_m"]].values)
            away_scatter.set_offsets(away[["Y_m", "X_m"]].values)

            # アクション発生
            act_now = attack_df[attack_df["フレーム番号"] == frame]
            if not act_now.empty:
                x_star = act_now.iloc[0]["位置座標X"]
                y_star = -act_now.iloc[0]["位置座標Y"]
                action_star.set_data([y_star], [x_star])
            else:
                action_star.set_data([], [])

            # テキスト削除→再描画
            for t in text_objs:
                t.remove()
            text_objs.clear()

            for _, row in frame_data.iterrows():
                txt = ax.text(row["Y_m"] + 0.3, row["X_m"], str(row["SysTarget"]), fontsize=6)
                text_objs.append(txt)

            ax.set_title(f"Team {team_id} / 攻撃ID {attack_id} / Frame {frame}")
            return [home_scatter, away_scatter, action_star] + text_objs

        ani = animation.FuncAnimation(fig, update, frames=frames_list, init_func=init, blit=False, interval=60)

        save_path = f"{team_folder}/attack_{attack_id}.mp4"
        ani.save(save_path, fps=10, dpi=120)
        plt.close(fig)

        print(f"   ✔ 保存 → {save_path}")

print("\n🎉 全チーム全攻撃IDの動画生成が完了しました！")
