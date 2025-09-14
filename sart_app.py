import argparse
import json
import math
import os
import random
from datetime import datetime

from psychopy import core, event, visual


TARGET_DIGIT = "3"
NONTARGET_DIGITS = ["1", "2", "4", "5", "6", "7", "8", "9"]


def generate_trial_sequence(total_trials: int = 225, target_count: int = 25) -> list[dict]:

    nontarget_each = (total_trials - target_count) // len(NONTARGET_DIGITS)
    seq = [
        {"digit": TARGET_DIGIT, "is_target": True}
        for _ in range(target_count)
    ]
    for d in NONTARGET_DIGITS:
        seq.extend({"digit": d, "is_target": False} for _ in range(nontarget_each))

    random.seed()
    random.shuffle(seq)
    return seq


def generate_practice_sequence() -> list[dict]:

    practice_total = 18
    target_in_practice = 2
    base = [
        {"digit": TARGET_DIGIT, "is_target": True}
        for _ in range(target_in_practice)
    ]
    remaining = practice_total - target_in_practice
    nontarget_pool = []
    while len(nontarget_pool) < remaining:
        nontarget_pool.extend({"digit": d, "is_target": False} for d in NONTARGET_DIGITS)
    seq = base + nontarget_pool[:remaining]
    random.shuffle(seq)
    return seq


def draw_mask(win: visual.Window, color: str) -> visual.ShapeStim:

    mask_radius = 0.15
    circle = visual.Circle(win, radius=mask_radius, edges=128, fillColor=None, lineColor=color, lineWidth=4)
    line1 = visual.Line(win, start=(-mask_radius, -mask_radius), end=(mask_radius, mask_radius), lineColor=color, lineWidth=4)
    line2 = visual.Line(win, start=(-mask_radius, mask_radius), end=(mask_radius, -mask_radius), lineColor=color, lineWidth=4)
    return circle, line1, line2


def run_block(win: visual.Window, font_size_choices: list[int], sequence: list[dict], record_list: list[dict], allow_feedback_mask: bool) -> None:

    stim = visual.TextStim(win, text="", color="white", height=0.1, font="Arial Unicode MS")

    isi_clock = core.Clock()
    rt_clock = core.Clock()

    for trial_index, trial in enumerate(sequence):
        digit = trial["digit"]
        is_target = trial["is_target"]

        stim.height = _points_to_height(random.choice(font_size_choices))
        stim.text = digit

        event.clearEvents()
        rt_clock.reset()
        responded = False
        rt_ms = None
        correct = None
        
        # 数字表示開始
        stim.draw()
        win.flip()
        
        # 反応受付時間: 1150ms (数字250ms + マスク900ms)
        reaction_window = 1.150
        reaction_timer = core.Clock()
        
        while reaction_timer.getTime() < reaction_window:
            # ESCキーで終了チェック
            if event.getKeys(keyList=["escape"]):
                win.close()
                core.quit()
                return
            
            # 数字表示中（最初の250ms）
            if reaction_timer.getTime() < 0.250:
                # 数字表示中に反応があった場合
                keys = event.getKeys(keyList=["space"], timeStamped=rt_clock)
                if keys and not responded:
                    responded = True
                    rt_ms = int(keys[0][1] * 1000)
                    correct = (not is_target and responded) or (is_target and not responded)
                    
                    # 反応した瞬間に色付きマスクを表示
                    if allow_feedback_mask:
                        mask_color = "green" if correct else "red"
                        circle, line1, line2 = draw_mask(win, mask_color)
                        circle.draw(); line1.draw(); line2.draw()
                        win.flip()
            
            # マスク表示期間（250ms以降）
            else:
                if not responded:
                    # まだ反応していない場合、マスク表示中に反応をチェック
                    keys = event.getKeys(keyList=["space"], timeStamped=rt_clock)
                    if keys:
                        responded = True
                        rt_ms = int(keys[0][1] * 1000)
                        correct = (not is_target and responded) or (is_target and not responded)
                        
                        # 反応した瞬間に色付きマスクに変更
                        if allow_feedback_mask:
                            mask_color = "green" if correct else "red"
                            circle, line1, line2 = draw_mask(win, mask_color)
                            circle.draw(); line1.draw(); line2.draw()
                            win.flip()
                
                # マスク表示（白または色付き）
                if not responded or not allow_feedback_mask:
                    # まだ反応していない場合、またはフィードバックなしの場合
                    circle, line1, line2 = draw_mask(win, "white")
                    circle.draw(); line1.draw(); line2.draw()
                    win.flip()
        
        # 最終的な正解判定
        if correct is None:
            correct = (not is_target and responded) or (is_target and not responded)

        record_list.append({
            "trial_index": trial_index,
            "digit": digit,
            "is_target": is_target,
            "responded": responded,
            "rt_ms": rt_ms,
            "correct": correct,
        })


