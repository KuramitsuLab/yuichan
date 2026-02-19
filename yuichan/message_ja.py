"""
message_ja.py  ─  YuiError のエラーメッセージを初心者向けの日本語に変換するモジュール
"""

from typing import Union


# ──────────────────────────────────────────────────────────────
# ヘルパー
# ──────────────────────────────────────────────────────────────

def _extract(messages: tuple, prefix: str) -> list:
    """メッセージタプルから特定のプレフィクスを持つ項目をすべて抜き出す"""
    return [m[len(prefix):] for m in messages if isinstance(m, str) and m.startswith(prefix)]


def _bad(messages: tuple) -> str:
    """❌ の値（問題のある実際の値）。なければ空文字"""
    items = _extract(messages, "❌")
    return items[0] if items else ""


def _bads(messages: tuple) -> list:
    """❌ の値をすべてリストで返す"""
    return _extract(messages, "❌")


def _good(messages: tuple) -> str:
    """✅ の値（期待していた正しい値）。なければ空文字"""
    items = _extract(messages, "✅")
    return items[0] if items else ""


def _info(messages: tuple) -> str:
    """🔍 の値（補足情報）。なければ空文字"""
    items = _extract(messages, "🔍")
    return items[0] if items else ""


def _hint(messages: tuple) -> str:
    """⚠️ の値（ヒント）。なければ空文字"""
    items = _extract(messages, "⚠️")
    return items[0] if items else ""


def _key(messages: tuple, index: int) -> str:
    """タプルの index 番目の要素を返す。なければ空文字"""
    if isinstance(messages, tuple) and len(messages) > index:
        return messages[index]
    return ""


_TYPE_JA = {
    "number":   "数値",
    "int":      "整数",
    "float":    "小数",
    "string":   "文字列",
    "array":    "配列",
    "object":   "オブジェクト（辞書）",
    "data":     "データ",
    "function": "関数",
    "not-int":  "整数以外",
}


def _type_ja(raw: str) -> str:
    """✅<number> のような文字列から日本語型名を返す。例: '<number>' → '数値'"""
    name = raw.strip("<>")
    return _TYPE_JA.get(name, name)


# ──────────────────────────────────────────────────────────────
# メイン変換関数
# ──────────────────────────────────────────────────────────────

