#!/usr/bin/env python3
# Copyright (c) 2026 Martial Systems LLC. MIT.
"""Script.rtf lines for the Maho Japanese voice bank.

English is the user's cue sheet. Japanese is what we train on (Okabe is
岡部さん; serious register; …… for ellipsis). Clip 57 is on disk (personality-disintegrate line).
"""

from __future__ import annotations

# id -> (en, ja). Non-speech marked in en with * *.
LINES: dict[str, tuple[str, str]] = {
    "1": ("Is it Kurisu's memories?", "紅莉栖の記憶、なの？"),
    "2": ("Hey, how did you guys meet Kagari?", "ねえ、かがりとはどうやって知り合ったの？"),
    "3": (
        "I wonder what she was up to before she came to Urushibara's house.",
        "漆原さんの家に来る前、何をしていたんだろう。",
    ),
    "4": (
        "But she had her memories of when she was a kid, right? You knew her, didn't you?",
        "でも子供の頃の記憶は残ってたんでしょ？　岡部さん、知ってたんじゃないの？",
    ),
    "5": ("Where was she when she was a kid?", "子供の頃は、どこにいたの？"),
    "6": ("W-What's all this about?", "な、なにこれ……？"),
    "7": ("...", "……"),
    "8": ("F-Fine. I won't tell anyone. I promise.", "わ、わかった。誰にも言わない。約束する。"),
    "9": ("...", "……"),
    "10": ("Don't make fun of me. I'm being serious here.", "馬鹿にしないで。本気なんだから。"),
    "11": (
        "In a time machine? There's no way you could make--",
        "タイムマシンで？　そんなの、作れるわけ――",
    ),
    "12": ("...", "……"),
    "13": ("That... can't...", "そんな……あり得ない……"),
    "14": ("...", "……"),
    "15": ("...Fine. I'll listen to what you have to say.", "……わかった。話は聞く。"),
    "16": (
        "What you're telling me is that Suzuha and Kagari came here from the year 2036 to have Okabe change the future, right?",
        "つまり鈴羽とかがりは、2036年から来て、岡部さんに未来を変えさせる、ってことよね？",
    ),
    "17": ("*sigh*", "はあ……"),
    "18": (
        "I can't imagine Okabe being capable of pulling something like that off.",
        "岡部さんに、そんなことできるとは思えない。",
    ),
    "19": (
        "I can't believe the fate of all humanity rests on a single person...",
        "人類の命運が、一人にかかってるなんて……信じられない。",
    ),
    "20": ("It's not really believable... but...", "にわかには信じられない……でも……"),
    "21": (
        "But the theory you described might allow for a time leap, yes.",
        "でも、今の理論なら、タイムリープは可能かもしれない。ええ。",
    ),
    "22": (
        "And more than anything, it was Kurisu who came up with that theory, right?",
        "それに何より、その理論を出したのは紅莉栖なんでしょ？",
    ),
    "23": ("Then it's worth looking into.", "なら、調べる価値はある。"),
    "24": ("Because... she was a genius.", "だって……彼女は天才だったから。"),
    "25": (
        "In exchange, I want you to let me see that time machine.",
        "その代わり、そのタイムマシンを見せて。",
    ),
    "26": (
        "If you came here in it, it still has to be around, right?",
        "乗ってきたなら、まだあるんでしょ？",
    ),
    "27": (
        "I'll need to look into this, but I've decided to believe you for now. So I want you to help me believe.",
        "調べる必要はあるけど、とりあえず信じると決めた。だから、信じられるように協力して。",
    ),
    "28": ("...Thank you.", "……ありがとう。"),
    "29": ("...", "……"),
    "30": (
        "I just checked with Dr. Leskinen a while ago. Kurisu's memory data has been sealed away, and no one can access it yet, he said.",
        "さっきレスキネン教授に確認した。紅莉栖の記憶データは封印されてて、まだ誰もアクセスできない、だって。",
    ),
    "31": (
        "But I don't have the authority to check that for myself.",
        "でも、私には自分で確かめる権限がない。",
    ),
    "32": (
        "And it's possible someone else took the data before the project was shut down.",
        "プロジェクトが止まる前に、誰かがデータを持ち出した可能性もある。",
    ),
    "33": (
        "Not necessarily. Anybody could do it if they hacked the server.",
        "必ずしもそうじゃない。サーバーをハックできれば、誰にでもできる。",
    ),
    "34": (
        "The question is why. If your theory's right, why would they want to do that?",
        "問題は動機。その理論が正しいなら、なぜそんなことを？",
    ),
    "35": (
        "But Kurisu arrived at that theory in the other world line you were telling me about, right?",
        "でも紅莉栖がその理論に辿り着いたのは、岡部さんの言ってた別の世界線、よね？",
    ),
    "36": (
        "Nakabachi? The guy who sought asylum in Russia?",
        "中鉢？　ロシアに亡命した、あの人？",
    ),
    "37": (
        "I took a look at it, and calling it a 'paper' is being way too kind.",
        "読んでみたけど、論文なんて呼ぶのはお世辞にも良いすぎ。",
    ),
    "38": ("What are you talking about?", "何の話？"),
    "39": ("*scared exclamation*", "ひっ……！"),
    "40": ("Come to think of it...", "そういえば……"),
    "41": (
        "I remember her saying that before she left Japan she was going to see her dad. He was announcing a new theory, and she'd been given an invitation.",
        "日本を発つ前、お父さんに会いに行くって言ってた。新しい理論の発表で、招待状をもらってたの。",
    ),
    "42": (
        "Then you mean someone found out about this paper, and is trying to get the theory needed to make a working time machine out of Kurisu's brain?",
        "つまり誰かがこの論文を知って、動くタイムマシンに必要な理論を、紅莉栖の脳から取り出そうとしてる、ってこと？",
    ),
    "43": ("Moving memory data into a brain, huh?", "記憶データを脳に移す、か。"),
    "44": ("Yeah, that's right. It's possible.", "ええ、そう。可能よ。"),
    "45": (
        "And that's what Amadeus was origially created to do.",
        "そもそもアマデウスは、そのために作られたの。",
    ),
    "46": (
        "Kurisu's time leap machine is another application of this.",
        "紅莉栖のタイムリープマシンも、その応用よ。",
    ),
    "47": (
        "I don't think it would be as simple as copying them to a hard drive on a PC with a different OS.",
        "OSの違うPCのハードディスクにコピーするみたいには、いかないと思う。",
    ),
    "48": (
        "We don't even know how much capacity the human brain has.",
        "人間の脳の容量すら、まだ正確にはわかってない。",
    ),
    "49": (
        "In terms of strict storage capacity, it should easily have enough room to store the memories of two 20 year old girls.",
        "純粋な記憶容量だけなら、二十歳の少女二人分の記憶は余裕で入るはず。",
    ),
    "50": ("But the problem goes way beyond that.", "でも問題は、そんな単純な話じゃない。"),
    "51": (
        "Like you said, we're still not even at the point of successfully downloading memories back into the original brain.",
        "岡部さんの言う通り、元の脳に記憶を書き戻すことすら、まだ成功してない。",
    ),
    "52": (
        "If you tried to copy those memories into someone else's brain, it could cause serious inconsistency problems.",
        "他人の脳にコピーしたら、重大な不整合が起きる。",
    ),
    "53": (
        "In fact, we're starting to see those errors happen right now.",
        "現に、そのエラーが今、出始めてる。",
    ),
    "54": (
        "Memories and personality are different things. Memories are controlled by the hippocampus and cerebral cortex. Personality is constructed  by the prefrontal cortex.",
        "記憶と人格は別物よ。記憶は海馬と大脳皮質。人格は前頭前野が構築する。",
    ),
    "55": (
        "The functions of the two are intricately connected.",
        "二つの機能は、複雑に結びついてる。",
    ),
    "56": (
        "The mix of the two sets of memories is probably putting a lot of stress on her brain.",
        "二つの記憶が混ざって、脳に相当な負荷がかかってるはず。",
    ),
    "57": (
        "If we don't do something, it could cause her entire personality to disintegrate.",
        "何もしなければ、人格そのものが崩壊する。",
    ),
    "58": (
        "The only way is to remove Kurisu's memories from Kagari's mind.",
        "方法は一つ。かがりから紅莉栖の記憶を取り除くこと。",
    ),
    "59": (
        "If I can analyze the data in her brain, yes, but how many years away that is, I don't know...",
        "脳のデータを解析できれば、ええ。何年先になるかは、わからない……",
    ),
    "60": ("If there was a way...", "もし方法があるなら……"),
    "61": (
        "It would be to overwrite her past memories again.",
        "過去の記憶を、もう一度上書きすること。",
    ),
    "62": (
        "I don't think whoever altered her memories intended to leave her original ones.",
        "記憶を改竄した側が、元の記憶を残すつもりだったとは思えない。",
    ),
    "63": (
        "So if we were able to overwrite her memories once more, with proper equipment, it might fix her.",
        "だから適切な装置でもう一度上書きできれば、治せるかもしれない。",
    ),
    "64": ("We'll just have to hope they made backups.", "バックアップがあることを祈るしかない。"),
    "65": ("If it doesn't exist, we can make it.", "なければ、作ればいい。"),
    "66": ("But Kurisu made it, right?", "でも作ったのは紅莉栖でしょ？"),
    "67": (
        "The question is where to find her memory data, thought. We'll just have to find it somehow.",
        "問題は、記憶データがどこにあるか。どうにかして見つけるしかない。",
    ),
    "Excited1": ("*excitement/wail*", "きゃあっ！"),
    "Excited2": (
        "This circuit board pattern is so pretty, it's like a work of art!",
        "この回路パターン、きれい……芸術作品みたい！",
    ),
    "Excited3": (
        "Is that an IFX008 image sensor?! What's it doing here?!",
        "IFX008のイメージセンサ！？　なんでここにあるの！？",
    ),
    "Excited4": (
        "Who knew Akihabara had places like this?!",
        "秋葉原に、こんな場所があるなんて！",
    ),
}

NONSPEECH = frozenset({"7", "9", "12", "14", "17", "29", "39", "Excited1"})
MISSING = frozenset()
