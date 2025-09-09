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

    stim = visual.TextStim(win, text="", color="white", height=0.1, font="Symbol")

    isi_clock = core.Clock()
    rt_clock = core.Clock()

    for trial_index, trial in enumerate(sequence):
        digit = trial["digit"]
        is_target = trial["is_target"]

        stim.height = _points_to_height(random.choice(font_size_choices))
        stim.text = digit

        event.clearEvents()
        rt_clock.reset()

        stim.draw()
        win.flip()
        core.wait(0.250)

        keys = event.getKeys(keyList=["space"], timeStamped=rt_clock)
        responded = len(keys) > 0
        rt_ms = None
        if responded:
            rt_ms = int(keys[0][1] * 1000)

        correct = (not is_target and responded) or (is_target and not responded)
        mask_color = "green" if correct else "red"

        circle, line1, line2 = draw_mask(win, mask_color if allow_feedback_mask else "white")
        circle.draw(); line1.draw(); line2.draw()
        win.flip()
        core.wait(0.900)

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

    text = "\n".join(lines)
    stim = visual.TextStim(win, text=text, color="white", height=0.05, wrapWidth=1.6, font="Symbol", alignText="center")
    stim.draw()
    win.flip()
    return event.waitKeys(keyList=["space", "escape"])[0]


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

    win = visual.Window(fullscr=True, color="black", units="height")

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
        "スペースキーで練習を開始します。",
    ]
    show_message_and_wait_space(win, start_text)

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
            "スペースキーで本試行を開始します。",
            "ESCで終了します。",
        ],
    )
    if key == "escape":
        win.close()
        core.quit()
        return

    records: list[dict] = []
    run_block(
        win,
        font_size_choices=[48, 72, 94, 100, 120],
        sequence=generate_trial_sequence(225, 25),
        record_list=records,
        allow_feedback_mask=True,
    )

    analyze_and_save(records, out_dir=os.path.join(os.getcwd(), "recoded_data"), tag="main")

    show_message_and_wait_space(win, ["終了しました。スペースキーで閉じます。"])
    win.close()
    core.quit()


if __name__ == "__main__":
    main()


