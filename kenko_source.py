#!/usr/bin/env python3
"""Clean the Wikisource text of Tsurezuregusa (校註日本文學大系, 1925).

The edition's glosses 〔…〕 are removed, its readings become {base|reading}
furigana markup, iteration marks are expanded and old kanji forms are
modernized. Historical kana spelling is kept.

Usage: python3 kenko_source.py sources/tsurezuregusa-wikisource.txt SECTION  (0 = preface)
"""
import json
import re
import sys
import unicodedata

SOURCE_URL = ('https://ja.wikisource.org/wiki/'
              '%E5%BE%92%E7%84%B6%E8%8D%89_(%E6%A0%A1%E8%A8%BB%E6%97%A5%E6%9C%AC%E6%96%87%E5%AD%B8%E5%A4%A7%E7%B3%BB)')

# Old (旧字体) → modern (新字体) forms, mostly from the 常用漢字表.
SHINJITAI = str.maketrans(
    '亞惡壓圍爲醫壹隱營榮衞驛圓鹽奧應歐毆櫻假價畫會囘壞懷繪擴殼覺學嶽樂勸卷寬歡觀關陷'
    '巖顏歸氣龜僞戲犧舊據擧虛峽挾狹鄕曉區驅勳薰徑惠揭溪經繼莖螢輕鷄藝擊缺儉劍圈檢權獻'
    '硏縣險顯驗嚴效廣恆黃鑛號國黑濟碎齋劑雜參慘棧蠶贊殘絲齒兒辭濕實寫釋壽收從澁獸縱肅'
    '處緖敍將燒稱涉證乘剩壤孃條淨狀疊讓釀觸囑眞寢愼盡圖粹醉穗隨髓樞數瀨聲靜齊攝竊專戰'
    '淺潛纖踐錢禪雙壯搜插爭總聰莊裝騷增藏臟卽屬續墮體對帶滯臺瀧擇澤單擔膽團彈斷癡遲晝'
    '蟲鑄廳聽敕鎭遞鐵轉點傳黨盜燈當鬪德獨讀屆繩貳惱腦霸廢拜賣麥發髮拔蠻祕濱甁拂佛竝變'
    '邊辨瓣辯舖步寶豐沒飜萬滿默譯藥與豫餘譽搖樣謠來賴亂覽兩獵綠壘勵禮靈齡戀爐勞樓郞錄'
    '灣彌淸靑渴晚飮遙棊讚劒鬭舍稻艷寳穩祿晉畧煑峯',
    '亜悪圧囲為医壱隠営栄衛駅円塩奥応欧殴桜仮価画会回壊懐絵拡殻覚学岳楽勧巻寛歓観関陥'
    '巌顔帰気亀偽戯犠旧拠挙虚峡挟狭郷暁区駆勲薫径恵掲渓経継茎蛍軽鶏芸撃欠倹剣圏検権献'
    '研県険顕験厳効広恒黄鉱号国黒済砕斎剤雑参惨桟蚕賛残糸歯児辞湿実写釈寿収従渋獣縦粛'
    '処緒叙将焼称渉証乗剰壌嬢条浄状畳譲醸触嘱真寝慎尽図粋酔穂随髄枢数瀬声静斉摂窃専戦'
    '浅潜繊践銭禅双壮捜挿争総聡荘装騒増蔵臓即属続堕体対帯滞台滝択沢単担胆団弾断痴遅昼'
    '虫鋳庁聴勅鎮逓鉄転点伝党盗灯当闘徳独読届縄弐悩脳覇廃拝売麦発髪抜蛮秘浜瓶払仏並変'
    '辺弁弁弁舗歩宝豊没翻万満黙訳薬与予余誉揺様謡来頼乱覧両猟緑塁励礼霊齢恋炉労楼郎録'
    '湾弥清青渇晩飲遥碁讃剣闘舎稲艶宝穏禄晋略煮峰',
)