def to_message(messages: Union[tuple, str]) -> str:
    """
    YuiError の messages を初心者向けの日本語メッセージに変換する。

    Parameters
    ----------
    messages : tuple | str
        YuiError.messages の値

    Returns
    -------
    str
        親しみやすい日本語のエラーメッセージ
    """
    if isinstance(messages, str):
        if messages == 'interruptted':
            return "実行が中断されたよ。"
        return messages

    if not isinstance(messages, tuple) or len(messages) == 0:
        return f"なんかエラーが起きちゃったよ… ({messages})"

    k0 = _key(messages, 0)
    k1 = _key(messages, 1)
    bad  = _bad(messages)
    good = _good(messages)
    info = _info(messages)
    hint = _hint(messages)

    # ────────────────────────────────────────────────
    # "error" カテゴリ（ランタイム）
    # ────────────────────────────────────────────────

    if k0 == "error":

        if k1 == "type":
            type_ja = _type_ja(good) if good else "別の型"
            if bad:
                return (
                    f"{type_ja}が必要なところに「{bad}」が来ているよ。\n"
                    f"ここには{type_ja}を使ってみてね！"
                )
            return f"ここには{type_ja}が必要だよ！"

        if k1 == "index":
            limit = good.lstrip("<") if good else ""  # "✅<5" → "5"
            if bad and limit:
                return (
                    f"配列の {bad} 番目にアクセスしようとしたけど、存在しないよ！\n"
                    f"このリストは {limit} 個の要素しかないよ（番号は 0 から始まるよ）。"
                )
            if bad:
                return (
                    f"配列の {bad} 番目にアクセスしようとしたけど、その番号は存在しないよ！\n"
                    "番号は 0 から始まるよ。配列の大きさを確認してみてね。"
                )
            return (
                "配列の範囲外にアクセスしようとしているよ！\n"
                "番号が大きすぎないか確認してみてね（番号は 0 から始まるよ）。"
            )

        if k1 == "incomparable":
            bads = _bads(messages)
            if len(bads) >= 2:
                return (
                    f"「{bads[0]}」と「{bads[1]}」は比べられないよ〜。\n"
                    "同じ種類のデータ（数字どうし・文字列どうし）じゃないと比べられないよ！"
                )
            return "比べられない値どうしを比較しようとしているよ。同じ種類のデータか確認してね！"

        if k1 == "recursion":
            if info:
                return (
                    f"関数「{info}」が自分自身を呼び出しすぎてしまったよ（再帰が深すぎる）！\n"
                    "再帰を止める条件（ベースケース）を書き忘れていないかな？"
                )
            return (
                "関数が自分自身を呼び出しすぎてしまったよ（再帰が深すぎる）！\n"
                "再帰を止める条件（ベースケース）を書き忘れていないかな？"
            )

        if k1 == "timeout":
            if bad:
                return (
                    f"実行が {bad} 秒を超えて時間切れになっちゃったよ〜⏰\n"
                    "無限ループになっていないか確認してみてね！\n"
                    "ループを抜ける条件が正しく書けているかな？"
                )
            return (
                "実行が時間切れになっちゃったよ〜⏰\n"
                "無限ループになっていないか確認してみてね！"
            )

        if k1 == "division by zero":
            if bad:
                return (
                    f"0 で割り算しようとしているよ！{bad} を使っているところを確認してね。\n"
                    "0 で割ることはできないよ。"
                )
            return "0 で割り算しようとしているよ！0 で割ることはできないよ。"

        if k1 == "conversion":
            if bad:
                return (
                    f"「{bad}」を数値に変換できなかったよ。\n"
                    "数字として読めない文字が含まれていないか確認してみてね！"
                )
            return "値を数値に変換できなかったよ。数字として読める文字列か確認してね！"

        if k1 == "internal":
            detail = info or hint
            if detail:
                return (
                    f"内部エラーが発生しちゃったよ（バグかも）。\n"
                    f"詳細: {detail}"
                )
            return "内部エラーが発生しちゃったよ（バグかも）。開発者に教えてあげてね！"

        # error + unknown
        return f"エラーが起きちゃったよ（{k1}）: " + " ".join(
            m for m in messages if isinstance(m, str)
        )

    # ────────────────────────────────────────────────
    # "undefined" カテゴリ
    # ────────────────────────────────────────────────

    if k0 == "undefined":

        if k1 == "variable":
            if bad:
                return (
                    f"変数「{bad}」はまだ定義されていないよ！\n"
                    f"使う前に「{bad} = ...」のように値を入れてあげてね。"
                )
            return "まだ定義されていない変数を使おうとしているよ。先に値を入れてね！"

        if k1 == "function":
            if bad:
                return (
                    f"関数「{bad}」が見つからないよ〜。\n"
                    "名前のスペルが違うか、定義する前に呼び出しているかも！"
                )
            return "呼び出した関数が見つからないよ。名前を確認してみてね！"

    # ────────────────────────────────────────────────
    # "expected" カテゴリ（パーサー・ランタイム）
    # ────────────────────────────────────────────────

    if k0 == "expected":

        if k1 == "token":
            if good and bad:
                return (
                    f"ここには「{good}」が必要なのに「{bad}」って書いてあったよ。\n"
                    "書き方を確認してみてね！"
                )
            if good:
                return f"ここには「{good}」が必要だよ！"
            return "必要な記号や文字が足りないよ。書き方を確認してみてね！"

        if k1 == "closing":
            if good:
                return (
                    f"開いたカッコや括弧を閉じ忘れているよ！「{good}」で閉じてね。\n"
                    "対応する括弧がちゃんとペアになっているか確認してみて！"
                )
            return "開いたカッコや括弧を閉じ忘れているよ！対応する括弧を確認してね。"

        if k1 == "variable":
            if bad:
                return (
                    f"「{bad}」に代入しようとしたけど、これは変数じゃないみたい。\n"
                    "代入できるのは変数名だけだよ！"
                )
            return "変数以外のものに代入しようとしているよ。代入先を確認してみてね！"

        if k1 == "arguments":
            if good and bad:
                return (
                    f"関数の引数の数が違うよ！\n"
                    f"必要な数は {good} 個なのに、{bad} 個渡しているよ。\n"
                    "引数の数を合わせてみてね！"
                )
            return "関数の引数の数が違うよ。引数の数を確認してみてね！"

        if k1 == "boolean":
            return (
                "true（はい）か false（いいえ）が必要なところだよ。\n"
                "条件式の書き方を確認してみてね！"
            )

        if k1 == "number":
            if bad:
                return (
                    f"数字が必要なところなのに「{bad}」って書いてあったよ。\n"
                    "数字を正しく書いてみてね！"
                )
            return "数字が必要なところだよ。数字を書いてみてね！"

        if k1 == "string":
            if bad:
                return (
                    f"文字列が必要なところなのに「{bad}」って書いてあったよ。\n"
                    '文字列はダブルクォート（""）で囲んでね！'
                )
            return '文字列が必要なところだよ。ダブルクォート（""）で囲んでね！'

        if k1 == "array":
            return (
                "配列が必要なところだよ。\n"
                "[1, 2, 3] のように [ ] で囲んで書いてみてね！"
            )

        if k1 == "object":
            return (
                "オブジェクト（辞書）が必要なところだよ。\n"
                '{"key": value} のように { } で囲んで書いてみてね！'
            )

        # 汎用ノンターミナル: ("expected", "funcdef", "❌...", "⚠️...")
        if bad:
            label = k1 if k1 else "構文"
            msg = f"「{label}」の書き方が間違っているみたい。「{bad}」って書いてあったよ。"
            if hint:
                msg += f"\nヒント: {hint}"
            return msg

        return f"ここに「{k1}」が必要だよ。書き方を確認してみてね！"

    # ────────────────────────────────────────────────
    # "required" カテゴリ
    # ────────────────────────────────────────────────

    if k0 == "required" and k1 == "arguments":
        if bad:
            return (
                f"この関数には引数が必要なのに、{bad} 個しか渡していないよ。\n"
                "引数を渡して呼び出してみてね！"
            )
        return "この関数には引数が必要だよ。引数を渡して呼び出してみてね！"

    # ────────────────────────────────────────────────
    # "wrong" カテゴリ（パーサー）
    # ────────────────────────────────────────────────

    if k0 == "wrong":

        if k1 == "statement":
            if bad:
                return (
                    f"「{bad}」はゆいの文として知らないよ〜。\n"
                    "スペルや書き方が間違っているかもしれないよ！"
                )
            return "この書き方はゆいの文として知らないよ〜。書き方を確認してみてね！"

        if k1 == "token":
            if bad and good:
                return (
                    f"ここは「{good}」のはずなのに「{bad}」って書いてあったよ。\n"
                    "書き方を確認してみてね！"
                )
            return "ここには違うものが書いてあるよ。書き方を確認してみてね！"

        if k1 == "name":
            if bad:
                return (
                    f"「{bad}」は変数名や関数名として使えないよ。\n"
                    "名前はアルファベット・ひらがな・漢字などで始めて、\n"
                    "数字や記号は使えないよ！"
                )
            return "変数名・関数名の書き方がおかしいよ。名前の付け方を確認してみてね！"

        if k1 == "indent":
            if good:
                return (
                    f"インデント（字下げ）がおかしいよ。\n"
                    f"ブロックの終わりは「{good}」のインデントに合わせてね！"
                )
            return (
                "インデント（字下げ）がおかしいよ。\n"
                "ブロックの中はそろえて字下げしてね！"
            )

    # ────────────────────────────────────────────────
    # "bad" カテゴリ（パーサー）
    # ────────────────────────────────────────────────

    if k0 == "bad":

        if k1 == "escape sequence":
            return (
                "バックスラッシュ（\\）の後に変な文字があるよ。\n"
                "使えるのは \\n（改行）・\\t（タブ）・\\\\（\\自身）などだよ！"
            )

    # ────────────────────────────────────────────────
    # "mismatch" カテゴリ
    # ────────────────────────────────────────────────

    if k0 == "mismatch" and k1 == "arguments":
        if good and bad:
            return (
                f"関数の引数の数が違うよ！\n"
                f"必要な数は {good} 個なのに、{bad} 個渡しているよ。\n"
                "引数の数を合わせてみてね！"
            )
        return "関数の引数の数が違うよ。引数の数を確認してみてね！"

    # ────────────────────────────────────────────────
    # "failed" カテゴリ（テスト失敗）
    # ────────────────────────────────────────────────

    if k0 == "failed" and k1 == "test":
        test_expr = info  # 🔍 に式が入っている
        if bad and good:
            expr_line = f"「{test_expr}」の結果を確認してみてね。\n" if test_expr else ""
            return (
                f"テスト失敗！{expr_line}"
                f"  期待した値: {good}\n"
                f"  実際の値:   {bad}"
            )
        return f"テストが失敗したよ！" + (f"「{test_expr}」の結果を確認してみてね。" if test_expr else "")

    # ────────────────────────────────────────────────
    # 文字列エラー（interruptted など）
    # ────────────────────────────────────────────────

    if k0 == "interruptted":
        return "実行が中断されたよ。"

    # ────────────────────────────────────────────────
    # フォールバック
    # ────────────────────────────────────────────────
    parts = [m for m in messages if isinstance(m, str)]
    return "エラーが起きちゃったよ: " + " ".join(parts)