def _points_to_height(points: int) -> float:

    return max(0.06, min(0.18, (points / 100.0) * 0.18))


def show_message_and_wait_space(win: visual.Window, lines: list[str]) -> str:
    """
    メッセージを表示し、スペースキーを2回連続で押すまで待機する関数
    
    誤操作を防ぐため、スペースキーを3秒以内に2回連続で押す必要がある。
    ESCキーは1回押すだけで終了できる。
    
    Args:
        win: PsychoPyのウィンドウオブジェクト
        lines: 表示するメッセージの行リスト
        
    Returns:
        str: "space"（スペースキー2回連続）または"escape"（ESCキー）
    """
    text = "\n".join(lines)
    stim = visual.TextStim(win, text=text, color="white", height=0.05, wrapWidth=1.6, font="Arial Unicode MS", alignText="center")
    stim.draw()
    win.flip()
    
    # スペースキー2回連続押しの制御変数
    space_count = 0
    last_space_time = 0
    space_interval = 3  # 3秒以内に2回押す必要がある
    
    while True:
        keys = event.waitKeys(keyList=["space", "escape"])
        current_time = core.getTime()
        
        if keys[0] == "escape":
            # ESCキーは1回押すだけで終了
            win.close()
            core.quit()
            return "escape"
        elif keys[0] == "space":
            if current_time - last_space_time <= space_interval:
                # 2回目のスペースキーが時間内に押された → 開始
                return "space"
            else:
                # 1回目のスペースキー → タイマーをリセットして待機継続
                space_count = 1
                last_space_time = current_time


def show_countdown(win: visual.Window, is_practice: bool = False) -> None:
    """3秒間のカウントダウンを画面中央に表示"""
    
    for i in range(3, 0, -1):
        # ESCキーで終了チェック
        if event.getKeys(keyList=["escape"]):
            win.close()
            core.quit()
            return
        
        # カウントダウンを画面中央に表示
        if is_practice:
            countdown_text = f"練習開始まで {i} 秒"
        else:
            countdown_text = f"開始まで {i} 秒"
        countdown_stim = visual.TextStim(
            win, 
            text=countdown_text, 
            color="white", 
            height=0.12, 
            font="Arial Unicode MS", 
            alignText="center",
            pos=(0, 0)  # 画面中央に配置
        )
        
        countdown_stim.draw()
        win.flip()
        core.wait(1.0)  # 1秒間表示
    
    # "開始！"メッセージを0.5秒表示
    start_text = "開始！"
    start_stim = visual.TextStim(
        win, 
        text=start_text, 
        color="green", 
        height=0.15, 
        font="Arial Unicode MS", 
        alignText="center",
        pos=(0, 0)  # 画面中央に配置
    )
    
    start_stim.draw()
    win.flip()
    core.wait(0.5)