ITERATION = {'〲': '〴〵', '〱': '〳〵'}
# Places where the general rules give the wrong result (checked against a second transcription).
OVERRIDES = {'かへす〴〵': 'かへすがへす', 'あさな〳〵': 'あさなあさな', 'はつれ〳〵': 'はつれはつれ', 'おどろ〳〵': 'おどろおどろ', 'ずゝ': 'ずず'}
TEMPLATE = re.compile(r'\{\{([^{}|]*)(?:\|([^{}|]*)\|([^{}|]*))?\}\}')


def remove_glosses(text):
    """Remove {{smaller|…}} glosses, including nested templates inside them."""
    out, i = [], 0
    while True:
        start = text.find('{{smaller|', i)
        if start < 0:
            return ''.join(out) + text[i:]
        out.append(text[i:start])
        depth, j = 0, start
        while j < len(text):
            if text.startswith('{{', j):
                depth, j = depth + 1, j + 2
            elif text.startswith('}}', j):
                depth, j = depth - 1, j + 2
                if depth == 0:
                    break
            else:
                j += 1
        if depth:
            raise ValueError('Unbalanced template near: %r' % text[start:start + 30])
        i = j


def _kana(ch):
    return 'ぁ' <= ch <= 'ヿ'


def _word(ch):
    return _kana(ch) or '一' <= ch <= '鿿' or ch == '々'


def _voiced(ch):
    v = unicodedata.normalize('NFC', ch + '゙')
    return v if len(v) == 1 else ch


def _unvoiced(ch):
    return unicodedata.normalize('NFC', unicodedata.normalize('NFD', ch).replace('゙', ''))


def _mark_error(text, i):
    return ValueError('Iteration mark after non-kana near: %r' % text[max(0, i - 5):i + 2])


def expand_iteration(text):
    """Expand ゝゞ (one kana) and 〳〵〴〵 (two characters); ゞ/〴〵 voice the first repeated kana."""
    for marked, expanded in OVERRIDES.items():
        text = text.replace(marked, expanded)
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if text.startswith(('〳〵', '〴〵'), i):
            unit = ''.join(out[-2:])
            if len(unit) < 2 or not all(_word(c) for c in unit):
                raise _mark_error(text, i)
            if ch == '〴':
                unit = _voiced(unit[0]) + unit[1]
            out.extend(unit)
            i += 2
            continue
        if ch in 'ゝゞ':
            if not out or not _kana(out[-1]):
                raise _mark_error(text, i)
            out.append(_voiced(out[-1]) if ch == 'ゞ' else _unvoiced(out[-1]))
        else:
            out.append(ch)
        i += 1
    return ''.join(out)


def to_shinjitai(text):
    return text.translate(SHINJITAI)


def _ruby(m):
    name, base, reading = m.groups()
    if name == 'r' and base and reading:
        return '{%s|%s}' % (base, reading.replace('－ママ', ''))
    raise ValueError('Unknown template: %r' % m[0])


def clean(raw, modern=True):
    text = remove_glosses(raw).replace(' ', '').replace('　', '')
    for name, marks in ITERATION.items():
        text = text.replace('{{%s}}' % name, marks)
    text = TEMPLATE.sub(_ruby, text)
    if '{{' in text or '}}' in text:
        raise ValueError('Unprocessed template in: %r' % text[:40])
    text = expand_iteration(text)
    return to_shinjitai(text) if modern else text


def sections(wikitext, modern=True):
    """Map section number → cleaned paragraphs. 0 is the preface, split off section 1.

    With modern=False the old kanji forms are kept, character for character in the same places.
    """
    body = wikitext[wikitext.index('\n}}') + 3:] if wikitext.startswith('{{') else wikitext
    parts = re.split(r'^(\d+)\s*$', body, flags=re.M)
    result = {}
    for num, chunk in zip(parts[1::2], parts[2::2]):
        paras = [p.strip() for p in chunk.strip().split('\n\n') if p.strip() and not p.strip().startswith(('{{PD', '{{DEFAULTSORT', '[[', '徒然草 終'))]
        result[int(num)] = [clean(p, modern) for p in paras]
    result[0], result[1] = result[1][:1], result[1][1:]
    return result


if __name__ == '__main__':
    raw = open(sys.argv[1], encoding='utf-8').read()
    print(json.dumps(sections(raw)[int(sys.argv[2])], ensure_ascii=False, indent=2))