def analyze_and_save(records: list[dict], out_dir: str, tag: str) -> None:

    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_path = os.path.join(out_dir, f"raw_{tag}_{ts}.json")
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    commission = sum(1 for r in records if r["is_target"] and r["responded"])
    omission = sum(1 for r in records if (not r["is_target"]) and (not r["responded"]))
    rts = [r["rt_ms"] for r in records if (not r["is_target"]) and r["responded"] and r["rt_ms"] is not None]
    mean_rt = (sum(rts) / len(rts)) if rts else None
    sd_rt = (math.sqrt(sum((rt - mean_rt) ** 2 for rt in rts) / (len(rts) - 1)) if len(rts) > 1 else None) if mean_rt is not None else None

    def mean_last4(before_indices: list[int]) -> float | None:
        vals = [records[i]["rt_ms"] for i in before_indices if records[i]["rt_ms"] is not None]
        return (sum(vals) / len(vals)) if len(vals) > 0 else None

    correct_inhibit_indices = [i for i, r in enumerate(records) if r["is_target"] and not r["responded"]]
    commission_indices = [i for i, r in enumerate(records) if r["is_target"] and r["responded"]]

    def neighbors(i: int, offset: int, count: int) -> list[int]:
        if offset < 0:
            start = max(0, i + offset)
            end = i
        else:
            start = i + 1
            end = min(len(records), i + 1 + count)
        return list(range(start, end))

    correct_inhibit_last4_mean = [mean_last4(neighbors(i, -4, 4)) for i in correct_inhibit_indices]
    commission_last4_mean = [mean_last4(neighbors(i, -4, 4)) for i in commission_indices]
    commission_next4_mean = [mean_last4(neighbors(i, 1, 4)) for i in commission_indices]

    summary = {
        "commission_errors": commission,
        "omission_errors": omission,
        "mean_rt_ms_nontarget": mean_rt,
        "sd_rt_ms_nontarget": sd_rt,
        "correct_inhibit_prev4_mean_rts": correct_inhibit_last4_mean,
        "commission_prev4_mean_rts": commission_last4_mean,
        "commission_next4_mean_rts": commission_next4_mean,
    }

    summary_path = os.path.join(out_dir, f"summary_{tag}_{ts}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="SART課題アプリケーション")
    parser.add_argument("--no-practice", action="store_true", help="練習試行をスキップする")
    parser.add_argument("--trials", type=int, default=225, help="本番試行数（デフォルト: 225）")
    parser.add_argument("--targets", type=int, default=25, help="ターゲット数（デフォルト: 25）")
    
    args = parser.parse_args()
    
    win = visual.Window(fullscr=True, color="black", units="height")

    # 練習試行の有無に応じて説明文を調整
    if args.no_practice:
        start_text = [
            "SART 課題",
            "\n",
            "画面中央に 1〜9 の数字が素早く表示されます。",
            "数字の 3 以外: スペースキーでできるだけ速く反応してください。",
            "数字の 3 : キーを押さずに反応を抑制してください。",
            "\n",
            "数字は 250ms 表示され、その後 900ms のマスクが出ます。",
            "正解時は緑のマスク、不正解時は赤のマスクが表示されます。",
            "正確さと速さの両方を等しく重視してください。",
            "\n",
            "練習開始前に3秒間のカウントダウンが表示されます。",
            "\n",
            "スペースキーを2回連続で押して練習を開始してください。",
        ]
    else:
        start_text = [
            "SART 課題",
            "\n",
            "画面中央に 1〜9 の数字が素早く表示されます。",
            "数字の 3 以外: スペースキーでできるだけ速く反応してください。",
            "数字の 3 : キーを押さずに反応を抑制してください。",
            "\n",
            "数字は 250ms 表示され、その後 900ms のマスクが出ます。",
            "正解時は緑のマスク、不正解時は赤のマスクが表示されます。",
            "正確さと速さの両方を等しく重視してください。",
            "\n",
            "練習開始前に3秒間のカウントダウンが表示されます。",
            "\n",
            "スペースキーを2回連続で押して練習を開始してください。",
        ]
    show_message_and_wait_space(win, start_text)

    # 練習試行の実行（--no-practiceが指定されていない場合のみ）
    if not args.no_practice:
        # 練習試行前のカウントダウン
        show_countdown(win, is_practice=True)
        
        practice_records: list[dict] = []
        run_block(
            win,
            font_size_choices=[48, 72, 94, 100, 120],
            sequence=generate_practice_sequence(),
            record_list=practice_records,
            allow_feedback_mask=True,
        )

        key = show_message_and_wait_space(
            win,
            [
                "練習が終了しました。",
                "\n",
                f"本試行数: {args.trials}試行（ターゲット: {args.targets}個）",
                "\n",
                "本番試行開始前に3秒間のカウントダウンが表示されます。",
                "\n",
                "スペースキーを2回連続で押して本試行を開始してください。",
            ],
        )
        if key == "escape":
            win.close()
            core.quit()
            return
    else:
        # no-practiceの場合は練習終了後の画面から開始
        key = show_message_and_wait_space(
            win,
            [
                "練習が終了しました。",
                "\n",
                f"本試行数: {args.trials}試行（ターゲット: {args.targets}個）",
                "\n",
                "本番試行開始前に3秒間のカウントダウンが表示されます。",
                "\n",
                "スペースキーを2回連続で押して本試行を開始してください。",
            ],
        )
        if key == "escape":
            win.close()
            core.quit()
            return

    # 本番試行前のカウントダウン
    show_countdown(win)
    
    records: list[dict] = []
    run_block(
        win,
        font_size_choices=[48, 72, 94, 100, 120],
        sequence=generate_trial_sequence(args.trials, args.targets),
        record_list=records,
        allow_feedback_mask=True,
    )

    analyze_and_save(records, out_dir=os.path.join(os.getcwd(), "recoded_data"), tag="main")

    show_message_and_wait_space(win, ["終了しました。スペースキーで閉じます。"])
    win.close()
    core.quit()


if __name__ == "__main__":
    main()


